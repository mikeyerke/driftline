"""Deterministic PM operating-loop projection for one decision case.

This module is deliberately read-only. It turns the durable Decision Twin state
into one compact interface that the UI and tests can consume. Evidence analysis
may come from Gemini/ADK, but source truth, human authority, execution state,
outcome evaluation, and memory confidence remain explicit and deterministic.
"""

from __future__ import annotations

from statistics import fmean
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SourceMode = Literal[
    "connected_observed",
    "pinned_demo_evidence",
    "pm_provided_unverified",
    "bounded_precedent",
]


class HarvestedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=180)
    channel: Literal[
        "customer_research",
        "support",
        "product_surface",
        "product_analytics",
        "roadmap",
        "decision_memory",
    ]
    mode: SourceMode
    status: Literal["changed", "needs_verification", "historical"]
    observed_at: str = Field(min_length=1, max_length=50)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_node_ids: list[str] = Field(default_factory=list, max_length=32)


class EvidenceHarvestState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "verification_required"]
    source_count: int = Field(ge=0, le=64)
    changed_source_count: int = Field(ge=0, le=64)
    sources: list[HarvestedSource] = Field(default_factory=list, max_length=64)
    covered_channels: list[str] = Field(default_factory=list, max_length=12)
    missing_channels: list[str] = Field(default_factory=list, max_length=12)
    disclosure: str = Field(min_length=1, max_length=320)


class AlignmentPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position_id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=100)
    input_mode: Literal["evidence_bound_decision_lens", "pm_provided"]
    preferred_option: str = Field(min_length=1, max_length=40)
    thesis: str = Field(min_length=1, max_length=360)
    evidence_node_ids: list[str] = Field(default_factory=list, max_length=8)
    would_change_position_if: str = Field(min_length=1, max_length=240)


class StakeholderAlignmentState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "unresolved_tradeoff", "approved_with_dissent", "measurement_resolved"
    ]
    dissent_preserved: bool
    apparent_consensus_risk: bool
    positions: list[AlignmentPosition] = Field(min_length=1, max_length=8)
    unresolved_tradeoffs: list[str] = Field(default_factory=list, max_length=4)
    evidence_requests: list[str] = Field(default_factory=list, max_length=6)
    disclosure: str = Field(min_length=1, max_length=280)


class ExecutionContractState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["awaiting_approval", "active", "completed", "rolled_back"]
    owner: str | None = Field(default=None, min_length=2, max_length=120)
    approved_option: str | None = Field(default=None, max_length=40)
    scope: str = Field(min_length=1, max_length=240)
    exclusions: list[str] = Field(default_factory=list, max_length=6)
    success_condition: str | None = Field(default=None, max_length=240)
    stop_conditions: list[str] = Field(default_factory=list, max_length=6)
    review_at: str | None = Field(default=None, max_length=50)
    next_action: str = Field(min_length=1, max_length=280)
    external_writes: Literal[False] = False


class OutcomeAutopilotState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "awaiting_approval",
        "scheduled",
        "awaiting_data",
        "evaluated",
        "reopened",
    ]
    next_check_at: str | None = Field(default=None, max_length=50)
    observation_count: int = Field(ge=0, le=64)
    latest_verdict: str | None = Field(default=None, max_length=40)
    trigger: str = Field(min_length=1, max_length=280)
    recommended_response: str = Field(min_length=1, max_length=280)


class MemoryInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal[
        "source_reliability", "decision_pattern", "segment_response", "calibration"
    ]
    statement: str = Field(min_length=1, max_length=320)
    sample_size: int = Field(ge=0, le=10000)
    recency: str = Field(min_length=1, max_length=80)
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: list[str] = Field(default_factory=list, max_length=12)


class CompoundingMemoryState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cycle_count: int = Field(ge=0, le=1000)
    precedent_count: int = Field(ge=0, le=1000)
    current_generation: int = Field(ge=1, le=1000)
    insights: list[MemoryInsight] = Field(default_factory=list, max_length=12)
    disclosure: str = Field(min_length=1, max_length=280)


class JourneyCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step: int = Field(ge=1, le=10)
    label: str = Field(min_length=1, max_length=100)
    state: Literal["done", "active", "waiting"]


class ProductOperatingLoop(BaseModel):
    """One interface for the seven PM capabilities and ten-step journey."""

    model_config = ConfigDict(extra="forbid")

    stage: Literal[
        "decision_required", "human_approval", "execution", "measurement", "learning"
    ]
    evidence_harvest: EvidenceHarvestState
    stakeholder_alignment: StakeholderAlignmentState
    execution_contract: ExecutionContractState
    outcome_autopilot: OutcomeAutopilotState
    compounding_memory: CompoundingMemoryState
    journey: list[JourneyCheckpoint] = Field(min_length=10, max_length=10)
    refreshed_at: str = Field(min_length=1, max_length=50)


_CHANNELS = {
    "customer": "customer_research",
    "support": "support",
    "image": "product_surface",
    "metric": "product_analytics",
    "commitment": "roadmap",
}
_ROLE_LABELS = {
    "customer": "Customer evidence lens",
    "usage": "Usage evidence lens",
    "strategy": "Strategy and commitment lens",
    "feasibility": "Delivery and reversibility lens",
    "challenger": "Independent challenge lens",
}


def _source_mode(label: str) -> SourceMode:
    normalized = label.casefold()
    if "pm-provided" in normalized:
        return "pm_provided_unverified"
    if "fixture" in normalized or "demo" in normalized:
        return "pinned_demo_evidence"
    if "bigquery" in normalized or "observed snapshot" in normalized:
        return "connected_observed"
    if "precedent" in normalized:
        return "bounded_precedent"
    return "pinned_demo_evidence"


def _harvest(case: Any) -> EvidenceHarvestState:
    grouped: dict[tuple[str, str], list[Any]] = {}
    for node in case.evidence_nodes:
        grouped.setdefault((node.source_label, _CHANNELS[node.kind]), []).append(node)
    sources: list[HarvestedSource] = []
    for index, ((label, channel), nodes) in enumerate(grouped.items(), start=1):
        mode = _source_mode(label)
        sources.append(
            HarvestedSource(
                source_id=f"source-{index}-{channel}",
                label=label,
                channel=channel,
                mode=mode,
                status=(
                    "needs_verification"
                    if mode == "pm_provided_unverified"
                    else "changed"
                ),
                observed_at=max(node.observed_at for node in nodes),
                confidence=fmean(node.confidence for node in nodes),
                evidence_node_ids=[node.node_id for node in nodes],
            )
        )
    for precedent in case.precedents:
        sources.append(
            HarvestedSource(
                source_id=precedent.precedent_id,
                label=precedent.source_label,
                channel="decision_memory",
                mode="bounded_precedent",
                status="historical",
                observed_at="historical precedent",
                confidence=precedent.similarity,
                evidence_node_ids=[],
            )
        )
    covered = sorted({source.channel for source in sources})
    expected = {
        "customer_research",
        "support",
        "product_surface",
        "product_analytics",
        "roadmap",
    }
    needs_verification = any(
        source.mode == "pm_provided_unverified" for source in sources
    )
    return EvidenceHarvestState(
        status="verification_required" if needs_verification else "ready",
        source_count=len(sources),
        changed_source_count=sum(source.status == "changed" for source in sources),
        sources=sources,
        covered_channels=covered,
        missing_channels=sorted(expected - set(covered)),
        disclosure=(
            "PM-provided context is structured but remains unverified until a connected or independently observed source corroborates it."
            if needs_verification
            else "The public case uses clearly labelled replayable evidence; connected BigQuery projections are labelled separately when available."
        ),
    )


def _alignment(case: Any) -> StakeholderAlignmentState:
    positions = [
        AlignmentPosition(
            position_id=position.role,
            label=_ROLE_LABELS[position.role],
            input_mode="evidence_bound_decision_lens",
            preferred_option=position.recommendation,
            thesis=position.thesis,
            evidence_node_ids=list(
                dict.fromkeys(
                    position.supporting_node_ids + position.contradicting_node_ids
                )
            ),
            would_change_position_if=position.would_change_mind_if,
        )
        for position in case.council.positions
    ]
    recommendations = {position.preferred_option for position in positions}
    resolved = case.status == "validated"
    approved = case.approval is not None or bool(case.decision_history)
    challenger = next(
        position for position in positions if position.position_id == "challenger"
    )
    return StakeholderAlignmentState(
        status=(
            "measurement_resolved"
            if resolved
            else "approved_with_dissent"
            if approved
            else "unresolved_tradeoff"
        ),
        dissent_preserved=len(recommendations) > 1,
        apparent_consensus_risk=len(recommendations) == 1,
        positions=positions,
        unresolved_tradeoffs=[] if resolved else [case.council.decisive_conflict],
        evidence_requests=[] if resolved else [challenger.would_change_position_if],
        disclosure=(
            "These are evidence-bound decision lenses, not fabricated quotes from human stakeholders. Human positions should be collected explicitly in a signed workspace."
        ),
    )


def _execution(case: Any) -> ExecutionContractState:
    plan = case.experiment_plan
    latest_action = case.action_records[-1] if case.action_records else None
    if latest_action is None:
        status = "awaiting_approval"
    else:
        status = latest_action.status
    if plan is None:
        recommended = next(
            option
            for option in case.council.options
            if option.option_id == case.council.recommendation
        )
        return ExecutionContractState(
            status=status,
            scope=recommended.summary,
            exclusions=[
                "No external system write before named human approval",
                "No unsupported roadmap, pricing, or customer-message mutation",
            ],
            stop_conditions=recommended.guardrails,
            next_action="Name the human owner and approve one reversible option.",
        )
    return ExecutionContractState(
        status=status,
        owner=plan.owner or (case.approval.approver if case.approval else None),
        approved_option=plan.option_id,
        scope=f"{plan.hypothesis} Target: {plan.target_segment}.",
        exclusions=[
            "Decision state only; no external write in the public lane",
            "No expansion outside the approved target segment",
        ],
        success_condition=plan.success_condition,
        stop_conditions=plan.stop_conditions,
        review_at=plan.review_at,
        next_action=(
            "Review the rebuilt council before authorizing generation "
            f"{case.generation}."
            if case.status == "reopened"
            else "Collect the named primary and risk measurements at the review window."
        ),
    )


def _outcome(case: Any) -> OutcomeAutopilotState:
    latest = case.outcomes[-1] if case.outcomes else None
    latest_verdict = latest.evaluation.verdict if latest and latest.evaluation else None
    if case.status == "reopened":
        status = "reopened"
    elif latest_verdict:
        status = "evaluated"
    elif case.experiment_plan is not None:
        status = "scheduled" if not case.outcomes else "awaiting_data"
    else:
        status = "awaiting_approval"
    return OutcomeAutopilotState(
        status=status,
        next_check_at=case.experiment_plan.review_at if case.experiment_plan else None,
        observation_count=len(case.outcomes),
        latest_verdict=latest_verdict,
        trigger=(
            case.reopen_reason
            or (
                "The approved measurement contract is waiting for its review window."
                if case.experiment_plan
                else "Monitoring begins only after a named human approval."
            )
        ),
        recommended_response=(
            case.decision_debt.recommended_next_step
            if case.decision_debt
            else "Keep the decision under explicit human review."
        ),
    )


def _memory(case: Any) -> CompoundingMemoryState:
    insights: list[MemoryInsight] = []
    if case.evidence_nodes:
        confidence = fmean(node.confidence for node in case.evidence_nodes)
        insights.append(
            MemoryInsight(
                category="source_reliability",
                statement="Current evidence confidence is an input-quality signal, not proof that the recommendation is correct.",
                sample_size=len(case.evidence_nodes),
                recency=max(node.observed_at for node in case.evidence_nodes),
                confidence=confidence,
                provenance=[node.node_id for node in case.evidence_nodes[:12]],
            )
        )
    for precedent in case.precedents[:3]:
        insights.append(
            MemoryInsight(
                category="decision_pattern",
                statement=precedent.lesson,
                sample_size=1,
                recency="historical precedent",
                confidence=precedent.similarity,
                provenance=[precedent.precedent_id],
            )
        )
    if case.decision_history:
        verdicts = [record.outcome_verdict for record in case.decision_history]
        insights.append(
            MemoryInsight(
                category="calibration",
                statement=f"{len(verdicts)} prior decision cycle(s) retained; latest measured verdict: {verdicts[-1]}.",
                sample_size=len(verdicts),
                recency=case.decision_history[-1].trigger_observation.observed_at,
                confidence=min(1.0, 0.55 + 0.1 * len(verdicts)),
                provenance=[
                    record.trigger_observation.observation_id
                    for record in case.decision_history[-12:]
                ],
            )
        )
    else:
        insights.append(
            MemoryInsight(
                category="calibration",
                statement="No measured cycle exists yet, so Driftline cannot claim decision accuracy for this case.",
                sample_size=0,
                recency="not yet measured",
                confidence=0.0,
                provenance=[],
            )
        )
    return CompoundingMemoryState(
        cycle_count=len(case.decision_history),
        precedent_count=len(case.precedents),
        current_generation=case.generation,
        insights=insights,
        disclosure="Memory remains cited, sample-sized, recency-labelled, and non-authoritative.",
    )


def _journey(case: Any) -> list[JourneyCheckpoint]:
    recommendations = {position.recommendation for position in case.council.positions}
    checks = [
        ("Source change observed", bool(case.evidence_nodes)),
        ("Affected commitment identified", bool(case.current_commitment)),
        ("Decision inbox item created", case.decision_debt is not None),
        ("Cited evidence harvested", bool(case.council.evidence_node_ids)),
        ("Disagreement and missing evidence exposed", len(recommendations) > 1),
        ("Bounded options proposed", len(case.council.options) >= 3),
        ("Named human approval recorded", case.approval is not None or bool(case.decision_history)),
        ("Execution contract activated", case.experiment_plan is not None or bool(case.decision_history)),
        ("Outcome measured", bool(case.outcomes)),
        ("Memory updated or decision reopened", bool(case.decision_history) or case.status == "validated"),
    ]
    first_waiting = next((index for index, (_, done) in enumerate(checks) if not done), None)
    return [
        JourneyCheckpoint(
            step=index + 1,
            label=label,
            state="done" if done else "active" if index == first_waiting else "waiting",
        )
        for index, (label, done) in enumerate(checks)
    ]


def build_product_operating_loop(case: Any) -> ProductOperatingLoop:
    """Project a DecisionCase through one stable, read-only interface."""
    if case.status in {"reopened", "validated", "review_required"}:
        stage = "learning"
    elif case.outcomes:
        stage = "measurement"
    elif case.experiment_plan is not None:
        stage = "execution"
    elif case.approval is None:
        stage = "human_approval"
    else:
        stage = "decision_required"
    durable_times = [node.observed_at for node in case.evidence_nodes]
    if case.approval is not None:
        durable_times.append(case.approval.approved_at)
    durable_times.extend(outcome.observed_at for outcome in case.outcomes)
    return ProductOperatingLoop(
        stage=stage,
        evidence_harvest=_harvest(case),
        stakeholder_alignment=_alignment(case),
        execution_contract=_execution(case),
        outcome_autopilot=_outcome(case),
        compounding_memory=_memory(case),
        journey=_journey(case),
        refreshed_at=max(durable_times),
    )
