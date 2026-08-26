from types import SimpleNamespace

from app.decision_twin import (
    PMMeasurementContract,
    approve_decision_case,
    attach_aggregate_metrics,
    build_demo_decision_case,
    build_intake_decision_case,
    record_outcome,
)


def _measurement_contract() -> PMMeasurementContract:
    return PMMeasurementContract(
        primary_metric="Activation rate",
        risk_metric="Support escalation rate",
        metric_unit="percent",
        baseline=0.42,
        success_operator="gte",
        success_threshold=0.48,
        risk_baseline=0.05,
        stop_operator="gte",
        stop_threshold=0.09,
        review_days=7,
        action_owner="Mike Yerke",
    )


def _approved_demo():
    case = build_demo_decision_case()
    return approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
        expected_generation=case.generation,
    )


def test_initial_loop_exposes_all_seven_capabilities_without_claiming_customer_truth() -> None:
    case = build_demo_decision_case()
    loop = case.operating_loop

    assert loop is not None
    assert loop.stage == "human_approval"
    assert loop.evidence_harvest.source_count == 6
    assert loop.evidence_harvest.status == "ready"
    assert {
        source.mode for source in loop.evidence_harvest.sources
    } == {"pinned_demo_evidence", "bounded_precedent"}
    assert loop.stakeholder_alignment.status == "unresolved_tradeoff"
    assert loop.stakeholder_alignment.dissent_preserved is True
    assert loop.stakeholder_alignment.apparent_consensus_risk is False
    assert len(loop.stakeholder_alignment.positions) == 5
    assert "not fabricated quotes" in loop.stakeholder_alignment.disclosure
    assert loop.execution_contract.status == "awaiting_approval"
    assert loop.execution_contract.external_writes is False
    assert loop.outcome_autopilot.status == "awaiting_approval"
    assert loop.compounding_memory.cycle_count == 0
    assert loop.compounding_memory.insights[-1].sample_size == 0
    assert "cannot claim decision accuracy" in loop.compounding_memory.insights[-1].statement


def test_ten_step_journey_advances_only_when_durable_state_exists() -> None:
    case = build_demo_decision_case()
    assert [item.state for item in case.operating_loop.journey] == [
        "done",
        "done",
        "done",
        "done",
        "done",
        "done",
        "active",
        "waiting",
        "waiting",
        "waiting",
    ]

    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Mike Yerke",
        expected_synthesis_hash=case.council.synthesis_hash,
        expected_generation=1,
    )
    assert approved.operating_loop.stage == "execution"
    assert approved.operating_loop.execution_contract.status == "active"
    assert approved.operating_loop.execution_contract.owner == "Mike Yerke"
    assert approved.operating_loop.outcome_autopilot.status == "scheduled"
    assert [item.state for item in approved.operating_loop.journey][6:] == [
        "done",
        "done",
        "active",
        "waiting",
    ]

    reopened = record_outcome(
        approved,
        {
            "observation_id": "operating-loop-guardrail-breach",
            "metric_id": "enterprise_activation_rate",
            "segment": "enterprise_workspaces",
            "value": -0.14,
            "baseline": 0.0,
            "unit": "relative_change",
            "observed_at": "2026-08-30T18:00:00+00:00",
            "source_label": "Bounded outcome fixture",
            "content_hash": "9" * 64,
        },
        expected_generation=1,
    )
    assert reopened.status == "reopened"
    assert reopened.operating_loop.stage == "learning"
    assert reopened.operating_loop.execution_contract.status == "rolled_back"
    assert reopened.operating_loop.outcome_autopilot.status == "reopened"
    assert reopened.operating_loop.compounding_memory.cycle_count == 1
    assert reopened.operating_loop.compounding_memory.insights[-1].sample_size == 1
    assert all(item.state == "done" for item in reopened.operating_loop.journey)


def test_pm_intake_remains_verification_gated_and_names_missing_channels() -> None:
    case = build_intake_decision_case(
        case_id="decision-intake-operating-loop",
        question="Should we expand the beta to all enterprise workspaces?",
        current_commitment="Expand the beta to all enterprise workspaces next Friday.",
        urgency="The launch review is in seven days.",
        positive_signal="Two beta customers completed setup faster.",
        risk_signal="One admin reported a role-permission regression.",
        affected_segment="Enterprise administrators",
        measurement_contract=_measurement_contract(),
    )

    harvest = case.operating_loop.evidence_harvest
    assert harvest.status == "verification_required"
    assert {source.mode for source in harvest.sources} == {"pm_provided_unverified"}
    assert "product_analytics" in harvest.missing_channels
    assert "product_surface" in harvest.missing_channels
    assert "remains unverified" in harvest.disclosure


def test_connected_aggregate_is_distinguished_from_replayable_evidence() -> None:
    case = build_demo_decision_case()
    connected = attach_aggregate_metrics(
        case,
        [
            SimpleNamespace(
                metric_id="activation_rate",
                segment="small_workspaces",
                value=0.09,
                sample_size=80,
                observed_at="2026-08-26T10:00:00+00:00",
            ),
            SimpleNamespace(
                metric_id="activation_rate",
                segment="enterprise_workspaces",
                value=-0.11,
                sample_size=64,
                observed_at="2026-08-26T10:00:00+00:00",
            ),
        ],
    )

    analytics = next(
        source
        for source in connected.operating_loop.evidence_harvest.sources
        if source.channel == "product_analytics"
    )
    assert analytics.mode == "connected_observed"
    assert analytics.status == "changed"
    assert analytics.confidence > 0.9
