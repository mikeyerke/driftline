"""Evidence-bound product decisions with deterministic approval and reopening.

The Decision Twin deliberately separates model analysis from authority. Gemini
and ADK may produce schema-constrained council positions; this module validates
their evidence citations, builds bounded counterfactuals, records a named human
decision, and evaluates later outcomes without giving a model write authority.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DecisionOptionId = Literal["ship", "rollback", "segment", "defer"]
CouncilRole = Literal[
    "customer", "usage", "strategy", "feasibility", "challenger"
]


class DecisionTwinPolicyError(ValueError):
    """Raised when evidence or a decision transition violates policy."""


class EvidenceNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,80}$")
    kind: Literal["customer", "support", "image", "metric", "commitment"]
    title: str = Field(min_length=1, max_length=120)
    excerpt: str = Field(min_length=1, max_length=600)
    source_label: str = Field(min_length=1, max_length=160)
    observed_at: str = Field(min_length=1, max_length=50)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    confidence: float = Field(ge=0.0, le=1.0)
    segment: str | None = Field(default=None, max_length=80)
    value: float | None = None
    unit: str | None = Field(default=None, max_length=40)


class EvidenceEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    target_id: str
    relation: Literal[
        "supports", "contradicts", "affects", "commits_to", "measures"
    ]


class CouncilPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: CouncilRole
    recommendation: DecisionOptionId
    thesis: str = Field(min_length=1, max_length=360)
    supporting_node_ids: list[str] = Field(min_length=1, max_length=5)
    contradicting_node_ids: list[str] = Field(default_factory=list, max_length=5)
    risks: list[str] = Field(min_length=1, max_length=4)
    would_change_mind_if: str = Field(min_length=1, max_length=240)


class CounterfactualOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_id: DecisionOptionId
    title: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=320)
    affected_segments: list[str] = Field(min_length=1, max_length=4)
    expected_outcome: str = Field(min_length=1, max_length=240)
    risks: list[str] = Field(min_length=1, max_length=4)
    guardrails: list[str] = Field(min_length=1, max_length=4)
    would_change_mind_if: str = Field(min_length=1, max_length=240)
    rollback: str = Field(min_length=1, max_length=240)
    evidence_node_ids: list[str] = Field(min_length=1, max_length=8)
    reversible: bool = True


class CouncilSynthesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=280)
    recommendation: DecisionOptionId
    executive_summary: str = Field(min_length=1, max_length=500)
    decisive_conflict: str = Field(min_length=1, max_length=360)
    positions: list[CouncilPosition] = Field(min_length=5, max_length=5)
    options: list[CounterfactualOption] = Field(min_length=4, max_length=4)
    evidence_manifest_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    synthesis_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    mode: Literal["google_adk", "deterministic_demo_fallback"]


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approver: str = Field(min_length=2, max_length=120)
    option_id: DecisionOptionId
    synthesis_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    approved_at: str = Field(min_length=1, max_length=50)


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    option_id: DecisionOptionId
    hypothesis: str = Field(min_length=1, max_length=320)
    target_segment: str = Field(min_length=1, max_length=100)
    primary_metric: str = Field(min_length=1, max_length=100)
    success_condition: str = Field(min_length=1, max_length=240)
    guardrails: list[str] = Field(min_length=1, max_length=4)
    stop_conditions: list[str] = Field(min_length=1, max_length=4)
    review_at: str = Field(min_length=1, max_length=50)
    owner_actions: list[str] = Field(min_length=1, max_length=6)
    rollback: str = Field(min_length=1, max_length=240)
    reversible: bool = True


class OutcomeEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Literal["validated", "invalidated", "inconclusive", "awaiting_data"]
    reason: str = Field(min_length=1, max_length=280)
    reopen_required: bool


class OutcomeObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,100}$")
    metric_id: str = Field(min_length=1, max_length=100)
    segment: str = Field(min_length=1, max_length=100)
    value: float
    baseline: float
    unit: str = Field(min_length=1, max_length=40)
    observed_at: str = Field(min_length=1, max_length=50)
    source_label: str = Field(min_length=1, max_length=160)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation: OutcomeEvaluation | None = None


class DecisionHistoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generation: int = Field(ge=1)
    option_id: DecisionOptionId
    approver: str
    synthesis_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    outcome_verdict: str | None = None
    approval: ApprovalRecord
    experiment_plan: ExperimentPlan
    trigger_observation: OutcomeObservation
    reopen_reason: str = Field(min_length=1, max_length=280)


class DecisionCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    tenant_id: str | None = None
    title: str
    question: str
    generation: int = Field(default=1, ge=1)
    status: Literal[
        "needs_approval",
        "experiment_active",
        "validated",
        "reopened",
        "inconclusive",
    ] = "needs_approval"
    current_commitment: str
    urgency: str
    evidence_nodes: list[EvidenceNode] = Field(min_length=1, max_length=24)
    evidence_edges: list[EvidenceEdge] = Field(default_factory=list, max_length=64)
    council: CouncilSynthesis
    approval: ApprovalRecord | None = None
    experiment_plan: ExperimentPlan | None = None
    outcomes: list[OutcomeObservation] = Field(default_factory=list, max_length=32)
    decision_history: list[DecisionHistoryRecord] = Field(
        default_factory=list, max_length=16
    )
    reopen_reason: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list, max_length=64)


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _node(
    node_id: str,
    kind: Literal["customer", "support", "image", "metric", "commitment"],
    title: str,
    excerpt: str,
    source_label: str,
    *,
    segment: str | None = None,
    value: float | None = None,
    unit: str | None = None,
) -> EvidenceNode:
    return EvidenceNode(
        node_id=node_id,
        kind=kind,
        title=title,
        excerpt=excerpt,
        source_label=source_label,
        observed_at="2026-08-23T18:00:00+00:00",
        content_hash=_digest(
            {"node_id": node_id, "source": source_label, "excerpt": excerpt}
        ),
        confidence=0.94 if kind != "customer" else 0.82,
        segment=segment,
        value=value,
        unit=unit,
    )


def _demo_nodes() -> list[EvidenceNode]:
    return [
        _node(
            "call-fast-setup",
            "customer",
            "Smaller teams report faster setup",
            "Three recent calls describe the redesigned setup as faster and clearer.",
            "Redacted customer-call theme fixture",
            segment="small_workspaces",
        ),
        _node(
            "support-permission-confusion",
            "support",
            "Enterprise permission questions increased",
            "Support themes show administrators cannot predict which roles may invite members.",
            "Aggregate support-theme fixture",
            segment="enterprise_workspaces",
        ),
        _node(
            "screenshot-role-step",
            "image",
            "Role selection lacks enterprise context",
            "Gemini Vision identifies one generic role selector with no policy preview.",
            "Pinned onboarding screenshot fixture",
            segment="enterprise_workspaces",
        ),
        _node(
            "metric-activation-split",
            "metric",
            "Activation moved in opposite directions by segment",
            "Small-workspace activation improved 9%; enterprise activation declined 11%.",
            "BigQuery aggregate fixture",
            segment="enterprise_workspaces",
            value=-0.11,
            unit="relative_change",
        ),
        _node(
            "commitment-full-rollout",
            "commitment",
            "Full rollout promised next week",
            "The roadmap commitment schedules the redesigned onboarding for all workspaces.",
            "Roadmap commitment fixture",
        ),
    ]


def _options() -> list[CounterfactualOption]:
    common_evidence = [
        "call-fast-setup",
        "support-permission-confusion",
        "screenshot-role-step",
        "metric-activation-split",
        "commitment-full-rollout",
    ]
    return [
        CounterfactualOption(
            option_id="ship",
            title="Ship to every workspace",
            summary="Keep the committed rollout and monitor enterprise recovery.",
            affected_segments=["small_workspaces", "enterprise_workspaces"],
            expected_outcome="Preserve small-team gains but expose enterprise users to the unresolved permission step.",
            risks=["Enterprise regression may deepen", "Support volume may increase"],
            guardrails=["Enterprise activation must not fall another 3%"],
            would_change_mind_if="Enterprise activation returns to baseline before rollout.",
            rollback="Restore the prior onboarding flow for all workspaces.",
            evidence_node_ids=common_evidence,
        ),
        CounterfactualOption(
            option_id="rollback",
            title="Roll back globally",
            summary="Restore the prior onboarding flow while the redesign is revised.",
            affected_segments=["small_workspaces", "enterprise_workspaces"],
            expected_outcome="Reduce enterprise risk but give up the measured small-team improvement.",
            risks=["Lose the small-team activation gain", "Delay learning"],
            guardrails=["Small-workspace activation must not fall below its prior baseline"],
            would_change_mind_if="The enterprise regression is isolated to a fixable permission explanation.",
            rollback="Re-enable the redesigned flow behind the existing segment gate.",
            evidence_node_ids=common_evidence,
        ),
        CounterfactualOption(
            option_id="segment",
            title="Segment the rollout",
            summary="Keep the redesign for smaller teams and hold enterprise workspaces on the prior flow while testing a permission preview.",
            affected_segments=["small_workspaces", "enterprise_workspaces"],
            expected_outcome="Retain the observed small-team gain while testing the leading enterprise failure mode.",
            risks=["Two onboarding paths require temporary coordination"],
            guardrails=["Enterprise activation may not decline more than 5% in the test"],
            would_change_mind_if="The permission preview fails to recover at least half the enterprise regression.",
            rollback="Return enterprise workspaces to the prior flow and remove the experiment allocation.",
            evidence_node_ids=common_evidence,
        ),
        CounterfactualOption(
            option_id="defer",
            title="Pause and collect evidence",
            summary="Delay rollout until more enterprise interviews and usage observations arrive.",
            affected_segments=["enterprise_workspaces"],
            expected_outcome="Reduce immediate decision risk but miss the committed rollout window.",
            risks=["Roadmap commitment slips", "Small-team gains remain constrained"],
            guardrails=["Decision must be revisited within seven days"],
            would_change_mind_if="Two additional sources confirm the permission step as causal.",
            rollback="Resume the current segment allocation without publishing changes.",
            evidence_node_ids=common_evidence,
        ),
    ]


def _positions() -> list[CouncilPosition]:
    return [
        CouncilPosition(
            role="customer",
            recommendation="segment",
            thesis="Preserve the faster small-team path while enterprise permission confusion is tested directly.",
            supporting_node_ids=["call-fast-setup", "support-permission-confusion"],
            contradicting_node_ids=[],
            risks=["Support themes are aggregate rather than causal proof"],
            would_change_mind_if="Enterprise interviews reject permission clarity as the dominant problem.",
        ),
        CouncilPosition(
            role="usage",
            recommendation="segment",
            thesis="Opposite segment movement makes a global rollout or rollback less defensible than a segmented experiment.",
            supporting_node_ids=["metric-activation-split"],
            contradicting_node_ids=[],
            risks=["Aggregate activation does not establish causality"],
            would_change_mind_if="The enterprise decline disappears after controlling for workspace mix.",
        ),
        CouncilPosition(
            role="strategy",
            recommendation="ship",
            thesis="The announced rollout favors shipping, but the commitment should be narrowed if enterprise risk is material.",
            supporting_node_ids=["commitment-full-rollout", "call-fast-setup"],
            contradicting_node_ids=["metric-activation-split"],
            risks=["A delay may reduce stakeholder confidence"],
            would_change_mind_if="The enterprise regression breaches the approved launch guardrail.",
        ),
        CouncilPosition(
            role="feasibility",
            recommendation="segment",
            thesis="A segment gate is the smallest reversible change and isolates the permission-preview hypothesis.",
            supporting_node_ids=["screenshot-role-step", "metric-activation-split"],
            contradicting_node_ids=[],
            risks=["Temporary dual paths require careful instrumentation"],
            would_change_mind_if="The current rollout system cannot isolate enterprise workspaces safely.",
        ),
        CouncilPosition(
            role="challenger",
            recommendation="defer",
            thesis="The evidence identifies correlation and a plausible interface issue, not a proven cause; one more bounded test may be cheaper than a rollout mistake.",
            supporting_node_ids=["support-permission-confusion", "screenshot-role-step"],
            contradicting_node_ids=["commitment-full-rollout"],
            risks=["The team may overfit to one screenshot and aggregate support themes"],
            would_change_mind_if="A segmented permission-preview test improves enterprise activation without harming setup completion.",
        ),
    ]


def _manifest_hash(nodes: list[EvidenceNode]) -> str:
    return _digest(
        [
            {"node_id": node.node_id, "content_hash": node.content_hash}
            for node in sorted(nodes, key=lambda item: item.node_id)
        ]
    )


def _build_synthesis(nodes: list[EvidenceNode]) -> CouncilSynthesis:
    positions = _positions()
    options = _options()
    manifest_hash = _manifest_hash(nodes)
    raw = {
        "question": "Should the onboarding redesign ship to every workspace next week?",
        "recommendation": "segment",
        "positions": [position.model_dump(mode="json") for position in positions],
        "options": [option.model_dump(mode="json") for option in options],
        "evidence_manifest_hash": manifest_hash,
    }
    return CouncilSynthesis(
        question=raw["question"],
        recommendation="segment",
        executive_summary="Segment the rollout: retain the measured small-team gain, hold enterprise workspaces on the prior path, and test a permission preview against an explicit stop guardrail.",
        decisive_conflict="Strategy favors honoring the announced rollout; usage and customer evidence show the result is not safe to generalize across segments.",
        positions=positions,
        options=options,
        evidence_manifest_hash=manifest_hash,
        synthesis_hash=_digest(raw),
        mode="deterministic_demo_fallback",
    )


def build_demo_decision_case(
    *, case_id: str = "decision-onboarding-segment"
) -> DecisionCase:
    nodes = _demo_nodes()
    case = DecisionCase(
        case_id=case_id,
        title="Onboarding rollout decision",
        question="Should the onboarding redesign ship to every workspace next week?",
        current_commitment="Roll out the redesigned onboarding flow to every workspace next week.",
        urgency="Enterprise activation is down while the public rollout commitment is seven days away.",
        evidence_nodes=nodes,
        evidence_edges=[
            EvidenceEdge(
                source_id="support-permission-confusion",
                target_id="screenshot-role-step",
                relation="supports",
            ),
            EvidenceEdge(
                source_id="metric-activation-split",
                target_id="commitment-full-rollout",
                relation="contradicts",
            ),
            EvidenceEdge(
                source_id="call-fast-setup",
                target_id="metric-activation-split",
                relation="supports",
            ),
        ],
        council=_build_synthesis(nodes),
        events=[
            {
                "event_id": "decision-debt-detected",
                "action": "decision_debt_detector",
                "outcome": "enterprise_guardrail_at_risk",
                "generation": 1,
            },
            {
                "event_id": "product-council-complete",
                "action": "deterministic_product_council",
                "outcome": "fallback_disagreement_fixture",
                "generation": 1,
                "execution_mode": "deterministic_demo_fallback",
            },
        ],
    )
    validate_evidence_graph(case)
    validate_council(case)
    return case


def attach_aggregate_metrics(
    case: DecisionCase, metrics: list[Any]
) -> DecisionCase:
    """Replace the pinned activation split with verified aggregate projections."""
    by_segment = {str(item.segment): item for item in metrics}
    required = {"small_workspaces", "enterprise_workspaces"}
    if set(by_segment) != required:
        raise DecisionTwinPolicyError(
            "Decision Twin requires both allowlisted activation segments"
        )
    if any(str(item.metric_id) != "activation_rate" for item in metrics):
        raise DecisionTwinPolicyError("Decision Twin received an unexpected metric")
    small = by_segment["small_workspaces"]
    enterprise = by_segment["enterprise_workspaces"]
    updated = deepcopy(case)
    node = next(
        item for item in updated.evidence_nodes if item.node_id == "metric-activation-split"
    )
    node.value = float(enterprise.value)
    node.source_label = "BigQuery aggregate · privacy floor ≥25"
    small_observed_at = str(small.observed_at)
    enterprise_observed_at = str(enterprise.observed_at)
    node.observed_at = min(small_observed_at, enterprise_observed_at)
    node.excerpt = (
        f"Small-workspace activation changed {float(small.value):+.0%}; "
        f"enterprise activation changed {float(enterprise.value):+.0%}."
    )
    node.content_hash = _digest(
        {
            "metric_id": "activation_rate",
            "small": float(small.value),
            "small_n": int(small.sample_size),
            "enterprise": float(enterprise.value),
            "enterprise_n": int(enterprise.sample_size),
            "small_observed_at": small_observed_at,
            "enterprise_observed_at": enterprise_observed_at,
        }
    )
    updated.council = _build_synthesis(updated.evidence_nodes)
    updated.events.append(
        {
            "event_id": "bigquery-aggregate-attached",
            "action": "bigquery_aggregate_reader",
            "outcome": "two_segment_projection_attached",
            "generation": updated.generation,
            "minimum_sample_size": min(int(item.sample_size) for item in metrics),
        }
    )
    validate_evidence_graph(updated)
    validate_council(updated)
    return updated


def validate_evidence_graph(case: DecisionCase) -> None:
    node_ids: set[str] = set()
    for node in case.evidence_nodes:
        if not node.source_label.strip() or not node.observed_at.strip():
            raise DecisionTwinPolicyError(
                f"Evidence node {node.node_id} is missing source provenance"
            )
        if node.node_id in node_ids:
            raise DecisionTwinPolicyError("Evidence graph contains a duplicate node")
        node_ids.add(node.node_id)
    for edge in case.evidence_edges:
        if edge.source_id not in node_ids or edge.target_id not in node_ids:
            raise DecisionTwinPolicyError("Evidence edge references an unknown evidence node")
    if case.council.evidence_manifest_hash != _manifest_hash(case.evidence_nodes):
        raise DecisionTwinPolicyError("Council is not bound to the current evidence manifest")


def validate_council(case: DecisionCase) -> None:
    validate_evidence_graph(case)
    node_ids = {node.node_id for node in case.evidence_nodes}
    roles = [position.role for position in case.council.positions]
    required_roles = {"customer", "usage", "strategy", "feasibility", "challenger"}
    if set(roles) != required_roles or len(roles) != len(required_roles):
        raise DecisionTwinPolicyError(
            "Product council requires one customer, usage, strategy, feasibility, and challenger position"
        )
    if len({position.recommendation for position in case.council.positions}) < 2:
        raise DecisionTwinPolicyError("Product council must preserve material disagreement")
    for position in case.council.positions:
        citations = position.supporting_node_ids + position.contradicting_node_ids
        if any(node_id not in node_ids for node_id in citations):
            raise DecisionTwinPolicyError("Council cites an unknown evidence node")
    option_ids = [option.option_id for option in case.council.options]
    if option_ids != ["ship", "rollback", "segment", "defer"]:
        raise DecisionTwinPolicyError("Council must evaluate the bounded option set")
    for option in case.council.options:
        if any(node_id not in node_ids for node_id in option.evidence_node_ids):
            raise DecisionTwinPolicyError("Counterfactual cites an unknown evidence node")
        if not (
            option.guardrails
            and option.would_change_mind_if.strip()
            and option.rollback.strip()
            and option.reversible
        ):
            raise DecisionTwinPolicyError(
                "Every counterfactual must be falsifiable and reversible"
            )


def _named_human(approver: str) -> str:
    cleaned = approver.strip()
    if len(cleaned) < 2 or cleaned.casefold() in {
        "agent",
        "assistant",
        "system",
        "driftline",
        "model",
    }:
        raise DecisionTwinPolicyError("A named human approver is required")
    return cleaned


def _experiment_plan(option: CounterfactualOption) -> ExperimentPlan:
    contracts = {
        "ship": {
            "hypothesis": "A global rollout preserves small-team gains without deepening the enterprise activation regression.",
            "target": "all_workspaces",
            "metric": "blended_activation_rate",
            "success": "Small-team activation remains positive and enterprise activation does not decline beyond the launch guardrail.",
            "stops": [
                "Stop if enterprise activation declines another 3% relative to the observed baseline.",
                "Stop if support volume for permissions increases during rollout.",
            ],
            "actions": [
                "Create the all-workspace rollout allocation.",
                "Instrument activation and permission-support volume by segment.",
                "Keep the prior onboarding flow ready for immediate restoration.",
                "Review both segment outcomes at the measurement deadline.",
            ],
        },
        "rollback": {
            "hypothesis": "Restoring the prior flow recovers enterprise activation without erasing the small-team learning.",
            "target": "all_workspaces",
            "metric": "blended_activation_rate",
            "success": "Enterprise activation returns toward baseline while the redesign remains available for a bounded follow-up test.",
            "stops": [
                "Stop if small-workspace activation falls below its prior baseline.",
                "Stop if the prior flow cannot be restored consistently across segments.",
            ],
            "actions": [
                "Restore the prior onboarding flow for all workspaces.",
                "Preserve the redesigned flow behind the existing segment gate.",
                "Instrument activation by workspace segment.",
                "Review the rollback outcome at the measurement deadline.",
            ],
        },
        "segment": {
            "hypothesis": "A permission preview recovers enterprise activation while the redesigned flow preserves the small-team gain.",
            "target": "enterprise_workspaces",
            "metric": "enterprise_activation_rate",
            "success": "Recover at least half of the observed enterprise activation regression within the review window.",
            "stops": [
                "Stop if enterprise activation declines to 12% or more below baseline.",
                "Stop if setup completion declines in either allocated segment.",
            ],
            "actions": [
                "Create the enterprise-only experiment allocation.",
                "Add permission-policy preview copy before role selection.",
                "Instrument activation and setup completion by workspace segment.",
                "Review the decision when the measurement window closes.",
            ],
        },
        "defer": {
            "hypothesis": "Additional enterprise evidence resolves the permission-step causal uncertainty before a rollout decision.",
            "target": "enterprise_workspaces",
            "metric": "qualified_enterprise_evidence_count",
            "success": "Two additional independent enterprise sources support or reject the permission-step hypothesis within seven days.",
            "stops": [
                "Stop the deferral after seven days and return to the human decision gate.",
                "Stop if enterprise activation deteriorates while evidence collection is pending.",
            ],
            "actions": [
                "Schedule two additional enterprise evidence sessions.",
                "Collect one fresh segmented activation observation.",
                "Keep the current segment allocation unchanged.",
                "Reopen the decision when the evidence deadline arrives.",
            ],
        },
    }
    contract = contracts[option.option_id]
    return ExperimentPlan(
        plan_id=f"experiment-{option.option_id}-onboarding",
        option_id=option.option_id,
        hypothesis=contract["hypothesis"],
        target_segment=contract["target"],
        primary_metric=contract["metric"],
        success_condition=contract["success"],
        guardrails=option.guardrails,
        stop_conditions=contract["stops"],
        review_at="2026-08-30T18:00:00+00:00",
        owner_actions=contract["actions"],
        rollback=option.rollback,
    )


def approve_decision_case(
    case: DecisionCase,
    *,
    option_id: DecisionOptionId,
    approver: str,
    expected_synthesis_hash: str,
    expected_generation: int,
) -> DecisionCase:
    validate_council(case)
    if case.status not in {"needs_approval", "reopened"}:
        raise DecisionTwinPolicyError("Decision case is not waiting for approval")
    if expected_generation != case.generation:
        raise DecisionTwinPolicyError("Approval references a stale decision generation")
    if expected_synthesis_hash != case.council.synthesis_hash:
        raise DecisionTwinPolicyError("Approval references a stale synthesis")
    try:
        option = next(
            item for item in case.council.options if item.option_id == option_id
        )
    except StopIteration as exc:
        raise DecisionTwinPolicyError("Approval references an unknown option") from exc
    approved = deepcopy(case)
    approved.approval = ApprovalRecord(
        approver=_named_human(approver),
        option_id=option_id,
        synthesis_hash=case.council.synthesis_hash,
        approved_at=datetime.now(UTC).isoformat(),
    )
    approved.experiment_plan = _experiment_plan(option)
    approved.status = "experiment_active"
    approved.reopen_reason = None
    approved.events.append(
        {
            "event_id": f"decision-approved-g{approved.generation}",
            "action": "human_decision_gate",
            "outcome": f"{option_id}_approved",
            "generation": approved.generation,
            "synthesis_hash": approved.council.synthesis_hash,
        }
    )
    return approved


def evaluate_outcome(
    case: DecisionCase, observation: OutcomeObservation | dict[str, Any]
) -> OutcomeEvaluation:
    outcome = (
        observation
        if isinstance(observation, OutcomeObservation)
        else OutcomeObservation.model_validate(observation)
    )
    if case.experiment_plan is None:
        raise DecisionTwinPolicyError("Outcome requires an approved experiment plan")
    if outcome.metric_id != case.experiment_plan.primary_metric:
        return OutcomeEvaluation(
            verdict="inconclusive",
            reason="Observation does not measure the approved primary metric.",
            reopen_required=False,
        )
    if outcome.segment != case.experiment_plan.target_segment:
        return OutcomeEvaluation(
            verdict="inconclusive",
            reason="Observation does not cover the approved target segment.",
            reopen_required=False,
        )
    relative_change = outcome.value - outcome.baseline
    if relative_change <= -0.12:
        return OutcomeEvaluation(
            verdict="invalidated",
            reason="Enterprise activation crossed the approved stop guardrail.",
            reopen_required=True,
        )
    if relative_change >= -0.055:
        return OutcomeEvaluation(
            verdict="validated",
            reason="Enterprise activation recovered at least half of the observed regression.",
            reopen_required=False,
        )
    return OutcomeEvaluation(
        verdict="inconclusive",
        reason="The outcome is inside the measurement window but does not resolve the hypothesis.",
        reopen_required=False,
    )


def record_outcome(
    case: DecisionCase,
    observation: OutcomeObservation | dict[str, Any],
    *,
    expected_generation: int,
) -> DecisionCase:
    if case.generation != expected_generation:
        raise DecisionTwinPolicyError("Outcome references a stale decision generation")
    outcome = (
        observation
        if isinstance(observation, OutcomeObservation)
        else OutcomeObservation.model_validate(observation)
    )
    if any(item.observation_id == outcome.observation_id for item in case.outcomes):
        return deepcopy(case)
    recorded = deepcopy(case)
    evaluation = evaluate_outcome(recorded, outcome)
    outcome.evaluation = evaluation
    recorded.outcomes.append(outcome)
    recorded.events.append(
        {
            "event_id": f"{outcome.observation_id}-evaluated",
            "action": "outcome_evaluator",
            "outcome": evaluation.verdict,
            "generation": recorded.generation,
            "content_hash": outcome.content_hash,
        }
    )
    if evaluation.reopen_required:
        if recorded.approval is None:
            raise DecisionTwinPolicyError("Reopening requires a prior human decision")
        recorded.decision_history.append(
            DecisionHistoryRecord(
                generation=recorded.generation,
                option_id=recorded.approval.option_id,
                approver=recorded.approval.approver,
                synthesis_hash=recorded.approval.synthesis_hash,
                outcome_verdict=evaluation.verdict,
                approval=recorded.approval.model_copy(deep=True),
                experiment_plan=recorded.experiment_plan.model_copy(deep=True),
                trigger_observation=outcome.model_copy(deep=True),
                reopen_reason=evaluation.reason,
            )
        )
        recorded.generation += 1
        recorded.status = "reopened"
        recorded.reopen_reason = evaluation.reason
        recorded.approval = None
        recorded.experiment_plan = None
        recorded.events.append(
            {
                "event_id": f"decision-reopened-g{recorded.generation}",
                "action": "decision_debt_detector",
                "outcome": "human_review_reopened",
                "generation": recorded.generation,
                "trigger_observation_id": outcome.observation_id,
            }
        )
    elif evaluation.verdict == "validated":
        recorded.status = "validated"
    elif evaluation.verdict == "inconclusive":
        recorded.status = "inconclusive"
    return recorded
