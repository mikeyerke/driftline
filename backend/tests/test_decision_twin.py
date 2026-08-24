from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app import product_council
from app.decision_twin import (
    CouncilPosition,
    DecisionTwinPolicyError,
    approve_decision_case,
    attach_aggregate_metrics,
    build_demo_decision_case,
    evaluate_outcome,
    record_outcome,
    validate_council,
    validate_evidence_graph,
)
from app.product_council import (
    COUNCIL_ROLES,
    build_council_agents,
    build_council_prompt,
    deterministic_council,
)
from app.trace_eval import evaluate_decision_twin_case


def test_demo_case_is_complete_grounded_and_preserves_real_disagreement() -> None:
    case = build_demo_decision_case()

    validate_evidence_graph(case)
    validate_council(case)

    assert case.status == "needs_approval"
    assert case.generation == 1
    assert len(case.evidence_nodes) == 5
    assert {position.role for position in case.council.positions} == {
        "customer",
        "usage",
        "strategy",
        "feasibility",
        "challenger",
    }
    assert len({position.recommendation for position in case.council.positions}) > 1
    assert case.council.recommendation == "segment"
    assert case.council.decisive_conflict
    assert case.council.synthesis_hash


def test_evidence_graph_rejects_missing_provenance_and_unknown_edges() -> None:
    case = build_demo_decision_case()
    broken = deepcopy(case)
    broken.evidence_nodes[0].source_label = ""
    with pytest.raises(DecisionTwinPolicyError, match="source provenance"):
        validate_evidence_graph(broken)

    broken = deepcopy(case)
    broken.evidence_edges[0].target_id = "missing-node"
    with pytest.raises(DecisionTwinPolicyError, match="unknown evidence node"):
        validate_evidence_graph(broken)


def test_council_rejects_missing_challenger_and_unsupported_citations() -> None:
    case = build_demo_decision_case()
    broken = deepcopy(case)
    broken.council.positions = [
        position for position in broken.council.positions if position.role != "challenger"
    ]
    with pytest.raises(DecisionTwinPolicyError, match="challenger"):
        validate_council(broken)

    broken = deepcopy(case)
    broken.council.positions[0].supporting_node_ids = ["invented-evidence"]
    with pytest.raises(DecisionTwinPolicyError, match="unknown evidence node"):
        validate_council(broken)


def test_counterfactuals_are_bounded_and_falsifiable() -> None:
    case = build_demo_decision_case()

    assert [option.option_id for option in case.council.options] == [
        "ship",
        "rollback",
        "segment",
        "defer",
    ]
    assert all(option.guardrails for option in case.council.options)
    assert all(option.would_change_mind_if for option in case.council.options)
    assert all(option.rollback for option in case.council.options)
    assert all(option.evidence_node_ids for option in case.council.options)


def test_approval_requires_current_synthesis_named_human_and_complete_plan() -> None:
    case = build_demo_decision_case()

    with pytest.raises(DecisionTwinPolicyError, match="stale synthesis"):
        approve_decision_case(
            case,
            option_id="segment",
            approver="Mike Yerke",
            expected_synthesis_hash="0" * 64,
            expected_generation=1,
        )
    with pytest.raises(DecisionTwinPolicyError, match="named human"):
        approve_decision_case(
            case,
            option_id="segment",
            approver="agent",
            expected_synthesis_hash=case.council.synthesis_hash,
            expected_generation=1,
        )

    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
        expected_generation=1,
    )
    assert approved.status == "experiment_active"
    assert approved.approval.approver == "Mike Yerke"
    assert approved.experiment_plan.option_id == "segment"
    assert approved.experiment_plan.stop_conditions
    assert approved.experiment_plan.rollback
    assert datetime.fromisoformat(approved.approval.approved_at) <= datetime.now(UTC)


def test_each_approval_option_builds_its_own_experiment_contract() -> None:
    case = build_demo_decision_case()
    plans = {
        option.option_id: approve_decision_case(
            case,
            option_id=option.option_id,
            approver="Mike Yerke",
            expected_synthesis_hash=case.council.synthesis_hash,
            expected_generation=1,
        ).experiment_plan
        for option in case.council.options
    }

    assert len({plan.primary_metric for plan in plans.values()}) == 3
    assert len({tuple(plan.owner_actions) for plan in plans.values()}) == 4
    assert plans["segment"].target_segment == "enterprise_workspaces"
    assert plans["defer"].primary_metric == "qualified_enterprise_evidence_count"


def test_approval_rejects_stale_generation_even_when_synthesis_matches() -> None:
    case = build_demo_decision_case()
    case.generation = 2

    with pytest.raises(DecisionTwinPolicyError, match="stale decision generation"):
        approve_decision_case(
            case,
            option_id="segment",
            approver="Mike Yerke",
            expected_synthesis_hash=case.council.synthesis_hash,
            expected_generation=1,
        )


def test_invalidated_outcome_reopens_same_case_with_preserved_lineage() -> None:
    case = build_demo_decision_case()
    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
        expected_generation=1,
    )

    observation = {
        "observation_id": "outcome-enterprise-activation",
        "metric_id": "enterprise_activation_rate",
        "segment": "enterprise_workspaces",
        "value": -0.14,
        "baseline": 0.0,
        "unit": "relative_change",
        "observed_at": "2026-08-30T18:00:00+00:00",
        "source_label": "BigQuery aggregate fixture",
        "content_hash": "a" * 64,
    }
    assert evaluate_outcome(approved, observation).verdict == "invalidated"

    reopened = record_outcome(
        approved,
        observation,
        expected_generation=1,
    )
    assert reopened.case_id == approved.case_id
    assert reopened.generation == 2
    assert reopened.status == "reopened"
    assert reopened.reopen_reason == "Enterprise activation crossed the approved stop guardrail."
    assert reopened.decision_history[0].generation == 1
    assert reopened.decision_history[0].option_id == "segment"
    assert reopened.decision_history[0].approval == approved.approval
    assert reopened.decision_history[0].experiment_plan == approved.experiment_plan
    assert reopened.decision_history[0].trigger_observation.observation_id == (
        observation["observation_id"]
    )
    assert reopened.outcomes[-1].evaluation.verdict == "invalidated"

    with pytest.raises(DecisionTwinPolicyError, match="stale decision generation"):
        record_outcome(reopened, observation, expected_generation=1)


def test_successful_outcome_validates_and_duplicate_is_idempotent() -> None:
    case = build_demo_decision_case()
    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
        expected_generation=1,
    )
    observation = {
        "observation_id": "outcome-enterprise-activation-safe",
        "metric_id": "enterprise_activation_rate",
        "segment": "enterprise_workspaces",
        "value": -0.02,
        "baseline": 0.0,
        "unit": "relative_change",
        "observed_at": "2026-08-30T18:00:00+00:00",
        "source_label": "BigQuery aggregate fixture",
        "content_hash": "b" * 64,
    }
    active = record_outcome(approved, observation, expected_generation=1)
    duplicate = record_outcome(active, observation, expected_generation=1)

    assert active.status == "validated"
    assert len(active.outcomes) == 1
    assert duplicate.model_dump() == active.model_dump()


def test_outcome_thresholds_leave_a_reachable_inconclusive_range() -> None:
    case = build_demo_decision_case()
    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
        expected_generation=1,
    )
    observation = {
        "observation_id": "outcome-enterprise-inconclusive",
        "metric_id": "enterprise_activation_rate",
        "segment": "enterprise_workspaces",
        "value": -0.08,
        "baseline": 0.0,
        "unit": "relative_change",
        "observed_at": "2026-08-30T18:00:00+00:00",
        "source_label": "BigQuery aggregate fixture",
        "content_hash": "c" * 64,
    }

    assert evaluate_outcome(approved, observation).verdict == "inconclusive"


def test_combined_metric_hash_and_freshness_bind_both_segment_timestamps() -> None:
    case = build_demo_decision_case()
    small = SimpleNamespace(
        metric_id="activation_rate",
        segment="small_workspaces",
        value=0.09,
        sample_size=42,
        observed_at="2026-08-22T18:00:00+00:00",
    )
    enterprise = SimpleNamespace(
        metric_id="activation_rate",
        segment="enterprise_workspaces",
        value=-0.11,
        sample_size=42,
        observed_at="2026-08-23T18:00:00+00:00",
    )
    first = attach_aggregate_metrics(case, [small, enterprise])
    small.observed_at = "2026-08-23T18:00:00+00:00"
    second = attach_aggregate_metrics(case, [small, enterprise])
    first_node = next(n for n in first.evidence_nodes if n.node_id == "metric-activation-split")
    second_node = next(n for n in second.evidence_nodes if n.node_id == "metric-activation-split")

    assert first_node.observed_at == "2026-08-22T18:00:00+00:00"
    assert first_node.content_hash != second_node.content_hash
    assert first.council.synthesis_hash != second.council.synthesis_hash


def test_product_council_agents_have_only_adk_task_completion_tool() -> None:
    agents = build_council_agents()

    assert set(agents) == set(COUNCIL_ROLES)
    assert len({agent.name for agent in agents.values()}) == 5
    # ADK task-mode injects its internal FinishTaskTool. No connector, approval,
    # publishing, or arbitrary function tool is available to a specialist.
    assert all(
        [tool.__class__.__name__ for tool in agent.tools] == ["FinishTaskTool"]
        for agent in agents.values()
    )
    assert all(agent.mode == "task" for agent in agents.values())
    assert all(agent.output_schema is CouncilPosition for agent in agents.values())
    assert all(agent.model == "gemini-3.5-flash" for agent in agents.values())


@pytest.mark.asyncio
async def test_run_json_reads_structured_task_output_from_terminal_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "role": "usage",
        "recommendation": "segment",
        "thesis": "Segment movement conflicts.",
        "supporting_node_ids": ["metric-activation-split"],
        "contradicting_node_ids": [],
        "risks": ["Aggregate data is not causal."],
        "would_change_mind_if": "The segment gap disappears.",
    }

    class FakeRunner:
        def __init__(self, **_: object) -> None:
            pass

        async def run_async(self, **_: object):
            yield SimpleNamespace(
                output=payload,
                content=None,
                is_final_response=lambda: False,
            )

    monkeypatch.setattr(product_council, "Runner", FakeRunner)

    result = await product_council._run_json(
        build_council_agents()["usage"], "{}"
    )

    assert json.loads(result) == payload


@pytest.mark.asyncio
async def test_live_council_translates_provider_failures_to_bounded_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unavailable(_case):
        raise RuntimeError("provider detail that must not escape")

    monkeypatch.setattr(product_council, "_run_live_product_council", unavailable)

    with pytest.raises(
        product_council.ProductCouncilUnavailable,
        match="Google ADK council runtime unavailable",
    ) as captured:
        await product_council.run_live_product_council(build_demo_decision_case())
    assert "provider detail" not in str(captured.value)


def test_product_council_prompt_contains_bounded_projections_not_secrets() -> None:
    case = build_demo_decision_case()
    prompt = build_council_prompt(case, "challenger")

    assert "support-permission-confusion" in prompt
    assert "BigQuery aggregate fixture" in prompt
    assert "challenger" in prompt
    assert "access_token" not in prompt
    assert "credential" not in prompt.casefold()


def test_product_council_prompts_encode_distinct_decision_mandates() -> None:
    case = build_demo_decision_case()
    prompts = {
        role: json.loads(build_council_prompt(case, role)) for role in COUNCIL_ROLES
    }

    assert all(prompt["assigned_role"] == role for role, prompt in prompts.items())
    assert len({prompt["decision_mandate"] for prompt in prompts.values()}) == 5
    assert prompts["customer"]["evaluation_prior"] == "protect_user_trust"
    assert prompts["usage"]["evaluation_prior"] == "trust_segment_measurement"
    assert prompts["strategy"]["evaluation_prior"] == "honor_current_commitment"
    assert prompts["feasibility"]["evaluation_prior"] == "prefer_safe_execution"
    assert prompts["challenger"]["evaluation_prior"] == "seek_credible_minority_case"


def test_deterministic_council_is_explicitly_labeled_and_policy_valid() -> None:
    case = build_demo_decision_case()
    council = deterministic_council(case)

    assert council.mode == "deterministic_demo_fallback"
    assert council.evidence_manifest_hash == case.council.evidence_manifest_hash
    case.council = council
    validate_council(case)


def test_decision_twin_trace_eval_scores_grounding_disagreement_and_falsifiability() -> None:
    case = build_demo_decision_case()
    report = evaluate_decision_twin_case(case)

    assert report["gate_status"] == "pass"
    assert report["overall_score"] == 1.0
    assert report["suite_version"] == "decision-twin-eval-v1"
    assert {item["case_id"] for item in report["cases"]} == {
        "evidence_provenance",
        "council_roles",
        "disagreement_preserved",
        "citation_coverage",
        "falsifiability",
        "human_authority",
        "reopening_lineage",
    }
