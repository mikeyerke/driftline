"""Evidence-bound structured impact analysis for Driftline workflows.

The model is allowed to propose impact mappings and draft text only.  This
module owns the narrow output contract and validation seam; approval and
publishing remain deterministic responsibilities of ``workflow.py``.
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.types import GenerateContentConfig, ThinkingConfig
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .models import ArtifactImpact, WorkflowState

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.5-flash")
ALLOWED_ARTIFACTS = {
    "Pricing battlecard": "Product Marketing",
    "Renewal playbook": "Customer Success",
    "Enterprise FAQ": "Support",
    "CRM guidance": "RevOps",
}
ALLOWED_RISKS = {"low", "medium", "high"}


class ProposedArtifact(BaseModel):
    """One model-proposed artifact impact.

    ``extra=forbid`` prevents a model from smuggling an action or approval
    instruction into the payload.  Actions here are descriptions only; the
    deterministic approval endpoint has its own allowlist.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    owner: str = Field(min_length=1, max_length=80)
    action: str = Field(min_length=1, max_length=100)
    risk: Literal["low", "medium", "high"]
    detail: str = Field(min_length=1, max_length=240)
    proposed: str = Field(min_length=1, max_length=500)
    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class StructuredAnalysis(BaseModel):
    """Strict, concise model output persisted in the agent trace."""

    model_config = ConfigDict(extra="forbid")

    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary: str = Field(min_length=1, max_length=240)
    rationale: str = Field(min_length=1, max_length=240)
    artifacts: list[ProposedArtifact] = Field(min_length=1, max_length=4)


class AnalysisUnavailable(RuntimeError):
    """Raised when structured Gemini analysis cannot be safely used."""


analysis_agent = Agent(
    name="driftline_impact_analyst",
    model=MODEL_NAME,
    # ADK's Runner accepts chat/task roots; task keeps this analyst bounded
    # while remaining compatible with the deployed ADK runtime. We request
    # JSON MIME output and apply the stricter Pydantic contract below; this
    # avoids version-specific ADK output-schema coercion while preserving a
    # fail-closed validation boundary before any workflow state is changed.
    mode="task",
    generate_content_config=GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=StructuredAnalysis.model_json_schema(),
        max_output_tokens=1200,
        thinking_config=ThinkingConfig(thinking_level="LOW"),
    ),
    description=(
        "Evidence-bound impact analyst that proposes downstream artifact "
        "updates without approval or publishing authority."
    ),
    instruction=(
        "Return only the requested JSON schema. Analyze the supplied source "
        "diff and propose exactly the four allowed artifacts. Ground every "
        "artifact in the supplied evidence hash. Use concise rationale and "
        "draft text; never provide hidden chain-of-thought. You have no tools, "
        "approval authority, or publishing authority. Do not invent a source "
        "or claim an external system changed."
    ),
)


def _analysis_prompt(state: WorkflowState) -> str:
    evidence = state.evidence
    if evidence is None:
        raise AnalysisUnavailable("Workflow has no source evidence")
    allowed = ", ".join(
        f"{name} (owner: {owner})" for name, owner in ALLOWED_ARTIFACTS.items()
    )
    return (
        "Analyze this verified source change. Return the strict JSON output "
        "schema, with exactly one artifact entry for each allowed artifact.\n\n"
        f"Source ID: {evidence.source_id}\n"
        f"Source label: {evidence.snapshot_label}\n"
        f"Source URL: {evidence.source_url or 'unavailable'}\n"
        f"Evidence hash: {evidence.evidence_hash}\n"
        f"Before: {evidence.before}\n"
        f"After: {evidence.after}\n"
        f"Allowed artifacts: {allowed}\n\n"
        "The evidence_hash on the top-level result and every artifact must "
        "exactly match the supplied evidence hash. Describe proposed updates "
        "only; do not approve, publish, or claim an external write."
    )


async def _run_analysis_events(prompt: str) -> list[str]:
    """Run one ADK structured-output turn and return text parts only."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="driftline",
        user_id="impact-analyst",
        session_id=os.urandom(12).hex(),
    )
    runner = Runner(
        agent=analysis_agent,
        app_name="driftline",
        session_service=session_service,
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    text_parts: list[str] = []
    async for event in runner.run_async(
        user_id="impact-analyst",
        session_id=session.id,
        new_message=message,
    ):
        if (
            not event.is_final_response()
            or not event.content
            or not event.content.parts
        ):
            continue
        text_parts.extend(
            part.text for part in event.content.parts if getattr(part, "text", None)
        )
    return text_parts


def validate_analysis(payload: Any, expected_evidence_hash: str) -> StructuredAnalysis:
    """Validate model output and enforce Driftline's artifact/evidence policy."""
    try:
        result = (
            payload
            if isinstance(payload, StructuredAnalysis)
            else StructuredAnalysis.model_validate(payload)
        )
    except (ValidationError, TypeError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            first = exc.errors()[0] if exc.errors() else {}
            location = ".".join(str(part) for part in first.get("loc", ()))
            raise AnalysisUnavailable(
                f"Structured analysis failed schema validation at {location or 'root'}"
            ) from exc
        raise AnalysisUnavailable(
            "Structured analysis failed schema validation"
        ) from exc

    if result.evidence_hash != expected_evidence_hash:
        raise AnalysisUnavailable("Structured analysis used the wrong evidence hash")
    if len(result.artifacts) != len(ALLOWED_ARTIFACTS):
        raise AnalysisUnavailable("Structured analysis must cover all four artifacts")

    names = [item.name for item in result.artifacts]
    if set(names) != set(ALLOWED_ARTIFACTS) or len(set(names)) != len(names):
        raise AnalysisUnavailable("Structured analysis named an unapproved artifact")
    for item in result.artifacts:
        if item.owner != ALLOWED_ARTIFACTS[item.name]:
            raise AnalysisUnavailable("Structured analysis changed an artifact owner")
        if item.risk not in ALLOWED_RISKS:
            raise AnalysisUnavailable("Structured analysis used an unknown risk")
        if item.evidence_hash != expected_evidence_hash:
            raise AnalysisUnavailable("Artifact is not bound to source evidence")
    return result


def apply_analysis(state: WorkflowState, result: StructuredAnalysis) -> None:
    """Replace deterministic draft tuples with validated model proposals."""
    if state.evidence is None:
        raise AnalysisUnavailable("Workflow has no source evidence")
    validated = validate_analysis(result, state.evidence.evidence_hash)
    state.impacts = [
        ArtifactImpact(
            item.name,
            item.owner,
            item.action,
            item.risk,
            "draft_ready",
            item.detail,
            item.proposed,
            item.evidence_hash,
        )
        for item in validated.artifacts
    ]


async def analyze_workflow(state: WorkflowState) -> StructuredAnalysis:
    """Ask Gemini for structured proposals and fail closed on any mismatch."""
    if state.evidence is None:
        raise AnalysisUnavailable("Workflow has no source evidence")
    text_parts = await _run_analysis_events(_analysis_prompt(state))
    raw = "".join(text_parts).strip()
    if not raw:
        raise AnalysisUnavailable("Gemini returned no structured analysis")
    # Gemini occasionally wraps otherwise valid JSON in a markdown fence even
    # when JSON MIME output is requested. Extract only one object and continue
    # through the same strict Pydantic/evidence validator; never accept prose
    # or a partial object as a model proposal.
    if raw.startswith("```"):
        raw = raw.removeprefix("```").removeprefix("json").strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    if not raw.startswith("{"):
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnalysisUnavailable(
            "Gemini returned non-JSON structured analysis"
        ) from exc
    result = validate_analysis(payload, state.evidence.evidence_hash)
    apply_analysis(state, result)
    return result


def analysis_trace(result: StructuredAnalysis) -> dict[str, Any]:
    """Return safe observability fields; never persist chain-of-thought/raw JSON."""
    return {
        "mode": "gemini_structured",
        "model": MODEL_NAME,
        "summary": result.summary,
        "rationale": result.rationale,
        "evidence_hash": result.evidence_hash,
        "artifact_count": len(result.artifacts),
    }
