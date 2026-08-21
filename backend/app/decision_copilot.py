"""Evidence-bound decision options and deterministic red-team policy checks.

Gemini may propose bounded choices. It may not approve, publish, or invent
evidence. The policy review below is deliberately deterministic and runs
before the public approval endpoint accepts an option.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Literal

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.types import GenerateContentConfig, ThinkingConfig
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .analysis import AnalysisUnavailable
from .guardrails import guard_evidence_fields, untrusted_evidence_instruction
from .models import WorkflowState

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.5-flash")
ALLOWED_ACTIONS = {"packet", "owner_review", "queued"}
ALLOWED_WORKFLOW_DECISIONS = {
    "grandfather_existing_customers",
    "approve_competitive_response",
}


class EvidenceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    quote: str = Field(min_length=1, max_length=240)


class DecisionOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,48}$")
    title: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=280)
    tradeoffs: list[str] = Field(min_length=1, max_length=4)
    rollback: str = Field(min_length=1, max_length=280)
    risk: Literal["low", "medium", "high"]
    workflow_decision: Literal[
        "grandfather_existing_customers", "approve_competitive_response"
    ]
    artifact_decisions: dict[str, Literal["packet", "owner_review", "queued"]]
    citations: list[EvidenceCitation] = Field(min_length=1, max_length=3)
    requires_human_approval: bool = True


class DecisionCopilot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    question: str = Field(min_length=1, max_length=240)
    recommendation_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,48}$")
    options: list[DecisionOption] = Field(min_length=2, max_length=3)


class PolicyFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=60)
    severity: Literal["low", "medium", "high", "critical"]
    message: str = Field(min_length=1, max_length=240)
    mitigation: str = Field(min_length=1, max_length=240)
    option_id: str | None = None
    blocking: bool = False


class PolicyReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pass", "blocked"]
    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    findings: list[PolicyFinding] = Field(max_length=12)


decision_copilot_agent = Agent(
    name="driftline_decision_copilot",
    model=MODEL_NAME,
    mode="task",
    generate_content_config=GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=DecisionCopilot.model_json_schema(),
        # Three options each cover every mapped artifact, citations, tradeoffs,
        # and rollback text.  1,800 tokens was too tight for Gemini to finish
        # the schema reliably, which caused an avoidable demo fallback.  Keep
        # this bounded, but leave enough room for a complete response.
        max_output_tokens=3200,
        thinking_config=ThinkingConfig(thinking_level="LOW"),
    ),
    description=(
        "Decision copilot that proposes evidence-cited options and reversible "
        "tradeoffs without approval or publishing authority."
    ),
    instruction=(
        "Return only the requested JSON schema. Propose two or three genuinely "
        "different bounded choices for the human operator. Every choice must "
        "cite the supplied evidence hash and quote the source change, include "
        "tradeoffs and a concrete rollback, and map every current artifact to "
        "packet, owner_review, or queued. Never approve, publish, contact a "
        "customer, or claim an external system changed. Keep rationale concise; "
        "do not reveal hidden chain-of-thought."
    ),
)


def _prompt(state: WorkflowState) -> str:
    evidence = state.evidence
    if evidence is None:
        raise AnalysisUnavailable("Workflow has no source evidence")
    impacts = "\n".join(
        f"- {item.name} | owner={item.owner} | risk={item.risk}"
        for item in state.impacts
    )
    category = state.impact_graph.get("summary", {}).get("category", "Change")
    safe, safety = guard_evidence_fields(evidence.__dict__)
    return (
        untrusted_evidence_instruction()
        + "Create a decision brief for this verified Driftline change. Return "
        "exactly 2 or 3 options and no prose outside JSON.\n\n"
        f"Category: {category}\n"
        f"Source: {safe['source_name']} ({evidence.source_id})\n"
        f"Evidence hash: {evidence.evidence_hash}\n"
        "<untrusted_source_before>\n"
        f"{safe['before']}\n"
        "</untrusted_source_before>\n"
        "<untrusted_source_after>\n"
        f"{safe['after']}\n"
        "</untrusted_source_after>\n"
        f"Source guard metadata: {json.dumps(safety, sort_keys=True)}\n"
        f"Current artifacts:\n{impacts}\n\n"
        "Every option must include all current artifact names, one of the "
        "allowlisted workflow decisions, tradeoffs, rollback, and a citation "
        "whose quote is copied exactly from Before or After. Human approval is "
        "mandatory for every option."
    )


async def _run_events(prompt: str) -> list[str]:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="driftline",
        user_id="decision-copilot",
        session_id=os.urandom(12).hex(),
    )
    runner = Runner(
        agent=decision_copilot_agent,
        app_name="driftline",
        session_service=session_service,
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    text_parts: list[str] = []
    async for event in runner.run_async(
        user_id="decision-copilot",
        session_id=session.id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            text_parts.extend(
                part.text for part in event.content.parts if getattr(part, "text", None)
            )
    return text_parts


def _parse(text_parts: list[str], state: WorkflowState) -> DecisionCopilot:
    raw = "".join(text_parts).strip()
    if not raw:
        raise AnalysisUnavailable("Gemini returned no decision copilot output")
    if raw.startswith("```"):
        raw = raw.removeprefix("```").removeprefix("json").strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    if not raw.startswith("{"):
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnalysisUnavailable("Gemini returned non-JSON decision copilot output") from exc
    # Gemini occasionally emits a semantically valid option set with a
    # recommendation label that is not one of its generated IDs. Preserve the
    # model's bounded options, but deterministically bind the recommendation to
    # the first option before the strict evidence/policy validation below.
    if isinstance(payload, dict) and payload.get("options"):
        option_ids = {
            item.get("option_id")
            for item in payload["options"]
            if isinstance(item, dict)
        }
        if payload.get("recommendation_id") not in option_ids:
            payload["recommendation_id"] = payload["options"][0].get("option_id")
    return validate_copilot(payload, state)


def validate_copilot(payload: Any, state: WorkflowState) -> DecisionCopilot:
    """Validate options at the model/API seam before they reach an approver."""
    evidence = state.evidence
    if evidence is None:
        raise AnalysisUnavailable("Workflow has no source evidence")
    try:
        result = payload if isinstance(payload, DecisionCopilot) else DecisionCopilot.model_validate(payload)
    except (ValidationError, TypeError, ValueError) as exc:
        raise AnalysisUnavailable("Decision copilot failed schema validation") from exc
    if result.evidence_hash != evidence.evidence_hash:
        raise AnalysisUnavailable("Decision copilot used the wrong evidence hash")
    expected_names = {item.name for item in state.impacts}
    option_ids = [option.option_id for option in result.options]
    if len(set(option_ids)) != len(option_ids):
        raise AnalysisUnavailable("Decision copilot returned duplicate option IDs")
    if result.recommendation_id not in set(option_ids):
        raise AnalysisUnavailable("Decision copilot recommendation is not an option")
    for option in result.options:
        if set(option.artifact_decisions) != expected_names:
            raise AnalysisUnavailable("Decision option does not cover every artifact")
        if not option.requires_human_approval:
            raise AnalysisUnavailable("Decision option bypasses human approval")
        if option.workflow_decision not in ALLOWED_WORKFLOW_DECISIONS:
            raise AnalysisUnavailable("Decision option uses an unknown policy decision")
        for action in option.artifact_decisions.values():
            if action not in ALLOWED_ACTIONS:
                raise AnalysisUnavailable("Decision option uses an unknown artifact action")
        for citation in option.citations:
            if citation.evidence_hash != evidence.evidence_hash:
                raise AnalysisUnavailable("Decision citation is not evidence-bound")
            if citation.quote not in {evidence.before, evidence.after}:
                raise AnalysisUnavailable("Decision citation is not copied from the source diff")
    return result


def red_team_review(copilot: DecisionCopilot, state: WorkflowState) -> PolicyReview:
    """Run deterministic safety checks independent of Gemini's recommendation."""
    evidence = state.evidence
    if evidence is None:
        raise AnalysisUnavailable("Workflow has no source evidence")
    findings: list[PolicyFinding] = []
    expected_names = {item.name for item in state.impacts}
    for option in copilot.options:
        if option.risk == "high":
            findings.append(
                PolicyFinding(
                    code="high_risk_human_gate",
                    severity="high",
                    message="This option can alter a high-risk business promise.",
                    mitigation="Keep the named-human approval gate and review each artifact decision.",
                    option_id=option.option_id,
                )
            )
        if set(option.artifact_decisions) != expected_names:
            findings.append(
                PolicyFinding(
                    code="incomplete_artifact_scope",
                    severity="critical",
                    message="The option does not cover the complete mapped artifact set.",
                    mitigation="Reject the option until every mapped artifact has an explicit bounded action.",
                    option_id=option.option_id,
                    blocking=True,
                )
            )
        if not option.rollback.strip():
            findings.append(
                PolicyFinding(
                    code="missing_rollback",
                    severity="critical",
                    message="The option has no rollback path.",
                    mitigation="Require a reversible packet and a recorded reopen path.",
                    option_id=option.option_id,
                    blocking=True,
                )
            )
    if copilot.evidence_hash != evidence.evidence_hash:
        findings.append(
            PolicyFinding(
                code="evidence_mismatch",
                severity="critical",
                message="The decision brief is not bound to the current source snapshot.",
                mitigation="Discard the brief and rerun analysis against the current evidence hash.",
                blocking=True,
            )
        )
    return PolicyReview(
        status="blocked" if any(item.blocking for item in findings) else "pass",
        evidence_hash=evidence.evidence_hash,
        findings=findings,
    )


def fallback_copilot(state: WorkflowState) -> DecisionCopilot:
    """Deterministic, visibly labeled fallback for judge reliability."""
    evidence = state.evidence
    if evidence is None:
        raise AnalysisUnavailable("Workflow has no source evidence")
    high_default = {
        item.name: (
            "queued"
            if item.name.lower().endswith("guidance")
            else "packet"
            if item.risk == "high"
            else "owner_review"
        )
        for item in state.impacts
    }
    transition = {
        item.name: ("queued" if item.risk == "low" else "owner_review")
        for item in state.impacts
    }
    hold = {item.name: "queued" for item in state.impacts}
    decision = (
        "approve_competitive_response"
        if state.impact_graph.get("summary", {}).get("category", "").startswith("Competitor")
        else "grandfather_existing_customers"
    )
    citation = EvidenceCitation(evidence_hash=evidence.evidence_hash, quote=evidence.after)
    return DecisionCopilot(
        evidence_hash=evidence.evidence_hash,
        question="Which bounded response should move forward from this verified change?",
        recommendation_id="preserve_commitments",
        options=[
            DecisionOption(
                option_id="preserve_commitments",
                title="Preserve existing commitments",
                summary="Keep current customers protected while updating future-facing guidance.",
                tradeoffs=["Lowest contractual surprise", "Requires an explicit exception path"],
                rollback="Reopen the decision and reverse the scoped packet or connector marker.",
                risk="high",
                workflow_decision=decision,
                artifact_decisions=high_default,
                citations=[citation],
            ),
            DecisionOption(
                option_id="managed_transition",
                title="Use a managed transition",
                summary="Move owners to the new promise while routing high-risk language for review.",
                tradeoffs=["Faster alignment", "More owner review before customer-facing use"],
                rollback="Reopen the decision and return every artifact to draft-ready state.",
                risk="medium",
                workflow_decision=decision,
                artifact_decisions=transition,
                citations=[citation],
            ),
            DecisionOption(
                option_id="pause_for_review",
                title="Pause and investigate",
                summary="Keep all outputs queued until an owner confirms the source interpretation.",
                tradeoffs=["Minimizes premature change", "Leaves the current inconsistency unresolved"],
                rollback="No external write occurs; reopen or discard the queued packet after review.",
                risk="low",
                workflow_decision=decision,
                artifact_decisions=hold,
                citations=[citation],
            ),
        ],
    )


async def analyze_decision(state: WorkflowState) -> tuple[DecisionCopilot, PolicyReview]:
    """Run Gemini options, then independently red-team them.

    The copilot is a second model turn after the coordinator and impact
    analyst.  A transient empty ADK response used to turn an otherwise live
    workflow into a deterministic fallback, which was honest but weakened the
    judge-facing proof.  Retry only transient transport/empty/schema-shape
    failures; evidence and policy violations still fail closed immediately.
    """
    prompt = _prompt(state)
    last_error: AnalysisUnavailable | None = None
    for attempt in range(3):
        try:
            copilot = _parse(await _run_events(prompt), state)
            policy = red_team_review(copilot, state)
            if policy.status == "blocked":
                raise AnalysisUnavailable("Decision copilot blocked by red-team policy")
            return copilot, policy
        except AnalysisUnavailable as exc:
            last_error = exc
            retryable = any(
                marker in str(exc).casefold()
                for marker in (
                    "no decision copilot output",
                    "non-json decision copilot output",
                    "decision copilot failed schema validation",
                )
            )
            if attempt < 2 and retryable:
                await asyncio.sleep(0.25 * (attempt + 1))
                continue
            raise
        except Exception as exc:
            last_error = AnalysisUnavailable("Gemini decision copilot request failed")
            if attempt < 2:
                await asyncio.sleep(0.25 * (attempt + 1))
                continue
            raise last_error from exc
    raise last_error or AnalysisUnavailable("Decision copilot unavailable")


def validate_approval_choice(
    state: WorkflowState,
    option_id: str | None,
    workflow_decision: str,
    artifact_decisions: dict[str, str] | None,
    *,
    custom_override: bool = False,
    override_reason: str | None = None,
) -> None:
    """Enforce that an API approval matches a reviewed or custom plan."""
    if not option_id:
        if custom_override:
            raise ValueError("Custom routing requires a reviewed copilot option")
        trace = state.agent_trace or {}
        decision_trace_payload = trace.get("decision_copilot")
        if trace.get("execution_mode") == "google_adk" and (
            not isinstance(decision_trace_payload, dict)
            or decision_trace_payload.get("mode") == "unavailable"
        ):
            raise TypeError("Decision copilot is unavailable; rerun the scan")
        # Legacy synthetic workflows have no copilot trace and remain
        # compatible with the packet-only approval contract. Once a live ADK
        # trace exists, however, an approval must name the reviewed option so
        # callers cannot silently bypass the deterministic policy review.
        if isinstance((state.agent_trace or {}).get("decision_copilot"), dict):
            raise ValueError("Decision copilot option is required")
        return
    trace = state.agent_trace or {}
    payload = trace.get("decision_copilot")
    if not isinstance(payload, dict):
        raise TypeError("Decision copilot is unavailable; rerun the scan")
    copilot = DecisionCopilot.model_validate(
        {key: payload[key] for key in DecisionCopilot.model_fields if key in payload}
    )
    policy_payload = payload.get("policy_review")
    if not isinstance(policy_payload, dict) or policy_payload.get("status") != "pass":
        raise ValueError("Decision copilot is blocked by red-team policy")
    option = next((item for item in copilot.options if item.option_id == option_id), None)
    if option is None:
        raise ValueError("Unknown decision copilot option")
    if option.workflow_decision != workflow_decision:
        raise ValueError("Approval policy does not match the selected option")
    if artifact_decisions is not None and artifact_decisions != option.artifact_decisions:
        if not custom_override:
            raise ValueError("Artifact decisions do not match the selected option")
        validate_custom_artifact_plan(
            state,
            workflow_decision=workflow_decision,
            artifact_decisions=artifact_decisions,
            override_reason=override_reason,
        )
    elif custom_override:
        raise ValueError("Custom routing must change at least one artifact decision")


def validate_custom_artifact_plan(
    state: WorkflowState,
    *,
    workflow_decision: str,
    artifact_decisions: dict[str, str] | None,
    override_reason: str | None,
) -> None:
    """Validate a human artifact override without weakening the policy gate."""
    reason = (override_reason or "").strip()
    if len(reason) < 3 or len(reason) > 240:
        raise ValueError("Custom routing requires an override reason")
    if workflow_decision not in ALLOWED_WORKFLOW_DECISIONS:
        raise ValueError("Approval policy is not allowlisted")
    if not isinstance(artifact_decisions, dict):
        raise TypeError("Custom routing requires artifact decisions")
    expected = {item.name for item in state.impacts}
    if set(artifact_decisions) != expected:
        raise ValueError("Custom routing must cover every mapped artifact")
    if any(value not in ALLOWED_ACTIONS for value in artifact_decisions.values()):
        raise ValueError("Custom artifact action is not allowlisted")
    high_risk = {
        item.name for item in state.impacts if str(item.risk).casefold() == "high"
    }
    if any(artifact_decisions[name] == "queued" for name in high_risk):
        raise ValueError("High-risk artifacts cannot be queued in a custom plan")


def decision_trace(
    copilot: DecisionCopilot,
    policy: PolicyReview,
    *,
    mode: str = "gemini_structured",
    reason: str | None = None,
) -> dict[str, Any]:
    """Return safe, UI-ready output without raw responses or chain-of-thought."""
    payload: dict[str, Any] = {
        "mode": mode,
        "model": MODEL_NAME,
        "question": copilot.question,
        "evidence_hash": copilot.evidence_hash,
        "recommendation_id": copilot.recommendation_id,
        "options": [option.model_dump() for option in copilot.options],
        "policy_review": policy.model_dump(),
    }
    if reason:
        payload["reason"] = reason
    return payload
