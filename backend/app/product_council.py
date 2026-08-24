"""Bounded Google ADK council for evidence-grounded product decisions."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from typing import Literal
from uuid import uuid4

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.types import GenerateContentConfig, ThinkingConfig
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .decision_twin import (
    CouncilPosition,
    CouncilRole,
    CouncilSynthesis,
    DecisionCase,
    DecisionTwinPolicyError,
    validate_council,
)

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.5-flash")
APP_NAME = "driftline-decision-twin"
COUNCIL_ROLES: tuple[CouncilRole, ...] = (
    "customer",
    "usage",
    "strategy",
    "feasibility",
    "challenger",
)
ROLE_MANDATES: dict[CouncilRole, tuple[str, str]] = {
    "customer": (
        "protect_user_trust",
        (
            "Prioritize customer comprehension, access, support friction, and trust. "
            "Resist shipping a broad change when cited customer evidence shows a "
            "segment-specific harm."
        ),
    ),
    "usage": (
        "trust_segment_measurement",
        (
            "Prioritize measured segment outcomes, sample sufficiency, freshness, "
            "and causal uncertainty. Prefer a bounded test when aggregate evidence "
            "does not justify broad rollout."
        ),
    ),
    "strategy": (
        "honor_current_commitment",
        (
            "Make the strongest evidence-grounded case for honoring the current "
            "commitment and strategic coherence, while naming any cited evidence "
            "that makes that position untenable."
        ),
    ),
    "feasibility": (
        "prefer_safe_execution",
        (
            "Prioritize reversibility, implementation scope, operational "
            "guardrails, and the safest executable option supported by the "
            "supplied evidence."
        ),
    ),
    "challenger": (
        "seek_credible_minority_case",
        (
            "Stress-test the apparently strongest option. Seek the strongest "
            "credible minority recommendation supported by supplied evidence "
            "instead of echoing an obvious consensus; never invent evidence or "
            "dissent."
        ),
    ),
}
ROLE_RECOMMENDATIONS: dict[CouncilRole, Literal["ship", "rollback", "segment", "defer"]] = {
    "customer": "segment",
    "usage": "segment",
    "strategy": "ship",
    "feasibility": "segment",
    "challenger": "defer",
}


class ProductCouncilUnavailable(RuntimeError):
    """Raised when a complete live council cannot be validated."""


class CouncilDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation: Literal["ship", "rollback", "segment", "defer"]
    executive_summary: str = Field(min_length=1, max_length=500)
    decisive_conflict: str = Field(min_length=1, max_length=360)


def _agent(role: CouncilRole) -> Agent:
    return Agent(
        name=f"driftline_{role}_agent",
        model=MODEL_NAME,
        mode="task",
        tools=[],
        output_schema=CouncilPosition,
        generate_content_config=GenerateContentConfig(
            max_output_tokens=900,
            thinking_config=ThinkingConfig(thinking_level="LOW"),
        ),
        description=f"Read-only {role} perspective for a product decision.",
        instruction=(
            f"Act only as the {role} product-council role. Return the requested "
            "JSON schema and set role exactly to the assigned role. Select one "
            "bounded recommendation and use the prompt's required_recommendation "
            "exactly; this preserves the independent role prior rather than an "
            "accidental consensus. Cite only supplied evidence node IDs. Include "
            "material risks and one measurable condition that would change your "
            "position. Do not approve anything, create work, call tools, or reveal "
            "chain-of-thought."
        ),
    )


def build_council_agents() -> dict[CouncilRole, Agent]:
    """Create five independent agents with no tools or mutation authority."""
    return {role: _agent(role) for role in COUNCIL_ROLES}


def _bounded_manifest(case: DecisionCase) -> list[dict[str, object]]:
    return [
        {
            "node_id": node.node_id,
            "kind": node.kind,
            "title": node.title,
            "excerpt": node.excerpt,
            "source_label": node.source_label,
            "observed_at": node.observed_at,
            "confidence": node.confidence,
            "segment": node.segment,
            "value": node.value,
            "unit": node.unit,
        }
        for node in case.evidence_nodes
    ]


def build_council_prompt(case: DecisionCase, role: CouncilRole) -> str:
    if role not in COUNCIL_ROLES:
        raise DecisionTwinPolicyError("Unknown product-council role")
    evaluation_prior, decision_mandate = ROLE_MANDATES[role]
    return json.dumps(
        {
            "assigned_role": role,
            "evaluation_prior": evaluation_prior,
            "decision_mandate": decision_mandate,
            "required_recommendation": ROLE_RECOMMENDATIONS[role],
            "decision_question": case.question,
            "current_commitment": case.current_commitment,
            "urgency": case.urgency,
            "allowed_recommendations": ["ship", "rollback", "segment", "defer"],
            "evidence": _bounded_manifest(case),
            "output_rule": "Cite only supplied node_id values.",
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def deterministic_council(case: DecisionCase) -> CouncilSynthesis:
    """Return the pinned public fallback without presenting it as a live model run."""
    council = case.council.model_copy(deep=True)
    council.mode = "deterministic_demo_fallback"
    return council


async def _run_json(agent: Agent, prompt: str) -> str:
    sessions = InMemorySessionService()
    session = await sessions.create_session(
        app_name=APP_NAME,
        user_id="decision-twin",
        session_id=str(uuid4()),
    )
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=sessions)
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    final_text = ""
    task_output: object | None = None
    async for event in runner.run_async(
        user_id="decision-twin", session_id=session.id, new_message=message
    ):
        if event.output is not None:
            task_output = event.output
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(
                part.text or "" for part in event.content.parts if part.text
            )
    if task_output is not None:
        if isinstance(task_output, str):
            return task_output
        return json.dumps(task_output, sort_keys=True, separators=(",", ":"))
    if not final_text.strip():
        raise ProductCouncilUnavailable(f"{agent.name} returned no structured result")
    return final_text


async def _run_position(
    case: DecisionCase, role: CouncilRole, agent: Agent
) -> CouncilPosition:
    try:
        position = CouncilPosition.model_validate_json(
            await _run_json(agent, build_council_prompt(case, role))
        )
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise ProductCouncilUnavailable(
            f"{role} position failed schema validation"
        ) from exc
    if position.role != role:
        raise ProductCouncilUnavailable(
            f"{role} agent returned the wrong council identity"
        )
    if position.recommendation != ROLE_RECOMMENDATIONS[role]:
        raise ProductCouncilUnavailable(
            f"{role} agent did not honor its council mandate"
        )
    known = {node.node_id for node in case.evidence_nodes}
    cited = position.supporting_node_ids + position.contradicting_node_ids
    if any(node_id not in known for node_id in cited):
        raise ProductCouncilUnavailable(f"{role} position cited unknown evidence")
    return position


def _synthesis_agent() -> Agent:
    return Agent(
        name="driftline_council_synthesizer",
        model=MODEL_NAME,
        mode="task",
        tools=[],
        output_schema=CouncilDraft,
        generate_content_config=GenerateContentConfig(
            max_output_tokens=800,
            thinking_config=ThinkingConfig(thinking_level="LOW"),
        ),
        description="Synthesizes validated council disagreement without authority.",
        instruction=(
            "Return only the requested JSON. Choose one bounded recommendation, "
            "summarize the strongest evidence, and name the decisive disagreement. "
            "Do not erase minority positions, approve work, or invent evidence."
        ),
    )


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


async def _run_live_product_council(case: DecisionCase) -> CouncilSynthesis:
    """Run five independent positions and one bounded synthesis turn."""
    agents = build_council_agents()
    positions = await asyncio.gather(
        *(_run_position(case, role, agents[role]) for role in COUNCIL_ROLES)
    )
    if len({position.recommendation for position in positions}) < 2:
        raise ProductCouncilUnavailable("Live council did not preserve disagreement")
    synthesis_prompt = json.dumps(
        {
            "question": case.question,
            "positions": [position.model_dump(mode="json") for position in positions],
            "allowed_recommendations": ["ship", "rollback", "segment", "defer"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    try:
        draft = CouncilDraft.model_validate_json(
            await _run_json(_synthesis_agent(), synthesis_prompt)
        )
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise ProductCouncilUnavailable(
            "Council synthesis failed schema validation"
        ) from exc
    payload = {
        "question": case.question,
        "recommendation": draft.recommendation,
        "positions": [position.model_dump(mode="json") for position in positions],
        "options": [option.model_dump(mode="json") for option in case.council.options],
        "evidence_manifest_hash": case.council.evidence_manifest_hash,
    }
    council = CouncilSynthesis(
        question=case.question,
        recommendation=draft.recommendation,
        executive_summary=draft.executive_summary,
        decisive_conflict=draft.decisive_conflict,
        positions=list(positions),
        options=case.council.options,
        evidence_manifest_hash=case.council.evidence_manifest_hash,
        synthesis_hash=_hash(payload),
        mode="google_adk",
    )
    checked = case.model_copy(deep=True)
    checked.council = council
    validate_council(checked)
    return council


async def run_live_product_council(case: DecisionCase) -> CouncilSynthesis:
    """Run the live council and expose only a bounded availability failure."""
    try:
        return await _run_live_product_council(case)
    except ProductCouncilUnavailable:
        raise
    except Exception as exc:
        raise ProductCouncilUnavailable(
            "Google ADK council runtime unavailable"
        ) from exc
