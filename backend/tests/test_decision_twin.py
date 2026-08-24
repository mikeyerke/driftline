from __future__ import annotations

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app import product_council
from app.decision_twin import (
    CouncilPosition,
    DecisionTwinPolicyError,
    approve_decision_case,
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
        )
    with pytest.raises(DecisionTwinPolicyError, match="named human"):
        approve_decision_case(
            case,
            option_id="segment",
            approver="agent",
            expected_synthesis_hash=case.council.synthesis_hash,
        )

    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
    )
    assert approved.status == "experiment_active"
    assert approved.approval.approver == "Mike Yerke"
    assert approved.experiment_plan.option_id == "segment"
    assert approved.experiment_plan.stop_conditions
    assert approved.experiment_plan.rollback


def test_invalidated_outcome_reopens_same_case_with_preserved_lineage() -> None:
    case = build_demo_decision_case()
    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
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


def test_product_council_prompt_contains_bounded_projections_not_secrets() -> None:
    case = build_demo_decision_case()
    prompt = build_council_prompt(case, "challenger")

    assert "support-permission-confusion" in prompt
    assert "BigQuery aggregate fixture" in prompt
    assert "challenger" in prompt
    assert "access_token" not in prompt
    assert "credential" not in prompt.casefold()


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
