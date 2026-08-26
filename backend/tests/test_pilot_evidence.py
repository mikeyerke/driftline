from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from app.decision_twin import (
    PMMeasurementContract,
    build_demo_decision_case,
    build_intake_decision_case,
)
from app.pilot_evidence import PilotEvidenceError, build_pilot_evidence_starter


def intake_case():
    return build_intake_decision_case(
        case_id="decision-intake-private-example",
        question="Should we expand the beta to all mid-market accounts next month?",
        current_commitment="Launch to every mid-market account on September 15.",
        urgency="Sales committed the date and allocation is due this Friday.",
        positive_signal="Beta users complete the core workflow faster than the control group.",
        risk_signal="Admins report permission confusion and support volume is rising.",
        measurement_contract=PMMeasurementContract(
            primary_metric="workflow completion rate",
            risk_metric="failed workflow rate",
            metric_unit="%",
            baseline=38,
            success_operator="gte",
            success_threshold=45,
            risk_baseline=3,
            stop_operator="gte",
            stop_threshold=8,
            review_days=7,
            action_owner="Taylor PM",
        ),
        affected_segment="mid-market admins",
    )


def test_starter_binds_product_evidence_without_raw_pm_context() -> None:
    case = intake_case()
    starter = build_pilot_evidence_starter(
        case,
        release_sha="a" * 40,
        verified_production=True,
        generated_at=datetime(2026, 8, 26, 18, 0, tzinfo=UTC),
    )

    assert starter["record"]["app_state"] == "verified_production"
    assert starter["record"]["evidence_input_count"] == 2
    assert starter["record"]["plausible_option_count"] == 4
    assert starter["record"]["review_window_days"] == 7
    assert starter["record"]["participant_role"] is None
    assert starter["evidence_binding"]["release_sha"] == "a" * 40
    assert starter["evidence_binding"]["external_writes_none"] is True
    serialized = json.dumps(starter)
    for private_value in (
        case.case_id,
        case.question,
        case.current_commitment,
        case.urgency,
        case.evidence_nodes[1].excerpt,
    ):
        assert private_value not in serialized


def test_starter_rejects_demo_case_and_unknown_release() -> None:
    with pytest.raises(PilotEvidenceError, match="PM-provided decision"):
        build_pilot_evidence_starter(
            build_demo_decision_case(),
            release_sha="a" * 40,
            verified_production=False,
        )
    with pytest.raises(PilotEvidenceError, match="exact release SHA"):
        build_pilot_evidence_starter(
            intake_case(),
            release_sha="unknown",
            verified_production=False,
        )
