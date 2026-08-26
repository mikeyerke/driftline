import hashlib
import hmac
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

from app import api, persistence, source
from app.api import app
from app.connectors import (
    ConnectorError,
    SalesforceReauthorizationRequired,
    _tenant_secret_or_env,
)
from app.decision_copilot import fallback_copilot, red_team_review
from app.models import JobState, SourceEvidence, WorkflowState
from app.tenant import principal_for_hmac, tenant_operator_signing_secret_name

client = TestClient(app)


def _pm_measurement_contract_payload() -> dict:
    return {
        "primary_metric": "workflow completion rate",
        "risk_metric": "failed workflow rate",
        "metric_unit": "%",
        "baseline": 38,
        "success_operator": "gte",
        "success_threshold": 45,
        "risk_baseline": 3,
        "stop_operator": "gte",
        "stop_threshold": 8,
        "review_days": 7,
        "action_owner": "Taylor PM",
    }


def _open_pm_measurement_window(case_id: str) -> None:
    case = persistence.load_decision_case(case_id)
    assert case is not None
    assert case.experiment_plan is not None
    case.experiment_plan.review_at = "2000-01-01T00:00:00+00:00"
    persistence.persist_decision_case(case)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["release_sha"] == "unknown"
    assert response.json()["build_id"] == "unknown"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["permissions-policy"] == (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    )


def test_health_exposes_non_secret_release_identity(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_RELEASE_SHA", "a" * 40)
    monkeypatch.setenv("DRIFTLINE_BUILD_ID", "build-123")
    payload = client.get("/health").json()
    assert payload["release_sha"] == "a" * 40
    assert payload["build_id"] == "build-123"


def test_decision_inbox_projects_observed_workflows_without_external_writes(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    api.workflow_store._runs.clear()
    try:
        assert client.post(
            "/api/workflows/demo?source_id=competitor/pricing"
        ).status_code == 200
        assert client.post(
            "/api/workflows/demo?source_id=competitor/pricing"
        ).status_code == 200
        assert client.post(
            "/api/workflows/demo?source_id=competitor/offerings"
        ).status_code == 200

        response = client.get("/api/ops/decision-inbox")
        assert response.status_code == 200
        payload = response.json()
        assert payload["summary"]["decision_threads"] == 2
        assert payload["summary"]["duplicate_observations_collapsed"] == 1
        assert payload["counts"]["needs_decision"] == 2
        assert payload["automation_boundary"]["external_writes"] is False
    finally:
        api.workflow_store._runs.clear()


def test_decision_twin_demo_runs_complete_approval_and_reopening_loop(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()

    created = client.post("/api/decision-twin/demo")
    assert created.status_code == 200
    case = created.json()
    assert case["status"] == "needs_approval"
    assert case["council"]["mode"] == "deterministic_demo_fallback"
    assert len(case["council"]["positions"]) == 5

    approved = client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Demo Product Manager",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "experiment_active"
    assert approved.json()["experiment_plan"]["reversible"] is True
    assert approved.json()["action_records"][0]["status"] == "active"
    assert approved.json()["action_records"][0]["external_write"] is False

    reopened = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/demo",
        json={"expected_generation": 1, "scenario": "guardrail_breach"},
    )
    assert reopened.status_code == 200
    payload = reopened.json()
    assert payload["status"] == "reopened"
    assert payload["generation"] == 2
    assert payload["decision_history"][0]["option_id"] == "segment"
    assert payload["outcomes"][0]["evaluation"]["verdict"] == "invalidated"
    assert payload["action_records"][0]["status"] == "rolled_back"

    restored = client.get(f"/api/decision-twin/{case['case_id']}")
    assert restored.status_code == 200
    assert restored.json() == payload


def test_shared_decision_link_is_read_only_and_owner_cookie_is_case_bound(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    owner = TestClient(app)
    shared_viewer = TestClient(app)

    created_response = owner.post("/api/decision-twin/demo")
    case = created_response.json()
    cookie_header = created_response.headers["set-cookie"]
    assert "HttpOnly" in cookie_header
    assert "SameSite=strict" in cookie_header
    assert f"Path=/api/decision-twin/{case['case_id']}" in cookie_header
    assert "mutation_capability" not in str(case)
    stored = persistence._decision_cases_memory[case["case_id"]]
    assert "_mutation_capability_hash" in stored
    assert api.DECISION_MUTATION_COOKIE_PREFIX not in str(stored)

    shared = shared_viewer.get(f"/api/decision-twin/{case['case_id']}")
    assert shared.status_code == 200
    assert shared.json()["can_edit"] is False
    assert "mutation_capability_hash" not in shared.json()
    denied = shared_viewer.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Link Recipient",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "This shared decision link is read-only."

    owner_view = owner.get(f"/api/decision-twin/{case['case_id']}")
    assert owner_view.status_code == 200
    assert owner_view.json()["can_edit"] is True
    approved = owner.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Owner PM",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    assert approved.status_code == 200


def test_decision_mutation_cookie_cannot_edit_another_case(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    first_owner = TestClient(app)
    second_owner = TestClient(app)
    first = first_owner.post("/api/decision-twin/demo").json()
    second = second_owner.post("/api/decision-twin/demo").json()

    denied = second_owner.post(
        f"/api/decision-twin/{first['case_id']}/approve",
        json={
            "approver": "Wrong Case Owner",
            "option_id": "segment",
            "expected_synthesis_hash": first["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    assert denied.status_code == 403
    assert second_owner.get(
        f"/api/decision-twin/{second['case_id']}"
    ).json()["can_edit"] is True


def test_one_browser_retains_edit_authority_for_multiple_decisions(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    owner = TestClient(app)
    first = owner.post("/api/decision-twin/demo").json()
    second = owner.post("/api/decision-twin/demo").json()

    assert owner.get(f"/api/decision-twin/{first['case_id']}").json()[
        "can_edit"
    ] is True
    assert owner.get(f"/api/decision-twin/{second['case_id']}").json()[
        "can_edit"
    ] is True


def test_decision_twin_intake_builds_an_honestly_labelled_pm_case(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()

    response = client.post(
        "/api/decision-twin/intake",
        json={
            "question": "Should we expand the beta to all mid-market accounts next month?",
            "current_commitment": "Launch to every mid-market account on September 15.",
            "urgency": "Sales committed the date and allocation is due this Friday.",
            "positive_signal": "Beta users complete the core workflow faster than the control group.",
            "risk_signal": "Admins report permission confusion and support volume is rising.",
            "affected_segment": "mid-market admins",
            "measurement_contract": _pm_measurement_contract_payload(),
        },
    )

    assert response.status_code == 200
    case = response.json()
    assert case["case_id"].startswith("decision-intake-")
    assert case["title"] == "Mid-market admins decision review"
    assert case["title"] != case["question"].rstrip(" ?.")
    assert case["status"] == "needs_approval"
    assert case["council"]["mode"] == "deterministic_demo_fallback"
    assert {node["source_label"] for node in case["evidence_nodes"]} == {
        "PM-provided context · unverified"
    }
    assert any(
        event.get("source_mode") == "pm_provided_unverified"
        for event in case["events"]
    )
    assert client.get(f"/api/decision-twin/{case['case_id']}").json() == case


def test_private_pilot_starter_is_product_bound_and_owner_only(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DRIFTLINE_RELEASE_SHA", "a" * 40)
    monkeypatch.setenv("K_SERVICE", "driftline")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    owner = TestClient(app, base_url="https://testserver")
    shared_viewer = TestClient(app, base_url="https://testserver")
    decision_text = "Should we expand the beta to all mid-market accounts next month?"
    commitment_text = "Launch to every mid-market account on September 15."
    created = owner.post(
        "/api/decision-twin/intake",
        json={
            "question": decision_text,
            "current_commitment": commitment_text,
            "urgency": "Sales committed the date and allocation is due this Friday.",
            "positive_signal": "Beta users complete the core workflow faster than the control group.",
            "risk_signal": "Admins report permission confusion and support volume is rising.",
            "affected_segment": "mid-market admins",
            "measurement_contract": _pm_measurement_contract_payload(),
        },
    ).json()

    cited_node_ids = created["council"]["evidence_node_ids"]
    denied_review = shared_viewer.post(
        f"/api/decision-twin/{created['case_id']}/evidence/{cited_node_ids[0]}/review",
        json={"expected_generation": 1},
    )
    assert denied_review.status_code == 403
    for node_id in cited_node_ids:
        reviewed = owner.post(
            f"/api/decision-twin/{created['case_id']}/evidence/{node_id}/review",
            json={"expected_generation": 1},
        )
        assert reviewed.status_code == 200
    duplicate = owner.post(
        f"/api/decision-twin/{created['case_id']}/evidence/{cited_node_ids[0]}/review",
        json={"expected_generation": 1},
    )
    assert duplicate.status_code == 200
    assert len(duplicate.json()["evidence_reviews"]) == len(cited_node_ids)
    stale = owner.post(
        f"/api/decision-twin/{created['case_id']}/evidence/{cited_node_ids[0]}/review",
        json={"expected_generation": 2},
    )
    assert stale.status_code == 409
    assert "stale generation" in stale.json()["detail"]

    response = owner.get(
        f"/api/decision-twin/{created['case_id']}/pilot-evidence-starter"
    )
    assert response.status_code == 200
    assert "no-store" in response.headers["cache-control"]
    starter = response.json()
    assert starter["record"]["app_release_sha"] == "a" * 40
    assert starter["record"]["app_state"] == "verified_production"
    assert starter["record"]["participant_role"] is None
    assert starter["record"]["all_citations_reviewed"] is True
    assert isinstance(starter["record"]["minutes_to_brief"], (int, float))
    assert starter["record"]["minutes_to_brief"] >= 0
    assert starter["evidence_binding"]["reviewed_evidence_count"] == len(
        cited_node_ids
    )
    assert starter["evidence_binding"]["all_citations_reviewed"] is True
    assert starter["evidence_binding"]["minutes_to_reviewed_brief"] == starter[
        "record"
    ]["minutes_to_brief"]
    assert starter["evidence_binding"]["evidence_manifest_hash"] == created["council"][
        "evidence_manifest_hash"
    ]
    assert starter["evidence_binding"]["external_writes_none"] is True
    serialized = response.text
    assert created["case_id"] not in serialized
    assert decision_text not in serialized
    assert commitment_text not in serialized

    denied = shared_viewer.get(
        f"/api/decision-twin/{created['case_id']}/pilot-evidence-starter"
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "This shared decision link is read-only."


def test_pilot_starter_rejects_demo_case_and_unknown_release(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    owner = TestClient(app)
    demo = owner.post("/api/decision-twin/demo").json()

    monkeypatch.setenv("DRIFTLINE_RELEASE_SHA", "a" * 40)
    wrong_kind = owner.get(
        f"/api/decision-twin/{demo['case_id']}/pilot-evidence-starter"
    )
    assert wrong_kind.status_code == 409
    assert "PM-provided decision" in wrong_kind.json()["detail"]

    monkeypatch.setenv("DRIFTLINE_RELEASE_SHA", "unknown")
    missing_identity = owner.get(
        f"/api/decision-twin/{demo['case_id']}/pilot-evidence-starter"
    )
    assert missing_identity.status_code == 503
    assert "no pilot starter was generated" in missing_identity.json()["detail"]


def test_decision_twin_intake_rejects_extra_or_underspecified_context(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    payload = {
        "question": "Should we expand the beta to all mid-market accounts next month?",
        "current_commitment": "Launch to every mid-market account on September 15.",
        "urgency": "Sales committed the date and allocation is due this Friday.",
        "positive_signal": "too short",
        "risk_signal": "Admins report permission confusion and support volume is rising.",
        "measurement_contract": _pm_measurement_contract_payload(),
        "invented_connected_source": "salesforce",
    }

    response = client.post("/api/decision-twin/intake", json=payload)

    assert response.status_code == 422


def test_decision_twin_intake_accepts_four_redacted_sources_and_rejects_five(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    payload = {
        "question": "Should we expand the beta to all mid-market accounts next month?",
        "current_commitment": "Launch to every mid-market account on September 15.",
        "urgency": "Sales committed the date and allocation is due this Friday.",
        "positive_signal": "Beta users complete the core workflow faster than the control group.",
        "risk_signal": "Admins report permission confusion and support volume is rising.",
        "measurement_contract": _pm_measurement_contract_payload(),
        "evidence_inputs": [
            {
                "source_type": "metric",
                "source_label": f"Redacted source {index}",
                "title": f"Observation {index}",
                "observation": "A safely redacted observation with enough decision context.",
                "observed_on": f"2026-08-{20 + index:02d}",
                "stance": "supports" if index % 2 else "contradicts",
            }
            for index in range(1, 5)
        ],
    }

    accepted = client.post("/api/decision-twin/intake", json=payload)
    assert accepted.status_code == 200
    assert len(accepted.json()["evidence_nodes"]) == 7
    assert all(
        source["mode"] == "pm_provided_unverified"
        for source in accepted.json()["operating_loop"]["evidence_harvest"]["sources"]
    )

    payload["evidence_inputs"].append(payload["evidence_inputs"][0])
    rejected = client.post("/api/decision-twin/intake", json=payload)
    assert rejected.status_code == 422


def test_decision_twin_intake_requires_an_operating_contract(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    response = client.post(
        "/api/decision-twin/intake",
        json={
            "question": "Should we expand the beta to all mid-market accounts next month?",
            "current_commitment": "Launch to every mid-market account on September 15.",
            "urgency": "Sales committed the date and allocation is due this Friday.",
            "positive_signal": "Beta users complete the core workflow faster than the control group.",
            "risk_signal": "Admins report permission confusion and support volume is rising.",
            "affected_segment": "mid-market admins",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "measurement_contract"


def test_decision_twin_approval_enqueues_autonomous_monitor(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setenv("DRIFTLINE_TASKS_ENABLED", "true")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    queued: list[tuple[str, int]] = []
    monkeypatch.setattr(
        api,
        "_enqueue_decision_twin_monitor",
        lambda case_id, generation: queued.append((case_id, generation)),
    )
    persistence._decision_cases_memory.clear()

    case = client.post("/api/decision-twin/demo").json()
    approved = client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Demo Product Manager",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "experiment_active"
    assert approved.json()["monitor_status"] == "scheduled"
    assert queued == [(case["case_id"], 1)]


def test_decision_twin_approval_exposes_monitor_enqueue_failure(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setenv("DRIFTLINE_TASKS_ENABLED", "true")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)

    def fail_enqueue(_case_id: str, _generation: int) -> None:
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(api, "_enqueue_decision_twin_monitor", fail_enqueue)
    persistence._decision_cases_memory.clear()

    case = client.post("/api/decision-twin/demo").json()
    approved = client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Demo Product Manager",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "experiment_active"
    assert approved.json()["monitor_status"] == "fallback_required"


def test_pm_intake_approval_never_enqueues_or_accepts_synthetic_outcome(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setenv("DRIFTLINE_TASKS_ENABLED", "true")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    queued: list[tuple[str, int]] = []
    monkeypatch.setattr(
        api,
        "_enqueue_decision_twin_monitor",
        lambda case_id, generation: queued.append((case_id, generation)),
    )
    persistence._decision_cases_memory.clear()
    case = client.post(
        "/api/decision-twin/intake",
        json={
            "question": "Should we expand the beta to all mid-market accounts next month?",
            "current_commitment": "Launch to every mid-market account on September 15.",
            "urgency": "Sales committed the date and allocation is due this Friday.",
            "positive_signal": "Beta users complete the core workflow faster than the control group.",
            "risk_signal": "Admins report permission confusion and support volume is rising.",
            "affected_segment": "mid-market admins",
            "measurement_contract": _pm_measurement_contract_payload(),
        },
    ).json()

    approved = client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Taylor PM",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    synthetic = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/demo",
        json={"expected_generation": 1, "scenario": "guardrail_breach"},
    )

    assert approved.status_code == 200
    assert approved.json()["monitor_status"] == "not_applicable"
    assert queued == []
    assert synthetic.status_code == 409
    assert "unavailable for PM-provided decisions" in synthetic.json()["detail"]


def test_pm_intake_accepts_real_two_metric_measurement_and_is_idempotent(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    case = client.post(
        "/api/decision-twin/intake",
        json={
            "question": "Should we expand the beta to all mid-market accounts next month?",
            "current_commitment": "Launch to every mid-market account on September 15.",
            "urgency": "Sales committed the date and allocation is due this Friday.",
            "positive_signal": "Beta users complete the core workflow faster than the control group.",
            "risk_signal": "Admins report permission confusion and support volume is rising.",
            "affected_segment": "mid-market admins",
            "measurement_contract": _pm_measurement_contract_payload(),
        },
    ).json()
    client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Taylor PM",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    measurement = {
        "expected_generation": 1,
        "measurement_id": "manual-safe-1",
        "primary_value": 46,
        "risk_value": 4,
        "source_label": "Weekly product analytics",
    }

    early = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/measured",
        json={**measurement, "measurement_id": "manual-early-1"},
    )
    assert early.status_code == 409
    assert "Measurement window opens at" in early.json()["detail"]
    unchanged = persistence.load_decision_case(case["case_id"])
    assert unchanged is not None
    assert unchanged.outcomes == []
    assert unchanged.action_records[0].status == "active"

    assert unchanged.experiment_plan is not None
    unchanged.experiment_plan.review_at = "invalid-review-date"
    persistence.persist_decision_case(unchanged)
    invalid_window = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/measured",
        json={**measurement, "measurement_id": "manual-invalid-window-1"},
    )
    assert invalid_window.status_code == 409
    assert "review date is invalid" in invalid_window.json()["detail"]

    _open_pm_measurement_window(case["case_id"])

    unresolved = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/measured",
        json={
            **measurement,
            "measurement_id": "manual-unresolved-1",
            "primary_value": 40,
        },
    )
    measured = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/measured",
        json=measurement,
    )
    duplicate = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/measured",
        json=measurement,
    )

    assert unresolved.status_code == 200
    assert unresolved.json()["status"] == "inconclusive"
    assert unresolved.json()["action_records"][0]["status"] == "active"
    assert measured.status_code == 200
    payload = measured.json()
    assert payload["status"] == "validated"
    assert payload["action_records"][0]["status"] == "completed"
    assert [item["evaluation"]["verdict"] for item in payload["outcomes"]] == [
        "inconclusive",
        "inconclusive",
        "inconclusive",
        "validated",
    ]
    assert all(
        item["source_label"].endswith("PM-provided · unverified")
        for item in payload["outcomes"]
    )
    assert duplicate.status_code == 200
    assert duplicate.json() == payload


def test_pm_risk_measurement_rolls_back_and_manual_measurement_rejects_demo(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    case = client.post(
        "/api/decision-twin/intake",
        json={
            "question": "Should we expand the beta to all mid-market accounts next month?",
            "current_commitment": "Launch to every mid-market account on September 15.",
            "urgency": "Sales committed the date and allocation is due this Friday.",
            "positive_signal": "Beta users complete the core workflow faster than the control group.",
            "risk_signal": "Admins report permission confusion and support volume is rising.",
            "affected_segment": "mid-market admins",
            "measurement_contract": _pm_measurement_contract_payload(),
        },
    ).json()
    client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Taylor PM",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    _open_pm_measurement_window(case["case_id"])
    breached = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/measured",
        json={
            "expected_generation": 1,
            "measurement_id": "manual-breach-1",
            "primary_value": 46,
            "risk_value": 9,
            "source_label": "Weekly product analytics",
        },
    )

    assert breached.status_code == 200
    assert breached.json()["status"] == "reopened"
    assert breached.json()["action_records"][0]["status"] == "rolled_back"
    measured_node = next(
        node
        for node in breached.json()["evidence_nodes"]
        if node["title"] == "Measured guardrail outcome"
    )
    assert measured_node["confidence"] == 0.6
    assert measured_node["source_label"].endswith("PM-provided · unverified")

    demo = client.post("/api/decision-twin/demo").json()
    rejected = client.post(
        f"/api/decision-twin/{demo['case_id']}/outcomes/measured",
        json={
            "expected_generation": 1,
            "measurement_id": "manual-demo-1",
            "primary_value": 1,
            "risk_value": 1,
            "source_label": "Not applicable",
        },
    )
    assert rejected.status_code == 409
    assert "only for PM-provided decisions" in rejected.json()["detail"]


def test_decision_twin_monitor_records_autonomous_lineage(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setenv("DRIFTLINE_TASKS_ENABLED", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()

    case = client.post("/api/decision-twin/demo").json()
    client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Demo Product Manager",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    monitored = client.post(
        f"/api/decision-twin/{case['case_id']}/monitor/run",
        json={"expected_generation": 1, "scenario": "guardrail_breach"},
    )

    assert monitored.status_code == 200
    payload = monitored.json()
    assert payload["status"] == "reopened"
    assert any(
        event.get("action") == "autonomous_experiment_monitor"
        and event.get("outcome") == "invalidated"
        for event in payload["events"]
    )


@pytest.mark.parametrize("option_id", ["ship", "rollback", "segment", "defer"])
@pytest.mark.parametrize(
    ("scenario", "expected_status"),
    [("successful_recovery", "validated"), ("guardrail_breach", "reopened")],
)
def test_decision_twin_demo_outcomes_follow_active_plan(
    monkeypatch, option_id: str, scenario: str, expected_status: str
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    case = client.post("/api/decision-twin/demo").json()
    approved = client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Demo Product Manager",
            "option_id": option_id,
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    ).json()

    response = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/demo",
        json={"expected_generation": 1, "scenario": scenario},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == expected_status
    assert payload["outcomes"][0]["metric_id"] == (
        approved["experiment_plan"]["primary_metric"]
    )
    assert payload["outcomes"][0]["segment"] == (
        approved["experiment_plan"]["target_segment"]
    )


def test_decision_twin_demo_runs_are_isolated(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()

    first = client.post("/api/decision-twin/demo")
    second = client.post("/api/decision-twin/demo")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["case_id"] != second.json()["case_id"]


def test_decision_twin_fallback_event_is_never_labeled_google_adk(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()

    case = client.post("/api/decision-twin/demo").json()
    event = next(e for e in case["events"] if e["event_id"] == "product-council-complete")

    assert event["action"] == "deterministic_product_council"
    assert event["execution_mode"] == "deterministic_demo_fallback"


def test_decision_twin_live_metadata_targets_council_event_and_bigquery_is_offloaded(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "true")
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_ENABLED", "true")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    monkeypatch.setattr(api, "_reserve_product_council_calls", lambda: True)
    persistence._decision_cases_memory.clear()
    offloaded: list[str] = []

    def metric(_metric_id, segment):
        return SimpleNamespace(
            metric_id="activation_rate",
            segment=segment,
            value=0.09 if segment == "small_workspaces" else -0.11,
            sample_size=42,
            observed_at="2026-08-23T18:00:00+00:00",
        )

    async def to_thread(function, *args):
        offloaded.append(args[1])
        return function(*args)

    async def live_council(case):
        council = case.council.model_copy(deep=True)
        council.mode = "google_adk"
        return council

    monkeypatch.setattr(api, "query_aggregate_metric", metric)
    monkeypatch.setattr(api.asyncio, "to_thread", to_thread)
    monkeypatch.setattr(api, "run_live_product_council", live_council)

    case = client.post("/api/decision-twin/demo").json()
    events = {event["event_id"]: event for event in case["events"]}

    assert sorted(offloaded) == ["enterprise_workspaces", "small_workspaces"]
    assert events["bigquery-aggregate-attached"].get("execution_mode") is None
    assert events["product-council-complete"]["execution_mode"] == "google_adk"
    assert events["product-council-complete"]["model"] == "gemini-3.5-flash"


def test_decision_twin_bigquery_runtime_failure_uses_labelled_fixture(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_ENABLED", "true")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()

    def unavailable(*_args):
        raise RuntimeError("transport detail")

    monkeypatch.setattr(api, "query_aggregate_metric", unavailable)
    response = client.post("/api/decision-twin/demo")

    assert response.status_code == 200
    event = next(
        e
        for e in response.json()["events"]
        if e["event_id"] == "bigquery-aggregate-unavailable"
    )
    assert event["reason"] == "bigquery_runtime_unavailable"
    assert "transport detail" not in str(event)


def test_decision_twin_rejects_stale_synthesis_and_stale_generation(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda: True)
    persistence._decision_cases_memory.clear()
    case = client.post("/api/decision-twin/demo").json()

    stale = client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Demo Product Manager",
            "option_id": "segment",
            "expected_synthesis_hash": "0" * 64,
            "expected_generation": 1,
        },
    )
    assert stale.status_code == 409
    assert "stale synthesis" in stale.json()["detail"]

    approved = client.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json={
            "approver": "Demo Product Manager",
            "option_id": "segment",
            "expected_synthesis_hash": case["council"]["synthesis_hash"],
            "expected_generation": 1,
        },
    )
    assert approved.status_code == 200
    outcome = client.post(
        f"/api/decision-twin/{case['case_id']}/outcomes/demo",
        json={"expected_generation": 2, "scenario": "guardrail_breach"},
    )
    assert outcome.status_code == 409
    assert "stale decision generation" in outcome.json()["detail"]


def test_auth_config_exposes_only_public_google_client_configuration(monkeypatch) -> None:
    monkeypatch.setenv(
        "DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE",
        "32555940559.apps.googleusercontent.com",
    )
    response = client.get("/api/auth/config")
    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "client_id": "32555940559.apps.googleusercontent.com",
        "mode": "google_oidc",
        "anonymous_lane": "packet_only",
        "sign_in_origin": None,
        "credential_values_exposed": False,
    }
    assert response.headers["cache-control"] == "no-store"
    assert "script-src" in response.headers["content-security-policy"]
    assert "https://accounts.google.com/gsi/" in response.headers["content-security-policy"]
    assert "style-src-elem" in response.headers["content-security-policy"]
    assert "fonts.googleapis.com" not in response.headers["content-security-policy"]


def test_auth_config_exposes_only_a_valid_https_signin_origin(monkeypatch) -> None:
    monkeypatch.setenv(
        "DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE",
        "32555940559.apps.googleusercontent.com",
    )
    monkeypatch.setenv(
        "DRIFTLINE_GOOGLE_OPERATOR_SIGNIN_ORIGIN",
        "https://driftline.example.com/",
    )
    assert client.get("/api/auth/config").json()["sign_in_origin"] == (
        "https://driftline.example.com"
    )

    monkeypatch.setenv(
        "DRIFTLINE_GOOGLE_OPERATOR_SIGNIN_ORIGIN",
        "https://driftline.example.com/oauth/callback",
    )
    assert client.get("/api/auth/config").json()["sign_in_origin"] is None


def test_api_responses_are_not_cacheable() -> None:
    response = client.get("/api/ops/value-proof")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_trace_evaluation_fixture_is_persisted_without_raw_trace_fields(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    persistence._evaluations_memory.clear()

    response = client.post("/api/evals/run", json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pass"
    evaluation = payload["evaluation"]
    assert evaluation["gate_status"] == "pass"
    assert evaluation["trace_redacted"] is True
    assert evaluation["customer_outcome"] is False
    assert '"before":' not in response.text
    assert '"after":' not in response.text
    assert '"prompt":' not in response.text
    latest = client.get("/api/evals/latest")
    assert latest.status_code == 200
    assert latest.json()["evaluation"]["evaluation_id"] == evaluation["evaluation_id"]


def test_trace_evaluation_latest_is_not_run_when_public_ledger_is_empty(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    persistence._evaluations_memory.clear()

    response = client.get("/api/evals/latest")

    assert response.status_code == 200
    assert response.json() == {
        "status": "not_run",
        "scope": "public_evaluation",
        "evaluation": None,
        "customer_outcome": False,
        "trace_redacted": True,
    }


def test_trace_evaluation_history_is_bounded_and_summary_only(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    persistence._evaluations_memory.clear()

    first = client.post("/api/evals/run", json={})
    second = client.post("/api/evals/run", json={})
    assert first.status_code == 200
    assert second.status_code == 200

    response = client.get("/api/evals/history?limit=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["scope"] == "public_evaluation"
    assert len(payload["evaluations"]) == 1
    point = payload["evaluations"][0]
    assert point["evaluation_id"] == second.json()["evaluation"]["evaluation_id"]
    assert point["gate_status"] == "pass"
    assert point["overall_score"] == 1.0
    assert "cases" not in point
    assert "tenant_id" not in point
    assert "expires_at" not in point
    assert payload["trace_redacted"] is True


def test_trace_evaluation_history_requires_complete_signed_context(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    persistence._evaluations_memory.clear()

    response = client.get("/api/evals/history?tenant_id=history-acme")

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Signed approval is required for tenant evaluation records"
    )


@pytest.mark.asyncio
async def test_api_cache_policy_overrides_endpoint_cache_header() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/test-cache-policy",
            "scheme": "https",
            "server": ("testserver", 443),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"",
            "headers": [],
        }
    )

    async def call_next(_request: Request) -> Response:
        return Response(headers={"Cache-Control": "public, max-age=3600"})

    response = await api.security_headers(request, call_next)

    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_permissions_policy_overrides_endpoint_capability_header() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/test-permissions-policy",
            "scheme": "https",
            "server": ("testserver", 443),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"",
            "headers": [],
        }
    )

    async def call_next(_request: Request) -> Response:
        return Response(
            headers={"Permissions-Policy": "camera=(self), microphone=(self)"}
        )

    response = await api.security_headers(request, call_next)

    assert response.headers["permissions-policy"] == (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    )


@pytest.mark.asyncio
async def test_fingerprinted_static_assets_are_immutable_cacheable() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/assets/index-abc123.js",
            "scheme": "https",
            "server": ("testserver", 443),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"",
            "headers": [],
        }
    )

    async def call_next(_request: Request) -> Response:
        return Response()

    response = await api.security_headers(request, call_next)

    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.asyncio
async def test_missing_static_asset_is_not_cached_as_immutable() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/assets/missing.js",
            "scheme": "https",
            "server": ("testserver", 443),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"",
            "headers": [],
        }
    )

    async def call_next(_request: Request) -> Response:
        return Response(status_code=404)

    response = await api.security_headers(request, call_next)

    assert "cache-control" not in response.headers


@pytest.mark.asyncio
async def test_html_shell_is_not_cached_across_releases() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "scheme": "https",
            "server": ("testserver", 443),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"",
            "headers": [],
        }
    )

    async def call_next(_request: Request) -> Response:
        return Response(
            content="<!doctype html>",
            media_type="text/html",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    response = await api.security_headers(request, call_next)

    assert response.headers["cache-control"] == "no-store"


def test_public_job_payload_redacts_caller_text_and_internal_claims() -> None:
    public_job = JobState(
        job_id="job-public-redaction",
        status="failed",
        query="private customer note that must not be echoed",
        user_id="untrusted-public-user",
        response="raw model response",
        error="provider exception detail",
        claim_id="opaque-claim",
    )

    payload = api._job_payload(public_job)

    assert "query" not in payload
    assert "user_id" not in payload
    assert "response" not in payload
    assert "error" not in payload
    assert "claim_id" not in payload
    assert payload["public_summary"] == "Public demo run failed; internal details are withheld."

    tenant_job = JobState(
        job_id="job-tenant-full",
        tenant_id="driftline-demo",
        query="signed tenant query",
        response="signed tenant response",
        claim_id="tenant-claim",
    )
    tenant_payload = api._job_payload(tenant_job)
    assert tenant_payload["query"] == "signed tenant query"
    assert tenant_payload["response"] == "signed tenant response"
    assert tenant_payload["claim_id"] == "tenant-claim"


def test_recover_orphaned_workflow_matches_recent_exact_source(monkeypatch) -> None:
    job = JobState(
        job_id="job-partial-agent",
        tenant_id="driftline-demo",
        source_id="custom/acme-pricing",
        created_at="2026-08-21T06:00:00+00:00",
    )
    state = WorkflowState(
        workflow_id="workflow-partial-agent",
        title="Pricing changed",
        tenant_id="driftline-demo",
        evidence=SourceEvidence(
            source_id="custom/acme-pricing",
            source_name="Acme pricing",
            before="old",
            after="new",
            evidence_hash="hash",
            confidence=0.99,
        ),
        created_at="2026-08-21T06:00:05+00:00",
    )
    monkeypatch.setattr(api.workflow_store, "_runs", {state.workflow_id: state})
    monkeypatch.setattr(api, "list_workflows", lambda limit=50: [])

    recovered = api._recover_orphaned_workflow(job)

    assert recovered is state


def test_tenant_metrics_exclude_tenantless_and_other_tenant_records() -> None:
    tenantless = SimpleNamespace(tenant_id=None)
    own = SimpleNamespace(tenant_id="acme")
    other = SimpleNamespace(tenant_id="other-acme")

    assert api._visible_tenant_record(tenantless, None) is True
    assert api._visible_tenant_record(own, None) is False
    assert api._visible_tenant_record(tenantless, {"tenant_id": "acme"}) is False
    assert api._visible_tenant_record(own, {"tenant_id": "acme"}) is True
    assert api._visible_tenant_record(other, {"tenant_id": "acme"}) is False


def test_durable_record_merge_does_not_underreport_after_instance_restart(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")
    local = JobState(job_id="job-local", created_at="2026-08-20T00:02:00+00:00")
    durable = JobState(job_id="job-durable", created_at="2026-08-20T00:01:00+00:00")
    refreshed = JobState(job_id="job-local", created_at="2026-08-20T00:03:00+00:00")

    merged = api._merge_durable_records(
        [local],
        lambda _limit: [durable, refreshed],
        limit=20,
        key=lambda item: item.job_id,
    )

    assert {item.job_id for item in merged} == {"job-local", "job-durable"}
    # The in-flight local copy wins over an older or concurrently written
    # durable snapshot; the durable-only record must still be included.
    assert next(item for item in merged if item.job_id == "job-local").created_at.endswith("02:00+00:00")


def test_available_tenants_is_identity_only_and_filters_disabled_memberships(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "test-audience")
    monkeypatch.setattr(
        api,
        "_verify_google_identity_claims",
        lambda _token, _audience: {
            "email": "member@example.com",
            "sub": "subject-available",
        },
    )
    api.persist_tenant({"tenant_id": "available-acme", "status": "active"})
    api.persist_tenant({"tenant_id": "available-disabled", "status": "disabled"})
    api.persist_tenant_membership(
        {
            "tenant_id": "available-acme",
            "email": "member@example.com",
            "role": "operator",
            "status": "active",
        }
    )
    api.persist_tenant_membership(
        {
            "tenant_id": "available-disabled",
            "email": "member@example.com",
            "role": "owner",
            "status": "active",
        }
    )

    response = client.get(
        "/api/tenants/available", params={"identity_token": "opaque-token"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "member@example.com"
    assert payload["selection_required"] is False
    assert payload["tenants"] == [
        {
            "tenant_id": "available-acme",
            "role": "operator",
            "membership_id": payload["tenants"][0]["membership_id"],
            "status": "active",
        }
    ]
    assert payload["credential_values_exposed"] is False


def test_available_tenants_accepts_bearer_identity_header(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "test-audience")
    captured: dict[str, object] = {}

    def verify(token, audience):
        captured.update(token=token, audience=audience)
        return {"email": "header@example.com", "sub": "subject-header"}

    monkeypatch.setattr(api, "_verify_google_identity_claims", verify)
    monkeypatch.setattr(
        api,
        "list_tenant_memberships_for_email",
        lambda email: [
            {
                "tenant_id": "header-acme",
                "email": email,
                "role": "owner",
                "status": "active",
                "membership_id": "membership-header",
            }
        ],
    )
    monkeypatch.setattr(
        api,
        "load_tenant",
        lambda tenant_id: {"tenant_id": tenant_id, "status": "active"},
    )

    response = client.get(
        "/api/tenants/available",
        headers={"Authorization": "Bearer opaque-header-token"},
    )

    assert response.status_code == 200
    assert captured == {
        "token": "Bearer opaque-header-token",
        "audience": "test-audience",
    }
    assert response.json()["tenants"][0]["tenant_id"] == "header-acme"


def test_monitor_registry_and_ops_summary_are_safe_for_operator_console() -> None:
    registry = client.get("/api/monitor/registry")
    assert registry.status_code == 200
    registry_payload = registry.json()
    assert registry_payload["append_only"] is True
    assert registry_payload["summary"]["total"] == 5
    assert registry_payload["summary"]["source_failed"] == 0
    assert "due" in registry_payload["summary"]
    assert all("cadence_due" in item for item in registry_payload["sources"])
    assert all(
        "token" not in str(item).casefold() for item in registry_payload["sources"]
    )

    ops = client.get("/api/ops/summary")
    assert ops.status_code == 200
    ops_payload = ops.json()
    assert ops_payload["project_id"]
    assert set(ops_payload["connectors"]) == {"jira", "confluence", "slack", "github"}
    assert "guardrails" in ops_payload
    assert ops_payload["crm"]["salesforce"]["mode"] == "prepared_only"
    assert ops_payload["crm"]["salesforce"]["external_read"] is False
    assert ops_payload["crm"]["salesforce"]["aggregate_read_verified"] is False
    assert ops_payload["crm"]["salesforce"]["aggregate_read_status"] == "not_run"
    assert ops_payload["crm"]["salesforce"]["credential_values_exposed"] is False
    assert ops_payload["approval_security"]["external_writes_require_signed"] is True
    assert ops_payload["approval_security"]["credential_model"]["tenant_bound"] is True
    assert ops_payload["guardrails"]["tenant_policy"] is None
    assert ops_payload["jobs"]["dead_lettered"] == 0
    assert ops_payload["source_health_summary"]["total"] == 5
    assert ops_payload["source_health_summary"]["paused"] == 0

    value_proof = client.get("/api/ops/value-proof")
    assert value_proof.status_code == 200
    assert value_proof.json()["scope"] == "observed_driftline_public_evaluation_records"
    assert "willingness_to_pay" in value_proof.json()["not_measured"]
    assert "change_cards" in value_proof.json()["observed"]
    assert "workflow_data_modes" in value_proof.json()["observed"]
    assert "job_run_modes" in value_proof.json()["observed"]
    assert "tenantless_workflows" in value_proof.json()["observed"]
    assert "high_materiality_cards" in value_proof.json()["observed"]
    assert "cards_dismissed" in value_proof.json()["observed"]
    assert "overdue_owner_actions" in value_proof.json()["observed"]
    assert "owner_action_cycle_seconds" in value_proof.json()["observed"]
    assert "action_items_completed_historically" in value_proof.json()["observed"]
    assert "action_item_completion_rate_historically" in value_proof.json()["observed"]
    assert "source_observations_unchanged" in value_proof.json()["observed"]
    assert "source_observations_changed" in value_proof.json()["observed"]
    assert "source_no_op_comparison_rate" in value_proof.json()["observed"]
    outcomes = client.get("/api/ops/outcomes")
    assert outcomes.status_code == 200
    assert outcomes.json()["status"] == "not_measured"


def test_signed_operational_metrics_keep_paused_sources_visible(monkeypatch) -> None:
    """A paused tenant source remains part of operational truth."""
    captured: dict[str, object] = {}

    def fake_identity(*_args, **_kwargs) -> dict[str, str]:
        return {"tenant_id": "paused-acme", "role": "owner", "identity": "owner"}

    def fake_health(**kwargs):
        captured.update(kwargs)
        return [
            {
                "source_id": "custom/paused-pricing",
                "status": "paused",
                "observation_count": 2,
                "unchanged_observation_count": 2,
                "changed_observation_count": 0,
                "cadence_due": False,
            }
        ]

    monkeypatch.setattr(api, "_verify_approval_mode", fake_identity)
    monkeypatch.setattr(api, "source_registry_health", fake_health)

    payload = api.get_value_proof(
        operator="owner",
        tenant_id="paused-acme",
        approval_token="signed-token",
    )

    assert captured["tenant_id"] == "paused-acme"
    assert captured["include_disabled"] is True
    assert payload["observed"]["sources_total"] == 1
    assert payload["observed"]["sources_paused"] == 1


def test_public_telemetry_uses_recent_bounded_window_without_hiding_history(monkeypatch) -> None:
    monkeypatch.setattr(api, "PUBLIC_METRIC_WINDOW", 1)
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda *_args: True)
    monkeypatch.setattr(
        api,
        "source_registry_health",
        lambda **_kwargs: [
            {"status": "healthy", "observation_count": 3},
            {"status": "healthy", "observation_count": 2},
        ],
    )

    original_runs = dict(api.workflow_store._runs)
    try:
        first = client.post("/api/workflows/demo")
        second = client.post("/api/workflows/demo")
        assert first.status_code == 200
        assert second.status_code == 200

        value = client.get("/api/ops/value-proof").json()
        assert value["telemetry_window"] == {
            "scope": "public_recent_evaluation_window",
            "limit": 1,
            "append_only_history": True,
        }
        assert value["observed"]["workflows"] <= 1
        assert value["observed"]["source_observations"] == 1
        assert value["observed"]["source_observation_window"] == value["telemetry_window"]

        memory = client.get("/api/memory/summary?limit=50").json()
        assert memory["history_window"] == value["telemetry_window"]
        assert memory["work_summary"]["workflow_count"] <= 1

        ops = client.get("/api/ops/summary").json()
        assert ops["telemetry_window"] == {
            "scope": "public_recent_evaluation_window",
            "limit": 1,
            "append_only_history": True,
        }
    finally:
        api.workflow_store._runs.clear()
        api.workflow_store._runs.update(original_runs)


def test_source_registry_and_freshness_can_be_bound_to_signed_tenant(monkeypatch) -> None:
    """Tenant operators can read only their signed source metadata surface."""
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "source-registry-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    actor = "Tenant reader"
    tenant_id = "driftline-demo"

    sources_token = hmac.new(
        secret.encode(), f"sources:list:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    sources = client.get(
        "/api/sources",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": sources_token,
        },
    )
    assert sources.status_code == 200
    assert len(sources.json()["sources"]) == 5
    assert all("token" not in str(item).casefold() for item in sources.json()["sources"])

    registry_token = hmac.new(
        secret.encode(), f"monitor-registry:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    registry = client.get(
        "/api/monitor/registry",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": registry_token,
        },
    )
    assert registry.status_code == 200
    assert registry.json()["summary"]["total"] == 5
    assert all("token" not in str(item).casefold() for item in registry.json()["sources"])


def test_signed_tenant_usage_is_aggregate_and_not_billing(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "usage-route-secret"
    actor = "Usage reader"
    tenant_id = "usage-route-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.record_tenant_usage(tenant_id, "agent_calls", period="2026-08")
    api.record_tenant_usage(tenant_id, "workflow_mutations", amount=2, period="2026-08")
    token = hmac.new(
        secret.encode(), f"tenant-usage:{actor}".encode(), hashlib.sha256
    ).hexdigest()

    response = client.get(
        "/api/tenants/usage",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "period": "2026-08",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["usage"] == {
        "agent_calls": 1,
        "workflow_mutations": 2,
        "connector_calls": 0,
        "monitor_jobs": 0,
    }
    assert payload["metering"]["durable"] is True
    assert payload["metering"]["billing_enabled"] is False
    assert payload["credential_values_exposed"] is False


def test_owner_can_update_and_read_tenant_quota_policy(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    secret = "tenant-policy-route-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    actor = "Policy owner"
    update_token = hmac.new(
        secret.encode(), f"tenant-policy-update:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    response = client.post(
        "/api/tenants/policy",
        json={
            "operator": actor,
            "tenant_id": "driftline-demo",
            "agent_calls_per_window": 17,
            "workflow_mutations_per_window": 42,
            "retention_days": 90,
            "approval_token": update_token,
        },
    )
    assert response.status_code == 200
    assert response.json()["policy"] == {
        "agent_calls_per_window": 17,
        "workflow_mutations_per_window": 42,
        "connector_calls_per_window": 60,
        "retention_days": 90,
    }

    read_token = hmac.new(
        secret.encode(), f"tenant-policy-read:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    read = client.get(
        "/api/tenants/policy",
        params={
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": read_token,
        },
    )
    assert read.status_code == 200
    assert read.json()["policy"]["agent_calls_per_window"] == 17
    assert read.json()["policy"]["connector_calls_per_window"] == 60
    assert read.json()["policy"]["retention_days"] == 90
    assert read.json()["billing_enabled"] is False


def test_signed_job_failure_ledger_is_tenant_filtered_and_redacted(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "failure-ledger-secret"
    actor = "Failure reader"
    tenant_id = "failure-ledger-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.persist_job_failure(
        {
            "job_id": "job-terminal-1",
            "tenant_id": tenant_id,
            "attempts": 3,
            "failed_at": "2026-08-20T00:00:00+00:00",
            "exception_text": "must never be retained",
        }
    )
    token = hmac.new(
        secret.encode(), f"job-failures:{actor}".encode(), hashlib.sha256
    ).hexdigest()

    response = client.get(
        "/api/ops/job-failures",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["failures"][0]["status"] == "dead_lettered"
    assert payload["failures"][0]["attempts"] == 3
    assert "exception_text" not in str(payload)
    assert payload["credential_values_exposed"] is False


def test_job_failure_ledger_requires_signed_operator() -> None:
    response = client.get("/api/ops/job-failures")
    assert response.status_code == 422


def test_outcome_measurements_require_signed_operator(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Anonymous",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 1,
            "baseline_minutes": 60,
            "driftline_minutes": 20,
            "evidence_ref": "artifact://pilot-a",
        },
    )
    assert response.status_code == 401


def test_outcome_measurement_records_direction_and_operational_counts(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    monkeypatch.setattr(
        api,
        "persist_outcome_measurement",
        lambda payload: captured.update(payload),
    )

    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Pilot owner",
            "tenant_id": "pilot-tenant",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 2,
            "baseline_minutes": 120,
            "driftline_minutes": 40,
            "baseline_owner_ready_within_24h": 1,
            "driftline_owner_ready_within_24h": 2,
            "baseline_actions_completed_within_7d": 0,
            "driftline_actions_completed_within_7d": 1,
            "baseline_reversed_or_reopened": 1,
            "driftline_reversed_or_reopened": 0,
            "evidence_ref": "artifact://pilot-a",
        },
    )

    assert response.status_code == 200
    assert captured["time_saved_minutes_total"] == 80
    assert captured["time_saved_minutes_per_change"] == 40
    assert captured["time_delta_direction"] == "saved"
    assert captured["baseline_owner_ready_within_24h"] == 1
    assert captured["driftline_actions_completed_within_7d"] == 1


def test_outcome_measurement_retry_is_idempotent(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    monkeypatch.setattr(api, "persist_outcome_measurement", lambda payload: False)
    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Pilot owner",
            "tenant_id": "pilot-tenant",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 1,
            "baseline_minutes": 60,
            "driftline_minutes": 20,
            "evidence_ref": "artifact://pilot-a",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "already_recorded"
    assert response.json()["measurement"]["measurement_id"].startswith("measurement-")


def test_outcome_measurement_changed_retry_is_a_conflict(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    monkeypatch.setattr(
        api,
        "persist_outcome_measurement",
        lambda payload: (_ for _ in ()).throw(ValueError("outcome_measurement_conflict")),
    )
    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Pilot owner",
            "tenant_id": "pilot-tenant",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 1,
            "baseline_minutes": 60,
            "driftline_minutes": 20,
            "evidence_ref": "artifact://pilot-a",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "outcome_measurement_conflict_for_evidence_ref"


def test_outcome_measurement_rejects_operational_count_above_change_set(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Pilot owner",
            "tenant_id": "pilot-tenant",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 1,
            "baseline_minutes": 60,
            "driftline_minutes": 20,
            "baseline_actions_completed_within_7d": 1,
            "driftline_actions_completed_within_7d": 2,
            "evidence_ref": "artifact://pilot-a",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["message"] == "pilot_operational_count_exceeds_changes_observed"


def test_outcome_measurement_rejects_partial_operational_pair(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Pilot owner",
            "tenant_id": "pilot-tenant",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 1,
            "baseline_minutes": 60,
            "driftline_minutes": 20,
            "baseline_owner_ready_within_24h": 1,
            "evidence_ref": "artifact://pilot-a",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["message"] == "pilot_operational_metric_requires_baseline_and_driftline"


def test_outcome_measurement_rejects_zero_baseline(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Pilot owner",
            "tenant_id": "pilot-tenant",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 1,
            "baseline_minutes": 0,
            "driftline_minutes": 0,
            "evidence_ref": "artifact://pilot-a",
        },
    )

    assert response.status_code == 422


def test_pilot_report_requires_signed_operator() -> None:
    response = client.get("/api/ops/pilot-report")
    assert response.status_code == 401


def test_pilot_packet_requires_signed_operator() -> None:
    response = client.get("/api/ops/pilot-packet")
    assert response.status_code == 401


def test_pilot_report_is_tenant_filtered_and_aggregate_only(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    monkeypatch.setattr(
        api,
        "list_outcome_measurements",
        lambda _limit: [
            {
                "tenant_id": "pilot-tenant",
                "cohort_label": "pilot-a",
                "changes_observed": 2,
                "baseline_minutes": 120,
                "driftline_minutes": 40,
                "baseline_owner_ready_within_24h": 1,
                "driftline_owner_ready_within_24h": 2,
                "baseline_actions_completed_within_7d": 0,
                "driftline_actions_completed_within_7d": 1,
                "baseline_reversed_or_reopened": 1,
                "driftline_reversed_or_reopened": 0,
                "revenue_lift_usd": 1500,
                "retention_lift_pct": 4,
                "willingness_to_pay_usd": 900,
                "evidence_ref": "https://private.example/not-returned",
            },
            {
                "tenant_id": "other-tenant",
                "cohort_label": "pilot-a",
                "changes_observed": 99,
                "baseline_minutes": 999,
                "driftline_minutes": 1,
            },
        ],
    )

    response = client.get(
        "/api/ops/pilot-report",
        params={"operator": "Pilot owner", "tenant_id": "pilot-tenant", "cohort_label": "pilot-a"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_count"] == 1
    assert payload["changes_observed"] == 2
    assert payload["time_saved_minutes_total"] == 80
    assert payload["time_saved_minutes_per_change"] == 40
    assert payload["time_delta_direction"] == "saved"
    assert payload["time_delta_pct"] == 66.67
    assert payload["operational_metrics"]["owner_ready_within_24h"]["delta_percentage_points"] == 50
    assert payload["operational_metrics"]["actions_completed_within_7d"]["driftline_rate_pct"] == 50
    assert payload["time_saved_pct"] == 66.67
    assert payload["revenue_lift_usd_total"] == 1500
    assert payload["willingness_to_pay_usd_median"] == 900
    assert "evidence_ref" not in str(payload)
    assert payload["status"] == "operator_reported_unverified"


def test_pilot_packet_is_aggregate_only(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *args, **kwargs: {"tenant_id": "pilot-tenant", "identity": "signed_operator"},
    )
    monkeypatch.setattr(
        api,
        "list_outcome_measurements",
        lambda _limit: [
            {
                "tenant_id": "pilot-tenant",
                "cohort_label": "pilot-a\nforged-heading",
                "changes_observed": 2,
                "baseline_minutes": 120,
                "driftline_minutes": 40,
                "revenue_lift_usd": 1500,
                "retention_lift_pct": 4,
                "willingness_to_pay_usd": 900,
                "evidence_ref": "gs://private/not-returned",
            },
        ],
    )
    monkeypatch.setattr(
        api,
        "get_value_proof",
        lambda **kwargs: {
            "observed": {
                "workflows": 3,
                "source_observations": 8,
                "source_observations_unchanged": 5,
                "source_observations_changed": 3,
                "source_no_op_comparison_rate": 0.625,
                "action_items_completed_historically": 2,
                "approval_latency_seconds": {"p50": 0.5, "p90": 1.2},
                "owner_action_cycle_seconds": {"p50": 3.7, "p90": 4.1},
            }
        },
    )

    response = client.get(
        "/api/ops/pilot-packet",
        params={
            "operator": "Pilot owner",
            "tenant_id": "pilot-tenant",
            "cohort_label": "pilot-a\nforged-heading",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith('driftline-pilot-packet.md"')
    body = response.text
    assert "Time saved minutes total: 80.0" in body
    assert "Revenue / win-rate lift: 1500.0" in body
    assert "pilot-a forged-heading" in body
    assert "gs://private/not-returned" not in body
    assert "evidence_ref" not in body
    assert "pilot-tenant" not in body
    assert "Workflows observed: 3" in body
    assert "No-op source observations: 5" in body
    assert "Material ledger changes: 3" in body
    assert "No-op comparison rate: 0.625" in body
    assert "Owner-action cycle p50 / p90 seconds: 3.7 / 4.1" in body
    assert "not customer proof" in body


def test_connector_context_summary_is_signed_and_redacted(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "context-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setattr(
        api,
        "_connector_context_info",
        lambda _tenant_id: {
            "jira": {
                "status": "ok",
                "scope": "read_only_project",
                "external_read": True,
                "open_issue_count": 2,
                "redaction": "aggregate_metadata_only",
            }
        },
    )
    token = hmac.new(
        secret.encode(), b"connector-context-summary:Signed operator", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Signed operator",
            "tenant_id": "driftline-demo",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "driftline-demo"
    assert payload["context_contract"]["persisted"] is False
    assert payload["context_contract"]["redaction"] == "aggregate_metadata_only"
    assert payload["connectors"]["jira"]["open_issue_count"] == 2
    assert "private" not in str(payload)


def test_connector_context_summary_rejects_unsigned_public_request(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    response = client.post(
        "/api/connectors/context/summary",
        json={"operator": "Anonymous"},
    )
    assert response.status_code == 401


def test_hmac_tenant_allowlist_rejects_unknown_tenant(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", "allowlist-secret")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    token = hmac.new(
        b"allowlist-secret",
        b"connector-context-summary:Tenant context",
        hashlib.sha256,
    ).hexdigest()
    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Tenant context",
            "tenant_id": "other-tenant",
            "approval_token": token,
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "tenant_not_allowlisted"


def test_hmac_can_require_a_tenant_specific_signing_secret(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS", "true")
    monkeypatch.setenv("DRIFTLINE_TENANT_SIGNING_SECRET_PREFIX", "driftline-signer-")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "signer-acme")
    tenant_secret = "signer-acme-secret"

    def fake_read_secret(name: str) -> str:
        assert name == tenant_operator_signing_secret_name(
            "signer-acme", "driftline-signer-"
        )
        return tenant_secret

    monkeypatch.setattr(api, "read_secret", fake_read_secret)
    token = hmac.new(
        tenant_secret.encode(),
        b"connector-context-summary:Tenant signer",
        hashlib.sha256,
    ).hexdigest()
    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Tenant signer",
            "tenant_id": "signer-acme",
            "approval_token": token,
        },
    )
    assert response.status_code == 200

    wrong_token = hmac.new(
        b"deployment-wide-secret",
        b"connector-context-summary:Tenant signer",
        hashlib.sha256,
    ).hexdigest()
    rejected = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Tenant signer",
            "tenant_id": "signer-acme",
            "approval_token": wrong_token,
        },
    )
    assert rejected.status_code == 401


def test_hmac_required_tenant_signer_fails_closed_when_secret_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS", "true")
    monkeypatch.setenv("DRIFTLINE_TENANT_SIGNING_SECRET_PREFIX", "driftline-signer-")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "missing-acme")

    def missing_secret(_name: str) -> str:
        raise api.ConnectorError("missing")

    monkeypatch.setattr(api, "read_secret", missing_secret)
    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Missing signer",
            "tenant_id": "missing-acme",
            "approval_token": "anything",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Tenant signing secret is unavailable"


def test_production_operator_lane_rejects_hmac_without_google_identity(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY", "true")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", "break-glass-secret")
    token = hmac.new(
        b"break-glass-secret",
        b"connector-context-summary:OIDC required",
        hashlib.sha256,
    ).hexdigest()
    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "OIDC required",
            "tenant_id": "driftline-demo",
            "approval_token": token,
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Google operator identity is required for this deployment"
    )


def test_hmac_can_use_the_durable_tenant_directory_without_redeployment(monkeypatch) -> None:
    tenant_id = "durable-directory-acme"
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DRIFTLINE_ALLOW_DURABLE_HMAC_TENANTS", "true")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "")
    api.persist_tenant({"tenant_id": tenant_id, "status": "active"})

    principal = principal_for_hmac(tenant_id)

    assert principal.tenant_id == tenant_id
    assert principal.role == "owner"

    api.persist_tenant({"tenant_id": tenant_id, "status": "disabled"})
    with pytest.raises(PermissionError, match="tenant_not_allowlisted"):
        principal_for_hmac(tenant_id)

    with pytest.raises(PermissionError, match="tenant_not_allowlisted"):
        principal_for_hmac("directory-missing-acme")


def test_platform_tenant_provisioning_creates_metadata_only_bootstrap(monkeypatch) -> None:
    tenant_id = "platform-bootstrap-acme"
    monkeypatch.setattr(
        api,
        "_verify_platform_operator",
        lambda _token: {
            "identity": "google_oidc_platform_operator",
            "subject": "platform-subject",
            "email": "platform@example.com",
        },
    )
    response = client.post(
        "/api/platform/tenants",
        json={
            "operator": "Platform bootstrap",
            "tenant_id": tenant_id,
            "owner_email": "owner@example.com",
            "identity_token": "opaque-test-token",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["owner_email"] == "owner@example.com"
    assert payload["credential_values_exposed"] is False
    assert payload["secret_references"]["jira"] == (
        f"driftline-tenant-{tenant_id}-jira"
    )
    assert payload["secret_references"]["salesforce"] == (
        f"driftline-tenant-{tenant_id}-salesforce"
    )
    assert payload["operator_signing_secret"] == (
        f"driftline-tenant-operator-{tenant_id}"
    )
    assert "token" not in str(payload).casefold()
    assert api.load_tenant(tenant_id)["status"] == "active"
    assert api.list_tenant_memberships(tenant_id)[0]["role"] == "owner"


def test_platform_tenant_provisioning_rejects_duplicate_active_tenant(monkeypatch) -> None:
    tenant_id = "platform-duplicate-acme"
    api.persist_tenant({"tenant_id": tenant_id, "status": "active"})
    api.persist_tenant_membership(
        {
            "tenant_id": tenant_id,
            "email": "existing-owner@example.com",
            "role": "owner",
            "status": "active",
        }
    )
    monkeypatch.setattr(
        api,
        "_verify_platform_operator",
        lambda _token: {"identity": "google_oidc_platform_operator", "email": "platform@example.com"},
    )
    response = client.post(
        "/api/platform/tenants",
        json={
            "operator": "Platform bootstrap",
            "tenant_id": tenant_id,
            "owner_email": "owner@example.com",
            "identity_token": "opaque-test-token",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "tenant_already_exists"


def test_platform_tenant_provisioning_repairs_missing_owner_membership(monkeypatch) -> None:
    tenant_id = "platform-repair-acme"
    api.persist_tenant({"tenant_id": tenant_id, "status": "active"})
    monkeypatch.setattr(
        api,
        "_verify_platform_operator",
        lambda _token: {
            "identity": "google_oidc_platform_operator",
            "email": "platform@example.com",
        },
    )
    response = client.post(
        "/api/platform/tenants",
        json={
            "operator": "Platform repair",
            "tenant_id": tenant_id,
            "owner_email": "owner@example.com",
            "identity_token": "opaque-test-token",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["repaired_membership"] is True
    assert api.list_tenant_memberships(tenant_id)[0]["email"] == "owner@example.com"


def test_salesforce_callback_cannot_rebind_deprovisioned_tenant(monkeypatch) -> None:
    writes: list[str] = []
    monkeypatch.setattr(
        api,
        "_consume_salesforce_state",
        lambda _state: {
            "tenant_id": "callback-acme",
            "email": "owner@example.com",
            "expires_at": 9_999_999_999,
            "code_verifier": "verifier",
        },
    )
    monkeypatch.setattr(
        api,
        "exchange_salesforce_code",
        lambda *_args, **_kwargs: {
            "refresh_token": "refresh-token",
            "instance_url": "https://callback.my.salesforce.com",
        },
    )
    monkeypatch.setattr(api, "load_tenant", lambda _tenant_id: {"status": "disabled"})
    monkeypatch.setattr(
        api,
        "write_secret_version",
        lambda secret_name, _value: writes.append(secret_name),
    )

    response = client.get(
        "/api/connectors/salesforce/oauth/callback",
        params={"code": "one-time-code", "state": "opaque-state"},
    )

    assert response.status_code == 503
    assert writes == []


def test_salesforce_oauth_start_is_owner_only(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "tenant_id": "salesforce-acme",
            "role": "operator",
            "identity": "signed_operator",
        },
    )

    response = client.post(
        "/api/connectors/salesforce/start",
        json={"operator": "Operator", "tenant_id": "salesforce-acme"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant owner role is required"


def test_salesforce_status_returns_tenant_metadata_without_credentials(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "tenant_id": "salesforce-acme",
            "role": "owner",
            "identity": "signed_operator",
        },
    )
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {
            "status": "oauth_ready",
            "mode": "awaiting_authorization",
            "scope": "read_only_context",
            "allowed_objects": ["Product2", "PricebookEntry", "Opportunity"],
        },
    )
    monkeypatch.setattr(api, "load_salesforce_connection", lambda _tenant: None)
    monkeypatch.setattr(api, "load_connector_binding", lambda *_args: None)

    response = client.get(
        "/api/connectors/salesforce/status",
        params={"operator": "Owner", "tenant_id": "salesforce-acme"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "oauth_ready"
    assert payload["authorization_required"] is True
    assert payload["allowed_objects"] == ["Product2", "PricebookEntry", "Opportunity"]
    assert payload["credential_values_exposed"] is False
    assert "secret" not in payload


def test_salesforce_status_surfaces_persisted_reauthorization_state(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "tenant_id": "salesforce-acme",
            "role": "owner",
            "identity": "signed_operator",
        },
    )
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {
            "status": "oauth_ready",
            "mode": "awaiting_authorization",
            "scope": "read_only_context",
        },
    )
    monkeypatch.setattr(
        api,
        "load_salesforce_connection",
        lambda _tenant: {
            "tenant_id": "salesforce-acme",
            "status": "connected_read_only",
            "instance_url": "https://acme.my.salesforce.com",
            "health_status": "reauthorization_required",
            "health_checked_at": "2026-08-22T01:00:00Z",
            "health_reason": "refresh_token_rejected",
            "health_objects": [
                {"object": "Product2", "total": 4, "fields": ["Name"]},
            ],
        },
    )
    monkeypatch.setattr(
        api,
        "load_connector_binding",
        lambda *_args: {
            "status": "active",
            "secret_name": "driftline-tenant-salesforce-acme-salesforce",
        },
    )

    response = client.get(
        "/api/connectors/salesforce/status",
        params={"operator": "Owner", "tenant_id": "salesforce-acme"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "reauthorization_required"
    assert payload["authorization_required"] is True
    assert payload["health_reason"] == "refresh_token_rejected"
    assert payload["health_checked_at"] == "2026-08-22T01:00:00Z"
    assert payload["aggregate_read_verified"] is False
    assert payload["aggregate_read_status"] == "reauthorization_required"
    assert payload["aggregate_read_objects"] == [
        {"object": "Product2", "total": 4, "fields": ["Name"]},
    ]
    assert payload["credential_values_exposed"] is False


def test_salesforce_status_does_not_collapse_missing_binding_into_oauth_ready(monkeypatch) -> None:
    """A stale metadata record must expose the repair step, not a false setup state."""
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "tenant_id": "salesforce-acme",
            "role": "owner",
            "identity": "signed_operator",
        },
    )
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {
            "status": "oauth_ready",
            "mode": "awaiting_authorization",
            "scope": "read_only_context",
        },
    )
    monkeypatch.setattr(
        api,
        "load_salesforce_connection",
        lambda _tenant: {
            "tenant_id": "salesforce-acme",
            "status": "connected_read_only",
            "instance_url": "https://acme.my.salesforce.com",
            "health_status": "connected_read_only",
            "health_checked_at": "2026-08-22T02:00:00Z",
            "health_objects": [
                {"object": "Product2", "total": 4, "fields": []},
                {"object": "PricebookEntry", "total": 5, "fields": []},
                {"object": "Opportunity", "total": 2, "fields": []},
            ],
        },
    )
    monkeypatch.setattr(api, "load_connector_binding", lambda *_args: None)

    response = client.get(
        "/api/connectors/salesforce/status",
        params={"operator": "Owner", "tenant_id": "salesforce-acme"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "setup_incomplete"
    assert payload["setup_state"] == "binding_missing"
    assert payload["authorization_required"] is True
    assert payload["aggregate_read_verified"] is False
    assert payload["aggregate_read_status"] == "setup_incomplete"
    assert payload["aggregate_read_reason"] == "connector_binding_missing"
    assert "Reconnect Salesforce" in payload["next_step"]


def test_salesforce_callback_verifies_aggregate_read_before_persisting_connection(monkeypatch) -> None:
    writes: list[tuple[str, str]] = []
    connections: list[dict[str, object]] = []
    bindings: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    monkeypatch.setattr(
        api,
        "_consume_salesforce_state",
        lambda _state: {
            "tenant_id": "callback-acme",
            "email": "owner@example.com",
            "expires_at": 9_999_999_999,
            "code_verifier": "verifier",
        },
    )
    monkeypatch.setattr(
        api,
        "exchange_salesforce_code",
        lambda *_args, **_kwargs: {
            "access_token": "short-lived-access-token",
            "refresh_token": "refresh-token",
            "instance_url": "https://callback.my.salesforce.com",
        },
    )
    monkeypatch.setattr(api, "load_tenant", lambda _tenant_id: {"status": "active"})
    monkeypatch.setattr(
        api,
        "_write_tenant_secret",
        lambda _tenant_id, name, value: writes.append((name, value)) or "7",
    )
    monkeypatch.setattr(api, "persist_connector_binding", lambda payload: bindings.append(payload) or payload)
    monkeypatch.setattr(api, "persist_salesforce_connection", lambda payload: connections.append(payload))
    monkeypatch.setattr(api, "persist_tenant_audit_event", lambda payload: audits.append(payload))
    monkeypatch.setattr(
        api.SalesforceConfig,
        "from_env",
        lambda: SimpleNamespace(scope="api refresh_token", api_version="v61.0"),
    )

    class FakeSalesforceClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def health_summary(self):
            return {
                "status": "connected_read_only",
                "objects": [
                    {"object": "Product2", "total": 4, "fields": ["Name"]},
                    {"object": "PricebookEntry", "total": 6, "fields": []},
                    {"object": "Opportunity", "total": 2, "fields": ["StageName"]},
                ],
                "external_write": False,
            }

    monkeypatch.setattr(api, "SalesforceReadOnlyClient", FakeSalesforceClient)

    response = client.get(
        "/api/connectors/salesforce/oauth/callback",
        params={"code": "one-time-code", "state": "opaque-state"},
    )

    assert response.status_code == 200
    assert "aggregate read verified" in response.text.casefold()
    assert writes == [("driftline-tenant-callback-acme-salesforce", "refresh-token")]
    assert connections[0]["health_status"] == "connected_read_only"
    assert connections[0]["health_objects"][0]["total"] == 4
    assert bindings[0]["status"] == "active"
    assert audits[0]["aggregate_read_verified"] is True


def test_salesforce_context_is_explicitly_unconfigured_before_oauth(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {
            "status": "oauth_ready",
            "mode": "awaiting_authorization",
            "scope": "read_only_context",
        },
    )
    monkeypatch.setattr(api, "load_salesforce_connection", lambda _tenant: None)
    monkeypatch.setattr(api, "load_connector_binding", lambda *_args: None)

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload == {
        "status": "not_configured",
        "mode": "awaiting_authorization",
        "scope": "read_only_crm",
        "external_read": False,
        "redaction": "aggregate_metadata_only",
        "authorization_required": True,
    }
    assert "token" not in str(payload).casefold()
    assert "secret" not in str(payload).casefold()


def test_salesforce_context_exposes_repair_state_without_attaching_crm(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {"status": "oauth_ready", "mode": "awaiting_authorization"},
    )
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {
                "status": "connected_read_only",
                "instance_url": "https://acme.my.salesforce.com",
                "health_status": "reauthorization_required",
                "health_reason": "refresh_token_rejected",
            },
            None,
            False,
        ),
    )

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload["status"] == "reauthorization_required"
    assert payload["external_read"] is False
    assert payload["authorization_required"] is True
    assert payload["reason"] == "refresh_token_rejected"
    assert "instance_url" not in str(payload)


def test_salesforce_context_does_not_retry_expired_token_after_reauth_marker(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {"status": "oauth_ready", "mode": "awaiting_authorization"},
    )
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {
                "status": "connected_read_only",
                "instance_url": "https://acme.my.salesforce.com",
                "health_status": "reauthorization_required",
                "health_reason": "refresh_token_rejected",
            },
            {"status": "active"},
            True,
        ),
    )

    def fail_if_refresh_attempted(*_args, **_kwargs):
        raise AssertionError("expired Salesforce credential must not be retried")

    monkeypatch.setattr(api, "refresh_salesforce_token", fail_if_refresh_attempted)

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload["status"] == "reauthorization_required"
    assert payload["external_read"] is False
    assert payload["authorization_required"] is True
    assert payload["reason"] == "refresh_token_rejected"
    assert "instance_url" not in str(payload)


def test_connector_context_preserves_salesforce_external_read_boundary(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "_salesforce_context_info",
        lambda _tenant: {
            "status": "not_configured",
            "mode": "awaiting_authorization",
            "external_read": False,
            "scope": "read_only_crm",
        },
    )

    payload = api._connector_context_info("salesforce-acme")

    assert payload["salesforce"]["external_read"] is False
    assert payload["salesforce"]["status"] == "not_configured"


def test_salesforce_context_returns_aggregate_health_only_after_binding(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {"status": "oauth_ready", "mode": "awaiting_authorization"},
    )
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {"status": "connected_read_only", "instance_url": "https://acme.my.salesforce.com"},
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    monkeypatch.setattr(
        api,
        "resolve_tenant_credential",
        lambda *_args, **_kwargs: SimpleNamespace(value="refresh-token"),
    )
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: {"access_token": "short-lived-access-token"},
    )

    class FakeSalesforceClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def health_summary(self):
            return {
                "status": "connected_read_only",
                "objects": [
                    {"object": "Product2", "total": 3, "fields": ["Name"]},
                    {"object": "Opportunity", "total": 2, "fields": ["StageName"]},
                ],
                "external_write": False,
            }

    monkeypatch.setattr(api, "SalesforceReadOnlyClient", FakeSalesforceClient)

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload["status"] == "connected_read_only"
    assert payload["scope"] == "read_only_crm"
    # A binding is not enough to ground a decision: all three allowlisted
    # aggregate probes must succeed before CRM context enters the model lane.
    assert payload["external_read"] is False
    assert payload["aggregate_read_verified"] is False
    assert payload["aggregate_read_status"] == "unverified"
    assert payload["redaction"] == "aggregate_metadata_only"
    assert payload["objects"][0]["total"] == 3
    assert "refresh-token" not in str(payload)
    assert "short-lived-access-token" not in str(payload)


def test_salesforce_partial_health_never_enters_internal_context(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {"status": "oauth_ready", "mode": "awaiting_authorization"},
    )
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {"status": "connected_read_only", "instance_url": "https://acme.my.salesforce.com"},
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    monkeypatch.setattr(
        api,
        "resolve_tenant_credential",
        lambda *_args, **_kwargs: SimpleNamespace(value="refresh-token"),
    )
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: {"access_token": "short-lived-access-token"},
    )

    class FakeSalesforceClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def health_summary(self):
            return {
                "status": "failed",
                "objects": [{"object": "Product2", "total": 3, "fields": []}],
                "failed_objects": [{"object": "PricebookEntry", "reason": "salesforce_query_failed"}],
                "reason": "one_or_more_allowlisted_objects_failed",
                "external_read": False,
                "external_write": False,
            }

    monkeypatch.setattr(api, "SalesforceReadOnlyClient", FakeSalesforceClient)

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload["status"] == "failed"
    assert payload["external_read"] is False
    assert payload["failed_objects"][0]["object"] == "PricebookEntry"
    assert "refresh-token" not in str(payload)
    assert "short-lived-access-token" not in str(payload)


def test_salesforce_context_reads_refresh_token_through_tenant_identity(monkeypatch) -> None:
    """Protect the production path from bypassing tenant Secret Manager IAM."""
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {"status": "oauth_ready", "mode": "awaiting_authorization"},
    )
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {"status": "connected_read_only", "instance_url": "https://acme.my.salesforce.com"},
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    sentinel_credentials = object()
    monkeypatch.setattr(api, "tenant_secret_credentials", lambda _tenant: sentinel_credentials)

    def fake_read_secret(_name: str, *, version: str = "latest", credentials: object | None = None) -> str:
        assert version == "7"
        assert credentials is sentinel_credentials
        return "refresh-token"

    monkeypatch.setattr(api, "read_secret", fake_read_secret)

    def fake_resolve(*_args, **kwargs):
        reader = kwargs["secret_reader"]
        assert reader("tenant-secret", version="7") == "refresh-token"
        return SimpleNamespace(value="refresh-token")

    monkeypatch.setattr(api, "resolve_tenant_credential", fake_resolve)
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: {"access_token": "short-lived-access-token"},
    )

    class FakeSalesforceClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def health_summary(self):
            return {"status": "connected_read_only", "objects": []}

    monkeypatch.setattr(api, "SalesforceReadOnlyClient", FakeSalesforceClient)

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload["status"] == "connected_read_only"
    assert payload["external_read"] is False
    assert payload["aggregate_read_verified"] is False


def test_salesforce_context_surfaces_reauthorization_required(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {"status": "oauth_ready", "mode": "awaiting_authorization"},
    )
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {
                "status": "connected_read_only",
                "instance_url": "https://acme.my.salesforce.com",
            },
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    monkeypatch.setattr(
        api,
        "resolve_tenant_credential",
        lambda *_args, **_kwargs: SimpleNamespace(value="refresh-token"),
    )
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            SalesforceReauthorizationRequired("salesforce_reauthorization_required")
        ),
    )

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload["status"] == "reauthorization_required"
    assert payload["authorization_required"] is True
    assert payload["external_read"] is False
    assert payload["reason"] == "refresh_token_rejected"


def test_salesforce_context_invalidates_stale_proof_after_non_auth_failure(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SALESFORCE_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "salesforce_readiness",
        lambda: {"status": "oauth_ready", "mode": "awaiting_authorization"},
    )
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {
                "status": "connected_read_only",
                "instance_url": "https://acme.my.salesforce.com",
                "health_status": "connected_read_only",
                "health_objects": [
                    {"object": "Product2", "total": 3, "fields": []},
                    {"object": "PricebookEntry", "total": 4, "fields": []},
                    {"object": "Opportunity", "total": 5, "fields": []},
                ],
            },
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    monkeypatch.setattr(
        api,
        "resolve_tenant_credential",
        lambda *_args, **_kwargs: SimpleNamespace(value="refresh-token"),
    )
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ConnectorError("salesforce_query_failed")
        ),
    )
    recorded: list[tuple[str, str]] = []
    monkeypatch.setattr(
        api,
        "_record_salesforce_health_status",
        lambda _tenant, status, **kwargs: recorded.append((status, kwargs["reason"])),
    )

    payload = api._salesforce_context_info("salesforce-acme")

    assert payload["status"] == "failed"
    assert payload["external_read"] is False
    assert payload["aggregate_read_verified"] is False
    assert payload["aggregate_read_status"] == "unverified"
    assert payload["reason"] == "context_read_failed"
    assert recorded == [("failed", "context_read_failed")]


def test_salesforce_health_returns_reauthorization_state(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "tenant_id": "salesforce-acme",
            "role": "owner",
            "identity": "signed_operator",
        },
    )
    monkeypatch.setattr(api, "_reserve_connector_call", lambda _tenant: True)
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {
                "status": "connected_read_only",
                "instance_url": "https://acme.my.salesforce.com",
            },
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    monkeypatch.setattr(
        api,
        "resolve_tenant_credential",
        lambda *_args, **_kwargs: SimpleNamespace(value="refresh-token"),
    )
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            SalesforceReauthorizationRequired("salesforce_reauthorization_required")
        ),
    )

    payload = api.salesforce_health(
        api.SalesforceHealthRequest(operator="Owner", tenant_id="salesforce-acme")
    )

    assert payload["status"] == "reauthorization_required"
    assert payload["tenant_id"] == "salesforce-acme"
    assert payload["external_read"] is False
    assert payload["external_write"] is False
    assert payload["authorization_required"] is True


def test_salesforce_health_records_non_auth_failure_and_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {"tenant_id": "salesforce-acme", "role": "owner"},
    )
    monkeypatch.setattr(api, "_reserve_connector_call", lambda _tenant: True)
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {"status": "connected_read_only", "instance_url": "https://acme.my.salesforce.com"},
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    monkeypatch.setattr(
        api,
        "resolve_tenant_credential",
        lambda *_args, **_kwargs: SimpleNamespace(value="refresh-token"),
    )
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ConnectorError("salesforce_query_failed")
        ),
    )
    recorded: list[tuple[str, str]] = []
    monkeypatch.setattr(
        api,
        "_record_salesforce_health_status",
        lambda _tenant, status, **kwargs: recorded.append((status, kwargs["reason"])),
    )

    with pytest.raises(api.HTTPException) as error:
        api.salesforce_health(
            api.SalesforceHealthRequest(operator="Owner", tenant_id="salesforce-acme")
        )

    assert error.value.status_code == 503
    assert recorded == [("failed", "read_probe_failed")]


def test_salesforce_health_marks_only_complete_allowlist_as_verified(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {"tenant_id": "salesforce-acme", "role": "owner"},
    )
    monkeypatch.setattr(api, "_reserve_connector_call", lambda _tenant: True)
    monkeypatch.setattr(
        api,
        "_salesforce_connection_metadata",
        lambda _tenant: (
            {"status": "connected_read_only", "instance_url": "https://acme.my.salesforce.com"},
            {"status": "active"},
            True,
        ),
    )
    monkeypatch.setattr(api.SalesforceConfig, "from_env", lambda: SimpleNamespace())
    monkeypatch.setattr(
        api,
        "resolve_tenant_credential",
        lambda *_args, **_kwargs: SimpleNamespace(value="refresh-token"),
    )
    monkeypatch.setattr(
        api,
        "refresh_salesforce_token",
        lambda *_args, **_kwargs: {"access_token": "short-lived-access-token"},
    )
    monkeypatch.setattr(
        api,
        "_record_salesforce_health_status",
        lambda *_args, **_kwargs: None,
    )

    class FakeSalesforceClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def health_summary(self):
            return {
                "status": "connected_read_only",
                "objects": [
                    {"object": "Product2", "total": 3, "fields": []},
                    {"object": "PricebookEntry", "total": 5, "fields": []},
                    {"object": "Opportunity", "total": 2, "fields": []},
                ],
                "external_write": False,
            }

    monkeypatch.setattr(api, "SalesforceReadOnlyClient", FakeSalesforceClient)

    payload = api.salesforce_health(
        api.SalesforceHealthRequest(operator="Owner", tenant_id="salesforce-acme")
    )

    assert payload["status"] == "connected_read_only"
    assert payload["aggregate_read_verified"] is True
    assert payload["aggregate_read_status"] == "verified"
    assert payload["external_read"] is True
    assert payload["external_write"] is False


def test_owner_can_register_metadata_only_tenant_binding(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "binding-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "binding-acme")
    monkeypatch.setattr(api, "read_secret", lambda name: "tenant-token")
    token = hmac.new(
        secret.encode(), b"connector-binding:jira:Binding owner", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/connectors/jira/binding",
        json={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "active"
    assert payload["secret_name"] == "driftline-tenant-binding-acme-jira"
    assert payload["secret_version"] == "latest"
    assert payload["credential_value_accepted"] is False
    listed = client.get(
        "/api/connectors/bindings",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"connector-bindings-list:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert listed.status_code == 200
    assert listed.json()["credential_values_exposed"] is False
    assert listed.json()["bindings"][0]["secret_name"] == payload["secret_name"]
    revoked = client.post(
        "/api/connectors/jira/binding/revoke",
        json={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(),
                b"connector-binding-revoke:jira:Binding owner",
                hashlib.sha256,
            ).hexdigest(),
        },
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["credential_value_exposed"] is False
    assert client.get(
        "/api/connectors/bindings",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"connector-bindings-list:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    ).json()["bindings"][0]["status"] == "revoked"
    audit = client.get(
        "/api/tenants/audit",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"tenant-audit:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert audit.status_code == 200
    assert audit.json()["append_only"] is True
    assert {event["event_type"] for event in audit.json()["events"]} >= {
        "connector_binding_activated",
        "connector_binding_revoked",
    }
    assert audit.json()["credential_values_exposed"] is False
    assert "tenant-token" not in str(audit.json())
    tenant_metadata = client.get(
        "/api/tenants",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"tenant-metadata:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert tenant_metadata.status_code == 200
    assert tenant_metadata.json()["tenant"]["tenant_id"] == "binding-acme"
    assert tenant_metadata.json()["credential_values_exposed"] is False


def test_owner_can_enroll_a_tenant_connector_without_submitting_a_secret(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "enrollment-test-secret"
    tenant_id = "enrollment-route-acme"
    operator = "Enrollment owner"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)

    start_token = hmac.new(
        secret.encode(),
        b"credential-enrollment:jira:Enrollment owner",
        hashlib.sha256,
    ).hexdigest()
    started = client.post(
        "/api/connectors/jira/credential-enrollment",
        json={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": start_token,
        },
    )
    assert started.status_code == 200
    enrollment = started.json()
    assert enrollment["status"] == "awaiting_secret"
    assert enrollment["allowed_operations"] == ["read_context"]
    assert enrollment["secret_name"] == f"driftline-tenant-{tenant_id}-jira"
    assert enrollment["credential_value_exposed"] is False
    assert "opaque-token" not in str(enrollment)

    monkeypatch.setattr(api, "_read_tenant_secret", lambda *_args, **_kwargs: "opaque-token")
    monkeypatch.setattr(api, "_tenant_secret_version", lambda *_args, **_kwargs: "3")
    enrollment_id = enrollment["enrollment_id"]
    complete_token = hmac.new(
        secret.encode(),
        f"credential-enrollment-complete:jira:{enrollment_id}:Enrollment owner".encode(),
        hashlib.sha256,
    ).hexdigest()
    completed = client.post(
        f"/api/connectors/jira/credential-enrollment/{enrollment_id}/complete",
        json={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": complete_token,
        },
    )
    assert completed.status_code == 200
    payload = completed.json()
    assert payload["status"] == "active"
    assert payload["secret_version"] == "3"
    assert payload["allowed_operations"] == ["read_context"]
    assert payload["credential_value_exposed"] is False
    assert "opaque-token" not in str(payload)
    assert api.load_connector_binding(tenant_id, "jira")["allowed_operations"] == [
        "read_context",
    ]


def test_hosted_get_rejects_authentication_in_query_string(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_REJECT_QUERY_AUTH", "true")
    response = client.get("/api/sources?approval_token=redacted")
    assert response.status_code == 400
    assert "Query authentication is disabled" in response.json()["detail"]


@pytest.mark.asyncio
async def test_hosted_get_redacts_rejected_query_token_in_asgi_scope(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_REJECT_QUERY_AUTH", "true")
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/sources",
            "scheme": "https",
            "server": ("testserver", 443),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"approval_token=secret-value&operator=demo",
            "headers": [],
        }
    )

    async def call_next(_request: Request) -> Response:
        return Response()

    response = await api.secure_get_auth(request, call_next)

    assert response.status_code == 400
    assert b"secret-value" not in request.scope["query_string"]
    assert b"approval_token" not in request.scope["query_string"]
    assert b"operator=demo" in request.scope["query_string"]


def test_hosted_get_resolves_signed_auth_from_headers_without_query_token(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_REJECT_QUERY_AUTH", "true")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY", "false")
    secret = "header-auth-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    token = hmac.new(
        secret.encode(), b"sources:list:Header operator", hashlib.sha256
    ).hexdigest()

    response = client.get(
        "/api/sources?operator=Header%20operator&tenant_id=driftline-demo",
        headers={"X-Driftline-Approval": token},
    )

    assert response.status_code == 200
    assert response.json()["sources"]


def test_owner_can_inspect_credential_broker_inventory_and_access_ledger(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "credential-inventory-test-secret"
    tenant_id = "credential-inventory-acme"
    operator = "Credential owner"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": "jira",
            "secret_name": f"driftline-tenant-{tenant_id}-jira",
            "credential_id": "cred-inventory-jira-1",
            "status": "active",
            "secret_version": "4",
            "allowed_operations": ["runtime", "create_issue"],
        }
    )
    inventory = client.get(
        "/api/connectors/credentials",
        params={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(),
                b"connector-credentials-list:Credential owner",
                hashlib.sha256,
            ).hexdigest(),
        },
    )
    assert inventory.status_code == 200
    payload = inventory.json()
    assert payload["credentials"][0]["credential_id"] == "cred-inventory-jira-1"
    assert payload["credentials"][0]["allowed_operations"] == [
        "create_issue",
        "runtime",
    ]
    assert payload["credential_values_exposed"] is False
    assert "secret_name" not in str(payload)

    monkeypatch.setattr(
        api,
        "list_credential_access_events",
        lambda _tenant, limit=100: [
            {
                "tenant_id": tenant_id,
                "credential_id": "cred-inventory-jira-1",
                "connector": "jira",
                "operation": "create_issue",
                "secret_version": "4",
                "outcome": "resolved",
            }
        ],
    )
    access = client.get(
        "/api/connectors/credentials/access",
        params={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(),
                b"connector-credentials-access:Credential owner",
                hashlib.sha256,
            ).hexdigest(),
        },
    )
    assert access.status_code == 200
    assert access.json()["append_only"] is True
    assert access.json()["events"][0]["credential_id"] == "cred-inventory-jira-1"
    assert access.json()["credential_values_exposed"] is False


def test_owner_rotation_fails_closed_until_binding_is_reverified(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "rotation-test-secret"
    tenant_id = "rotation-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    monkeypatch.setattr(api, "read_secret", lambda _name: "replacement-ready")
    api.persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": "jira",
            "secret_name": f"driftline-tenant-{tenant_id}-jira",
            "status": "active",
            "scope": "tenant_bound_connector_credential",
        }
    )
    token = hmac.new(
        secret.encode(),
        b"connector-binding-rotate:jira:Rotation owner",
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/connectors/jira/binding/rotate",
        json={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "reason": "scheduled credential rotation",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rotation_pending"
    assert payload["rotation_id"].startswith("rotation-")
    assert payload["credential_value_exposed"] is False
    assert api.load_connector_binding(tenant_id, "jira")["status"] == "rotation_pending"
    repeated = client.post(
        "/api/connectors/jira/binding/rotate",
        json={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "reason": "retry after timeout",
            "approval_token": token,
        },
    )
    assert repeated.status_code == 200
    assert repeated.json()["already_pending"] is True
    assert repeated.json()["rotation_id"] == payload["rotation_id"]
    with pytest.raises(ConnectorError, match="jira_tenant_binding_missing"):
        _tenant_secret_or_env(tenant_id, "jira", "DRIFTLINE_JIRA_TOKEN")

    reactivate = client.post(
        "/api/connectors/jira/binding",
        json={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(), b"connector-binding:jira:Rotation owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert reactivate.status_code == 200
    assert reactivate.json()["status"] == "active"
    audit = client.get(
        "/api/tenants/audit",
        params={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(), b"tenant-audit:Rotation owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert audit.status_code == 200
    assert "connector_binding_rotation_requested" in {
        event["event_type"] for event in audit.json()["events"]
    }


def test_connector_binding_health_reconciles_without_exposing_credentials(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "health-test-secret"
    tenant_id = "health-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    monkeypatch.setattr(
        api,
        "list_connector_bindings",
        lambda _tenant: [
            {
                "tenant_id": tenant_id,
                "connector": "jira",
                "secret_name": f"driftline-tenant-{tenant_id}-jira",
                "status": "active",
            },
            {
                "tenant_id": tenant_id,
                "connector": "slack",
                "secret_name": f"driftline-tenant-{tenant_id}-slack",
                "status": "rotation_pending",
            },
        ],
    )
    monkeypatch.setattr(
        api,
        "load_connector_profile",
        lambda _tenant, connector: (
            {"status": "active", "settings": {"project_key": "KAN"}}
            if connector == "jira"
            else None
        ),
    )
    monkeypatch.setattr(api, "read_secret", lambda _name: "token-not-returned")
    token = hmac.new(
        secret.encode(),
        b"connector-bindings-health:Health owner",
        hashlib.sha256,
    ).hexdigest()

    response = client.get(
        "/api/connectors/bindings/health",
        params={
            "operator": "Health owner",
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {
        "total": 5,
        "healthy": 1,
        "attention": 1,
        "not_configured": 3,
    }
    jira = next(item for item in payload["checks"] if item["connector"] == "jira")
    assert jira["status"] == "healthy"
    assert jira["secret_status"] == "readable"
    assert jira["profile_status"] == "healthy"
    assert jira["profile_configured_keys"] == ["project_key"]
    slack = next(item for item in payload["checks"] if item["connector"] == "slack")
    assert slack["status"] == "attention"
    assert slack["secret_status"] == "not_checked"
    assert slack["profile_status"] == "not_configured"
    assert "token-not-returned" not in str(payload)
    assert payload["credential_values_exposed"] is False


def test_owner_can_register_non_secret_connector_profile(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "profile-route-test-secret"
    tenant_id = "profile-route-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    token = hmac.new(
        secret.encode(), b"connector-profile:jira:Profile owner", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/connectors/jira/profile",
        json={
            "operator": "Profile owner",
            "tenant_id": tenant_id,
            "settings": {
                "base_url": "https://profile.atlassian.net",
                "project_key": "PROF",
            },
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["settings"]["project_key"] == "PROF"
    assert payload["credential_values_accepted"] is False

    read_token = hmac.new(
        secret.encode(),
        b"connector-profile-read:jira:Profile owner",
        hashlib.sha256,
    ).hexdigest()
    read = client.get(
        "/api/connectors/jira/profile",
        params={
            "operator": "Profile owner",
            "tenant_id": tenant_id,
            "approval_token": read_token,
        },
    )
    assert read.status_code == 200
    assert read.json()["settings"]["base_url"] == "https://profile.atlassian.net"
    assert read.json()["credential_values_exposed"] is False
    assert "secret" not in str(read.json()).casefold()


def test_owner_can_provision_durable_member_without_credentials(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "membership-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "membership-acme")
    token = hmac.new(
        secret.encode(),
        b"tenant-member-provision:Membership owner",
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/tenants/members",
        json={
            "operator": "Membership owner",
            "tenant_id": "membership-acme",
            "email": "operator@example.com",
            "role": "operator",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "membership-acme"
    assert payload["role"] == "operator"
    assert payload["credential_values_exposed"] is False
    assert "secret" not in str(payload).casefold()


def test_owner_can_soft_deprovision_tenant_and_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "deprovision-test-secret"
    tenant_id = "deprovision-acme"
    actor = "Deprovision owner"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": "jira",
            "secret_name": f"driftline-tenant-{tenant_id}-jira",
            "status": "active",
            "scope": "tenant_bound_connector_credential",
        }
    )
    api.persist_tenant_membership(
        {
            "tenant_id": tenant_id,
            "email": "member@example.com",
            "role": "operator",
            "status": "active",
        }
    )
    token = hmac.new(
        secret.encode(), b"tenant-deprovision:Deprovision owner", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/tenants/deprovision",
        json={
            "operator": actor,
            "tenant_id": tenant_id,
            "confirmation": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
    assert response.json()["revoked_binding_count"] == 1
    assert response.json()["disabled_membership_count"] == 1
    assert response.json()["credential_values_exposed"] is False
    metadata_token = hmac.new(
        secret.encode(), b"tenant-metadata:Deprovision owner", hashlib.sha256
    ).hexdigest()
    blocked = client.get(
        "/api/tenants",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": metadata_token,
        },
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "tenant_disabled"


def test_scheduler_tick_fans_out_only_allowlisted_sources(monkeypatch) -> None:
    monkeypatch.setattr(api, "_verify_scheduler_request", lambda request: None)
    monkeypatch.setattr(
        api,
        "_start_job",
        lambda **kwargs: JobState(job_id=f"job-{kwargs['query'].split()[-2]}"),
    )
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post("/api/scheduler/tick")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_ids"] == [
        "public/pricing",
        "public/terms",
        "competitor/pricing",
        "competitor/offerings",
        "competitor/blog",
    ]
    assert len(payload["jobs"]) == 5


def test_monitor_due_selection_is_cadence_aware_and_fair_across_tenants(monkeypatch) -> None:
    entries = [
        (None, "public/pricing", {}),
        (None, "public/terms", {}),
        ("acme", "custom/acme-pricing", {}),
        ("beta", "custom/beta-pricing", {}),
    ]

    def fake_health(*, tenant_id=None):
        if tenant_id is None:
            return [
                {
                    "source_id": "public/pricing",
                    "status": "healthy",
                    "next_due_at": "2099-01-01T00:00:00+00:00",
                },
                {"source_id": "public/terms", "status": "needs_baseline"},
            ]
        return [{"source_id": f"custom/{tenant_id}-pricing", "status": "needs_baseline"}]

    monkeypatch.setattr(api, "source_registry_health", fake_health)

    selected, deferred = api._monitor_due_selection(entries, max_sources=2)

    assert [(tenant, source_id) for tenant, source_id, _ in selected] == [
        (None, "public/terms"),
        ("acme", "custom/acme-pricing"),
    ]
    assert {
        (item["tenant_id"], item["source_id"], item["reason"])
        for item in deferred
    } == {
        (None, "public/pricing", "not_due"),
        ("beta", "custom/beta-pricing", "source_cap"),
    }


def test_scheduler_tick_carries_custom_source_tenant(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/tenant-pricing",
        name="Tenant pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id="acme",
    )
    monkeypatch.setattr(api, "_verify_scheduler_request", lambda request: None)
    captured: list[dict[str, object]] = []

    def fake_start_job(**kwargs):
        captured.append(kwargs)
        return JobState(job_id=f"job-{len(captured)}")

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    monkeypatch.setenv("DRIFTLINE_MONITOR_MAX_SOURCES", "6")
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._tenant_agent_call_times.clear()

    response = client.post("/api/scheduler/tick")
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert response.status_code == 200
    custom = next(item for item in captured if item.get("tenant_id") == "acme")
    assert "custom/tenant-pricing" in str(custom["query"])
    assert custom["source_id"] == "custom/tenant-pricing"


def test_scheduler_tick_deduplicates_inflight_monitor_job(monkeypatch) -> None:
    monkeypatch.setattr(api, "_verify_scheduler_request", lambda request: None)
    in_flight = JobState(
        job_id="job-monitor-inflight",
        status="running",
        run_mode="monitor",
        source_id="public/pricing",
    )
    api._set_job(in_flight)
    captured: list[str] = []

    def fake_start_job(**kwargs):
        captured.append(str(kwargs["source_id"]))
        return JobState(job_id=f"job-{len(captured)}")

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    monkeypatch.setenv("DRIFTLINE_MONITOR_MAX_SOURCES", "5")
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._tenant_agent_call_times.clear()

    response = client.post("/api/scheduler/tick")

    assert response.status_code == 200
    payload = response.json()
    assert "public/pricing" not in payload["source_ids"]
    assert payload["in_flight_source_ids"] == ["public/pricing"]
    assert "public/pricing" not in captured


def test_signed_operator_can_onboard_an_exact_public_source(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    source_id = "custom/example-pricing"
    message = f"source-onboarding:{source_id}:Signed operator".encode()
    token = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/operator/sources",
        json={
            "source_id": source_id,
            "name": "Example pricing",
            "category": "Competitor pricing",
            "change_type": "Pricing move",
            "url": "https://example.com/pricing",
            "owner": "Product Marketing",
            "cadence": "24h",
            "freshness_sla_hours": 48,
            "parser": "html",
            "registered_by": "Signed operator",
            "approval_token": token,
        },
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "registered"
    assert (
        response.json()["source"]["allowlist"] == "exact operator-registered HTTPS URL"
    )


def test_signed_operator_can_pause_and_resume_custom_source_with_audit(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    persistence._tenant_audit_memory.clear()
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY", "false")
    monkeypatch.setenv("DRIFTLINE_ALLOW_DURABLE_HMAC_TENANTS", "false")
    monkeypatch.delenv("DRIFTLINE_TENANT_SIGNING_SECRET_PREFIX", raising=False)
    monkeypatch.delenv("DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS", raising=False)
    secret = "source-lifecycle-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
    source_id = "custom/lifecycle-pricing"
    source.register_operator_source(
        source_id=source_id,
        name="Lifecycle pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id="driftline-demo",
    )

    def token(action: str) -> str:
        return hmac.new(
            secret.encode(), f"{action}:Signed operator".encode(), hashlib.sha256
        ).hexdigest()

    try:
        pause = client.post(
            f"/api/operator/sources/{source_id}/lifecycle",
            json={
                "enabled": False,
                "reason": "Competitor page is under maintenance.",
                "operator": "Signed operator",
                "tenant_id": "driftline-demo",
                "approval_token": token(f"source-lifecycle:{source_id}:pause"),
            },
        )
        assert pause.status_code == 200
        assert pause.json()["status"] == "paused"
        assert pause.json()["audit_event"]["event_type"] == "source_paused"
        assert pause.json()["source"]["enabled"] == "false"

        sources = client.get(
            "/api/sources",
            params={
                "operator": "Signed operator",
                "tenant_id": "driftline-demo",
                "approval_token": token("sources:list"),
            },
        )
        assert sources.status_code == 200
        paused_source = next(
            item for item in sources.json()["sources"] if item["source_id"] == source_id
        )
        assert paused_source["enabled"] is False
        assert paused_source["lifecycle_status"] == "paused"

        registry = client.get(
            "/api/monitor/registry",
            params={
                "operator": "Signed operator",
                "tenant_id": "driftline-demo",
                "approval_token": token("monitor-registry"),
            },
        )
        assert registry.status_code == 200
        assert registry.json()["summary"]["paused"] == 1
        assert next(
            item for item in registry.json()["sources"] if item["source_id"] == source_id
        )["status"] == "paused"
        assert not any(
            tenant == "driftline-demo" and current_id == source_id
            for tenant, current_id, _definition in source.scheduler_source_entries()
        )

        resume = client.post(
            f"/api/operator/sources/{source_id}/lifecycle",
            json={
                "enabled": True,
                "reason": "Maintenance window is complete.",
                "operator": "Signed operator",
                "tenant_id": "driftline-demo",
                "approval_token": token(f"source-lifecycle:{source_id}:resume"),
            },
        )
        assert resume.status_code == 200
        assert resume.json()["status"] == "resumed"
        assert resume.json()["audit_event"]["event_type"] == "source_resumed"
        assert any(
            tenant == "driftline-demo" and current_id == source_id
            for tenant, current_id, _definition in source.scheduler_source_entries()
        )
        assert [event["event_type"] for event in persistence._tenant_audit_memory] == [
            "source_paused",
            "source_resumed",
        ]
    finally:
        source._CUSTOM_SOURCE_DEFINITIONS.clear()
        persistence._tenant_audit_memory.clear()


def test_source_lifecycle_rolls_back_when_audit_persistence_fails(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    persistence._tenant_audit_memory.clear()
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY", "false")
    monkeypatch.delenv("DRIFTLINE_TENANT_SIGNING_SECRET_PREFIX", raising=False)
    monkeypatch.delenv("DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS", raising=False)
    secret = "source-lifecycle-rollback-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
    source_id = "custom/lifecycle-rollback"
    source.register_operator_source(
        source_id=source_id,
        name="Lifecycle rollback",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id="driftline-demo",
    )
    token = hmac.new(
        secret.encode(),
        f"source-lifecycle:{source_id}:pause:Signed operator".encode(),
        hashlib.sha256,
    ).hexdigest()

    def fail_audit(_payload: dict[str, object]) -> None:
        raise RuntimeError("audit-store-unavailable")

    monkeypatch.setattr(api, "persist_tenant_audit_event", fail_audit)
    try:
        response = client.post(
            f"/api/operator/sources/{source_id}/lifecycle",
            json={
                "enabled": False,
                "reason": "Temporary source outage.",
                "operator": "Signed operator",
                "tenant_id": "driftline-demo",
                "approval_token": token,
            },
        )
        assert response.status_code == 503
        assert "no lifecycle change was retained" in response.json()["detail"]
        restored = source.source_definition(
            source_id, "driftline-demo", include_disabled=True
        )
        assert restored is not None
        assert restored["enabled"] == "true"
        assert any(
            tenant == "driftline-demo" and current_id == source_id
            for tenant, current_id, _definition in source.scheduler_source_entries()
        )
        assert persistence._tenant_audit_memory == []
    finally:
        source._CUSTOM_SOURCE_DEFINITIONS.clear()
        persistence._tenant_audit_memory.clear()


def test_public_source_onboarding_establishes_bounded_baseline(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", "test-only-secret")
    baseline = {
        "status": "baseline_established",
        "change_detected": False,
        "data_mode": "operator_registered_public",
    }
    monkeypatch.setattr(api, "inspect_allowlisted_source", lambda *args, **kwargs: baseline)
    source_id = "custom/live-pricing"
    token = hmac.new(
        b"test-only-secret",
        f"source-onboarding:{source_id}:Signed operator".encode(),
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/operator/sources",
        json={
            "source_id": source_id,
            "name": "Live pricing",
            "category": "Competitor pricing",
            "change_type": "Pricing move",
            "url": "https://example.com/pricing",
            "owner": "Product Marketing",
            "cadence": "24h",
            "freshness_sla_hours": 48,
            "parser": "html",
            "registered_by": "Signed operator",
            "approval_token": token,
        },
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert response.status_code == 200
    assert response.json()["baseline"] == baseline
    assert "first baseline was established" in response.json()["next_step"]


def test_manual_monitor_job_requires_signed_operator(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setattr(
        api,
        "_start_job",
        lambda **kwargs: JobState(job_id="job-monitor-test"),
    )
    denied = client.post(
        "/api/jobs/demo",
        json={"run_mode": "monitor", "source_id": "public/pricing"},
    )
    assert denied.status_code == 401

    operator = "Signed operator"
    message = f"monitor:public/pricing:{operator}".encode()
    token = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    allowed = client.post(
        "/api/jobs/demo",
        json={
            "run_mode": "monitor",
            "source_id": "public/pricing",
            "operator": operator,
            "approval_token": token,
        },
    )
    assert allowed.status_code == 200


def test_public_demo_job_uses_fixed_query_and_identity(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_start_job(**kwargs):
        captured.update(kwargs)
        return JobState(job_id="job-public-fixed-query")

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    response = client.post(
        "/api/jobs/demo",
        json={
            "query": "private customer note that must never reach the demo agent",
            "user_id": "untrusted-public-user",
            "source_id": "public/pricing",
        },
    )

    assert response.status_code == 200
    assert captured["user_id"] == "public-demo"
    assert "private customer note" not in str(captured["query"])
    assert "allowlisted public/pricing change" in str(captured["query"])


def test_public_demo_job_reuses_inflight_source_job(monkeypatch) -> None:
    """A public refresh must not enqueue duplicate Gemini work."""
    source_id = "public/terms"
    existing = JobState(
        job_id="job-public-inflight",
        status="running",
        run_mode="demo",
        source_id=source_id,
    )
    api._set_job(existing)
    monkeypatch.setattr(api, "list_jobs", lambda limit=50: [])
    started = False

    def fake_start_job(**kwargs):
        nonlocal started
        started = True
        return JobState(job_id="job-should-not-start")

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    response = client.post("/api/jobs/demo", json={"source_id": source_id})

    with api._jobs_lock:
        api._jobs.pop(existing.job_id, None)
    assert response.status_code == 200
    assert response.json()["job_id"] == existing.job_id
    assert response.json()["deduplicated"] is True
    assert started is False


def test_signed_monitor_job_carries_authenticated_tenant(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "tenant-monitor-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    captured: dict[str, object] = {}

    def fake_start_job(**kwargs):
        captured.update(kwargs)
        return JobState(job_id="job-tenant-monitor", tenant_id=kwargs["tenant_id"])

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    actor = "Tenant monitor operator"
    token = hmac.new(
        secret.encode(), f"monitor:public/pricing:{actor}".encode(), hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/jobs/demo",
        json={
            "run_mode": "monitor",
            "source_id": "public/pricing",
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert captured["tenant_id"] == "driftline-demo"
    assert captured["source_id"] == "public/pricing"
    assert response.json()["tenant_id"] == "driftline-demo"


def test_signed_registered_source_job_uses_monitor_lane(monkeypatch) -> None:
    """The operator console must route dynamic sources to production monitoring."""
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/operator-pricing",
        name="Operator pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id="driftline-demo",
    )
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", "registered-source-secret")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    captured: dict[str, object] = {}

    def fake_start_job(**kwargs):
        captured.update(kwargs)
        return JobState(job_id="job-registered-source", tenant_id=kwargs["tenant_id"])

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    actor = "Registered source operator"
    token = hmac.new(
        b"registered-source-secret",
        f"monitor:custom/operator-pricing:{actor}".encode(),
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/jobs/demo",
        json={
            "run_mode": "monitor",
            "source_id": "custom/operator-pricing",
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": token,
        },
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert response.status_code == 200
    assert captured["run_mode"] == "monitor"
    assert captured["source_id"] == "custom/operator-pricing"
    assert captured["tenant_id"] == "driftline-demo"


def test_signed_failed_tenant_job_retry_preserves_scope_and_is_idempotent(monkeypatch) -> None:
    """Retries must be tenant-bound and never create duplicate successors."""
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "retry-route-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    with api._agent_call_lock:
        api._tenant_agent_call_times.clear()

    failed_job = JobState(
        job_id="job-failed-retry-route",
        status="failed",
        query='Monitor exact source_id "public/pricing".',
        user_id="signed-operator",
        tenant_id="driftline-demo",
        run_mode="monitor",
        source_id="public/pricing",
    )
    api._set_job(failed_job)
    captured: dict[str, object] = {}

    def fake_start_job(**kwargs):
        captured.update(kwargs)
        successor = JobState(
            job_id="job-retry-successor",
            tenant_id=kwargs["tenant_id"],
            run_mode=kwargs["run_mode"],
            source_id=kwargs["source_id"],
            retry_of=kwargs["retry_of"],
        )
        api._set_job(successor)
        return successor

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    actor = "Retry route operator"
    token = hmac.new(
        secret.encode(),
        f"job-retry:{failed_job.job_id}:{actor}".encode(),
        hashlib.sha256,
    ).hexdigest()
    payload = {
        "operator": actor,
        "tenant_id": "driftline-demo",
        "approval_token": token,
    }

    first = client.post(f"/api/jobs/{failed_job.job_id}/retry", json=payload)
    second = client.post(f"/api/jobs/{failed_job.job_id}/retry", json=payload)

    assert first.status_code == 200
    assert first.json()["status"] == "queued"
    assert second.status_code == 200
    assert second.json()["status"] == "already_queued"
    assert captured["query"] == failed_job.query
    assert captured["tenant_id"] == failed_job.tenant_id
    assert captured["source_id"] == failed_job.source_id
    assert captured["run_mode"] == failed_job.run_mode
    assert captured["retry_of"] == failed_job.job_id


def test_signed_tenant_demo_job_carries_authenticated_tenant(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "tenant-demo-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    captured: dict[str, object] = {}

    def fake_start_job(**kwargs):
        captured.update(kwargs)
        return JobState(job_id="job-tenant-demo", tenant_id=kwargs["tenant_id"])

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    actor = "Tenant demo operator"
    token = hmac.new(
        secret.encode(),
        f"tenant-demo:public/pricing:{actor}".encode(),
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/jobs/demo",
        json={
            "run_mode": "tenant_demo",
            "source_id": "public/pricing",
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert captured["tenant_id"] == "driftline-demo"
    assert captured["run_mode"] == "tenant_demo"
    assert response.json()["tenant_id"] == "driftline-demo"


def test_signed_operator_cannot_approve_another_tenant_workflow(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "cross-tenant-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "other-acme")
    state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(state)
    token = hmac.new(
        secret.encode(), f"{state.workflow_id}:Other operator".encode(), hashlib.sha256
    ).hexdigest()

    response = client.post(
        f"/api/workflows/{state.workflow_id}/approve",
        json={
            "approver": "Other operator",
            "approval_mode": "signed",
            "tenant_id": "other-acme",
            "approval_token": token,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "workflow_tenant_mismatch"


def test_tenant_bound_reads_require_matching_signed_identity(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "tenant-read-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo,other-acme")
    state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(state)
    job = JobState(job_id="job-tenant-read", tenant_id="driftline-demo")
    with api._jobs_lock:
        api._jobs[job.job_id] = job

    public = client.get(f"/api/workflows/{state.workflow_id}")
    assert public.status_code == 403
    assert public.json()["detail"] == "Tenant-scoped resource requires signed approval"
    action_public = client.post(
        f"/api/workflows/{state.workflow_id}/actions/action-1/claim",
        json={"actor": "Action actor"},
    )
    assert action_public.status_code == 403
    assert action_public.json()["detail"] == "Tenant-scoped workflow requires signed approval"
    assert client.get("/api/jobs/job-tenant-read").status_code == 403
    assert all(item["job_id"] != job.job_id for item in client.get("/api/jobs").json()["jobs"])
    assert state.workflow_id not in str(client.get("/api/memory/summary").json())
    assert state.workflow_id not in str(client.get("/api/ops/summary").json())
    public_value = client.get("/api/ops/value-proof").json()

    actor = "Tenant reader"
    token = hmac.new(
        secret.encode(), f"{state.workflow_id}:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    signed_params = {
        "operator": actor,
        "tenant_id": "driftline-demo",
        "approval_token": token,
    }
    assert client.get(f"/api/workflows/{state.workflow_id}", params=signed_params).status_code == 200
    assert client.get(
        f"/api/workflows/{state.workflow_id}/actions", params=signed_params
    ).status_code == 200
    assert client.get(
        f"/api/workflows/{state.workflow_id}/scenarios", params=signed_params
    ).status_code == 200
    assert client.get(
        f"/api/workflows/{state.workflow_id}/packet", params=signed_params
    ).status_code == 200
    memory_token = hmac.new(
        secret.encode(), f"memory:summary:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    signed_memory = client.get(
        "/api/memory/summary",
        params={
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": memory_token,
        },
    )
    assert signed_memory.status_code == 200
    assert state.workflow_id in str(signed_memory.json())
    value_token = hmac.new(
        secret.encode(), f"ops:value-proof:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    signed_value = client.get(
        "/api/ops/value-proof",
        params={
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": value_token,
        },
    )
    assert signed_value.status_code == 200
    signed_value_payload = signed_value.json()
    assert signed_value_payload["scope"] == "observed_tenant_records"
    assert signed_value_payload["observed"]["tenant_scoped_workflows"] >= 1
    assert signed_value_payload["observed"]["tenantless_workflows"] == 0
    assert (
        signed_value_payload["observed"]["workflows"]
        >= public_value["observed"]["workflows"] + 1
    )
    jobs_token = hmac.new(
        secret.encode(), f"jobs:list:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    signed_jobs = client.get(
        "/api/jobs",
        params={**signed_params, "approval_token": jobs_token},
    )
    assert signed_jobs.status_code == 200
    assert all(item.get("tenant_id") == "driftline-demo" for item in signed_jobs.json()["jobs"])

    wrong_token = hmac.new(
        secret.encode(), f"{state.workflow_id}:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    wrong = client.get(
        f"/api/workflows/{state.workflow_id}",
        params={
            "operator": actor,
            "tenant_id": "other-acme",
            "approval_token": wrong_token,
        },
    )
    assert wrong.status_code == 403
    assert wrong.json()["detail"] == "workflow_tenant_mismatch"


def test_rate_limits_are_isolated_per_tenant(monkeypatch) -> None:
    monkeypatch.setattr(api, "AGENT_MAX_CALLS", 1)
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 1)
    monkeypatch.setattr(api, "CONNECTOR_MAX_CALLS", 1)
    api._tenant_agent_call_times.clear()
    api._tenant_demo_mutation_times.clear()
    api._tenant_connector_call_times.clear()

    assert api._reserve_agent_call("tenant-a") is True
    assert api._reserve_agent_call("tenant-a") is False
    assert api._reserve_agent_call("tenant-b") is True
    assert api._reserve_demo_mutation("tenant-a") is True
    assert api._reserve_demo_mutation("tenant-a") is False
    assert api._reserve_demo_mutation("tenant-b") is True
    assert api._reserve_connector_call("tenant-a") is True
    assert api._reserve_connector_call("tenant-a") is False
    assert api._reserve_connector_call("tenant-b") is True


def test_public_agent_quota_is_separate_from_signed_tenant_quota(monkeypatch) -> None:
    monkeypatch.setattr(api, "AGENT_MAX_CALLS", 1)
    monkeypatch.setattr(api, "PUBLIC_AGENT_MAX_CALLS", 2)
    api._agent_call_times.clear()
    api._tenant_agent_call_times.clear()

    assert api._reserve_agent_call() is True
    assert api._reserve_agent_call() is True
    assert api._reserve_agent_call() is False
    assert api._reserve_agent_call("tenant-a") is True


def test_product_council_quota_reserves_all_six_slots_or_none(monkeypatch) -> None:
    monkeypatch.setattr(api, "PUBLIC_AGENT_MAX_CALLS", 20)
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._agent_call_times.extend([api.monotonic()] * 18)

    assert api._reserve_product_council_calls() is False
    assert len(api._agent_call_times) == 18
    with api._agent_call_lock:
        api._agent_call_times.clear()


def test_demo_approval_and_undo_round_trip() -> None:
    started = client.post("/api/workflows/demo")
    assert started.status_code == 200
    workflow_id = started.json()["workflow_id"]

    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "complete"
    assert approved.json()["action_record"]["operational_status"] == "not_configured"
    assert approved.json()["action_record"]["jira_status"] == "prepared_only"

    undone = client.post(
        f"/api/workflows/{workflow_id}/undo",
        json={"actor": "Demo operator"},
    )
    assert undone.status_code == 200
    assert undone.json()["status"] == "needs_approval"
    assert undone.json()["action_record"]["operational_status"] == "not_configured"
    assert undone.json()["action_record"]["jira_status"] == "prepared_only"


def test_approval_claim_blocks_concurrent_undo(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    original = api._connector_handoff_info

    def inspect_claim(state, identity, *, reverse=False):
        assert state.status.value == "approval_executing"
        raced = client.post(
            f"/api/workflows/{workflow_id}/undo",
            json={"actor": "Second operator"},
        )
        assert raced.status_code == 409
        return original(state, identity, reverse=reverse)

    monkeypatch.setattr(api, "_connector_handoff_info", inspect_claim)
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "complete"


def test_reversal_claim_blocks_concurrent_reapproval(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    assert approved.status_code == 200
    original = api._connector_handoff_info

    def inspect_claim(state, identity, *, reverse=False):
        assert reverse is True
        assert state.status.value == "reversal_executing"
        raced = client.post(
            f"/api/workflows/{workflow_id}/approve",
            json={"approver": "Second operator"},
        )
        assert raced.status_code == 409
        return original(state, identity, reverse=reverse)

    monkeypatch.setattr(api, "_connector_handoff_info", inspect_claim)
    undone = client.post(
        f"/api/workflows/{workflow_id}/undo",
        json={"actor": "Demo operator"},
    )

    assert undone.status_code == 200
    assert undone.json()["status"] == "needs_approval"


def test_interrupted_approval_is_durable_and_reconciles_same_operation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    workflow_id = client.post("/api/workflows/demo").json()["workflow_id"]
    original = api.persist_action_artifact
    calls = 0

    def fail_once(state, *, kind):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("simulated storage interruption")
        return original(state, kind=kind)

    monkeypatch.setattr(api, "persist_action_artifact", fail_once)
    interrupted = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )

    assert interrupted.status_code == 200
    payload = interrupted.json()
    assert payload["status"] == "reconciliation_required"
    assert payload["operation"]["status"] == "reconciliation_required"
    assert payload["operation"]["attempts"] == 1
    operation_id = payload["operation"]["operation_id"]
    assert payload["action_record"]["reconciliation_required"] is True

    conflicting = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Second operator"},
    )
    assert conflicting.status_code == 409

    reconciled = client.post(
        f"/api/workflows/{workflow_id}/reconcile",
        json={"actor": "Demo operator"},
    )
    assert reconciled.status_code == 200
    recovered = reconciled.json()
    assert recovered["status"] == "complete"
    assert recovered["operation"]["operation_id"] == operation_id
    assert recovered["operation"]["generation"] == 1
    assert recovered["operation"]["attempts"] == 2
    assert recovered["operation"]["status"] == "completed"
    assert recovered["action_record"]["reconciliation_required"] is False


def test_hard_crash_claim_requires_expired_lease_then_reconciles_same_operation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    workflow_id = client.post("/api/workflows/demo").json()["workflow_id"]
    original = api.persist_action_artifact

    def terminate_after_claim(_state, *, kind):
        raise SystemExit(f"simulated hard termination during {kind}")

    monkeypatch.setattr(api, "persist_action_artifact", terminate_after_claim)
    with pytest.raises(SystemExit, match="simulated hard termination"):
        api.approve(workflow_id, api.ApprovalRequest(approver="Demo operator"))

    orphaned = api._resolve_workflow(workflow_id)
    assert orphaned.status == api.WorkflowStatus.APPROVAL_EXECUTING
    operation_id = orphaned.operation["operation_id"]
    assert orphaned.operation["lease_expires_at"]

    active_retry = client.post(
        f"/api/workflows/{workflow_id}/reconcile",
        json={"actor": "Demo operator"},
    )
    assert active_retry.status_code == 409
    assert "still active" in active_retry.json()["detail"]

    monkeypatch.setattr(api, "persist_action_artifact", original)
    monkeypatch.setattr(api, "_operation_lease_expired", lambda _operation: True)
    recovered = client.post(
        f"/api/workflows/{workflow_id}/reconcile",
        json={"actor": "Demo operator"},
    )

    assert recovered.status_code == 200
    payload = recovered.json()
    assert payload["status"] == "complete"
    assert payload["operation"]["operation_id"] == operation_id
    assert payload["operation"]["attempts"] == 2
    assert payload["operation"]["status"] == "completed"
    assert any(
        event.get("outcome") == "expired_claim_recovered"
        for event in payload["events"]
    )


def test_interrupted_reversal_reconciles_back_to_human_gate(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    workflow_id = client.post("/api/workflows/demo").json()["workflow_id"]
    assert client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    ).status_code == 200
    original = api.persist_operational_output
    calls = 0

    def fail_once(state, *, kind):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("simulated output interruption")
        return original(state, kind=kind)

    monkeypatch.setattr(api, "persist_operational_output", fail_once)
    interrupted = client.post(
        f"/api/workflows/{workflow_id}/undo",
        json={"actor": "Demo operator"},
    )
    assert interrupted.status_code == 200
    assert interrupted.json()["status"] == "reconciliation_required"
    operation_id = interrupted.json()["operation"]["operation_id"]

    reconciled = client.post(
        f"/api/workflows/{workflow_id}/reconcile",
        json={"actor": "Demo operator"},
    )
    assert reconciled.status_code == 200
    assert reconciled.json()["status"] == "needs_approval"
    assert reconciled.json()["operation"]["operation_id"] == operation_id


def test_configured_reconciliation_rejects_public_demo_identity(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    state = api.workflow_store.start_demo()
    state.status = api.WorkflowStatus.RECONCILIATION_REQUIRED
    state.operation = {
        "operation_id": "op-configured-test",
        "kind": "approval",
        "status": "reconciliation_required",
        "generation": 1,
        "attempts": 1,
        "scope": "configured",
    }
    state.action_record = {"external_write": True}
    api.workflow_store.restore(state)

    response = client.post(
        f"/api/workflows/{state.workflow_id}/reconcile",
        json={"actor": "Demo operator"},
    )

    assert response.status_code == 409
    assert "Signed approval is required" in response.json()["detail"]


def test_reconciliation_requires_named_human(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    state = api.workflow_store.start_demo()
    state.status = api.WorkflowStatus.RECONCILIATION_REQUIRED
    state.operation = {
        "operation_id": "op-named-human",
        "kind": "approval",
        "status": "reconciliation_required",
        "generation": 1,
        "attempts": 1,
        "scope": "public_demo",
    }
    api.workflow_store.restore(state)

    response = client.post(
        f"/api/workflows/{state.workflow_id}/reconcile",
        json={"actor": "system"},
    )

    assert response.status_code == 400
    assert "named human" in response.json()["detail"]


def test_oidc_reconciliation_binds_audit_actor_to_verified_email(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "mode": "signed",
            "identity": "google_oidc_operator",
            "scope": "configured",
            "email": "real.operator@example.com",
            "tenant_id": "driftline-demo",
            "role": "operator",
        },
    )
    monkeypatch.setattr(api, "_connector_handoff_info", lambda *_args, **_kwargs: {})
    state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    state.status = api.WorkflowStatus.RECONCILIATION_REQUIRED
    state.operation = {
        "operation_id": "op-oidc-attribution",
        "kind": "approval",
        "status": "reconciliation_required",
        "generation": 1,
        "attempts": 1,
        "scope": "configured",
    }
    api.workflow_store.restore(state)

    response = client.post(
        f"/api/workflows/{state.workflow_id}/reconcile",
        json={
            "actor": "Impersonated executive",
            "approval_mode": "signed",
            "identity_token": "verified-elsewhere",
            "tenant_id": "driftline-demo",
        },
    )

    assert response.status_code == 200
    assert response.json()["operation"]["reconciled_by"] == (
        "real.operator@example.com"
    )


def test_first_attempt_connector_failure_requires_reconciliation(monkeypatch) -> None:
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda _tenant_id=None: True)
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "mode": "signed",
            "identity": "google_oidc_operator",
            "scope": "configured",
            "email": "operator@example.com",
            "tenant_id": "driftline-demo",
            "role": "operator",
        },
    )
    monkeypatch.setattr(
        api,
        "_connector_handoff_info",
        lambda *_args, **_kwargs: {
            "jira_status": "failed",
            "jira_external_write": False,
        },
    )
    workflow_id = api.workflow_store.start_demo(tenant_id="driftline-demo").workflow_id

    response = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Impersonated executive",
            "approval_mode": "signed",
            "identity_token": "verified-elsewhere",
            "tenant_id": "driftline-demo",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "reconciliation_required"
    assert payload["operation"]["status"] == "reconciliation_required"
    assert payload["approval"]["approver"] == "operator@example.com"
    assert not any(
        event.get("outcome") == "operation_completed" for event in payload["events"]
    )


def test_value_proof_counts_reopened_workflows_after_undo() -> None:
    before = client.get("/api/ops/value-proof").json()["observed"]
    started = client.post("/api/workflows/demo")
    assert started.status_code == 200
    workflow_id = started.json()["workflow_id"]

    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    undone = client.post(
        f"/api/workflows/{workflow_id}/undo",
        json={"actor": "Demo operator"},
    )
    assert undone.status_code == 200
    assert any(
        event.get("outcome") == "decision_reopened"
        for event in undone.json()["events"]
    )

    after = client.get("/api/ops/value-proof").json()["observed"]
    assert after["workflows_reversed_or_reopened"] >= (
        before["workflows_reversed_or_reopened"] + 1
    )
    assert after["action_items_completed"] == before["action_items_completed"]


def test_value_proof_retains_historical_owner_closure_after_reversal(monkeypatch) -> None:
    # Keep this lifecycle assertion independent from the suite-wide public
    # mutation quota; the production quota itself is covered separately.
    monkeypatch.setattr(api, "_reserve_demo_mutation", lambda *_args: True)
    before = client.get("/api/ops/value-proof").json()["observed"]
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator", "decision": "grandfather_existing_customers"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]
    claimed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    assert claimed.status_code == 200
    completed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )
    assert completed.status_code == 200

    after_completion = client.get("/api/ops/value-proof").json()["observed"]
    assert after_completion["action_items_completed_historically"] >= (
        before["action_items_completed_historically"] + 1
    )
    assert after_completion["owner_action_cycle_seconds"]["sample_count"] >= (
        before["owner_action_cycle_seconds"]["sample_count"] + 1
    )
    undone = client.post(
        f"/api/workflows/{workflow_id}/undo",
        json={"actor": "Demo operator"},
    )
    assert undone.status_code == 200
    reversed_item = next(
        item for item in undone.json()["action_items"] if item["item_id"] == item_id
    )
    assert reversed_item["status"] == "reversed"
    assert reversed_item["completed_at"]

    after_reversal = client.get("/api/ops/value-proof").json()["observed"]
    assert after_reversal["action_items_completed"] == before["action_items_completed"]
    assert after_reversal["action_items_completed_historically"] >= (
        before["action_items_completed_historically"] + 1
    )


def test_demo_dismissal_records_reason_without_creating_work() -> None:
    started = client.post("/api/workflows/demo")
    assert started.status_code == 200
    workflow_id = started.json()["workflow_id"]

    dismissed = client.post(
        f"/api/workflows/{workflow_id}/dismiss",
        json={
            "actor": "Demo operator",
            "reason": "Not material for the current segment",
        },
    )

    assert dismissed.status_code == 200
    payload = dismissed.json()
    assert payload["status"] == "dismissed"
    assert payload["approval"]["decision"] == "dismissed"
    assert payload["approval"]["reason"] == "Not material for the current segment"
    assert payload["change_card"]["closure"]["state"] == "dismissed"
    assert payload["action_items"] == []

    packet = client.get(f"/api/workflows/{workflow_id}/packet")
    assert packet.status_code == 200
    assert "Decision reason: Not material for the current segment" in packet.text


def test_same_demo_snapshot_exposes_stable_change_card_identity() -> None:
    first = client.post("/api/workflows/demo").json()
    second = client.post("/api/workflows/demo").json()
    assert first["change_card"]["change_card_id"] == second["change_card"]["change_card_id"]

    approved = client.post(
        f"/api/workflows/{first['workflow_id']}/approve",
        json={"approver": "Demo operator"},
    )
    assert approved.status_code == 200
    assert approved.json()["action_record"]["change_card_id"] == first["change_card"]["change_card_id"]


def test_demo_approval_never_calls_configured_connectors(monkeypatch) -> None:
    """Public named actors receive a packet even if connector env is present."""
    calls: list[str] = []

    def forbidden(state):
        calls.append("write")
        raise AssertionError("demo approval crossed the external-write boundary")

    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_CONFLUENCE_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_SLACK_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_GITHUB_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "_CONNECTOR_HANDOFFS",
        tuple((name, forbidden, forbidden) for name, _, _ in api._CONNECTOR_HANDOFFS),
    )

    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Public demo reviewer"},
    )

    assert approved.status_code == 200
    action = approved.json()["action_record"]
    assert not calls
    assert action["external_write"] is False
    assert action["external_write_authorized"] is False
    assert all(
        action[f"{name}_status"] == "prepared_only"
        for name in ("jira", "confluence", "slack", "github")
    )


def test_signed_approval_can_cross_connector_boundary_when_enabled(monkeypatch) -> None:
    calls: list[str] = []
    persisted_packets: list[str] = []

    def create(state):
        calls.append("write")
        return {"jira_status": "created", "external_write": True}

    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setattr(
        api,
        "_CONNECTOR_HANDOFFS",
        (("jira", create, create),),
    )
    monkeypatch.setattr(
        api,
        "persist_action_artifact",
        lambda state, kind: (
            persisted_packets.append(api.packet_markdown(state))
            or {"storage_status": "not_configured"}
        ),
    )
    tenant_state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(tenant_state)
    workflow_id = tenant_state.workflow_id
    actor = "Signed operator"
    token = hmac.new(
        secret.encode(), f"{workflow_id}:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": actor,
            "approval_mode": "signed",
            "approval_token": token,
        },
    )

    assert approved.status_code == 200
    assert calls == ["write"]
    assert approved.json()["action_record"]["external_write_authorized"] is True
    assert approved.json()["action_record"]["external_systems_changed"] is True
    assert "External systems changed: **Yes** (configured connector lane)" in persisted_packets[0]
    assert "Jira: status `created` · external write `yes`" in persisted_packets[0]


def test_configured_handoff_only_runs_mapped_connectors_and_names_writes(monkeypatch) -> None:
    calls: list[str] = []

    def make_operation(name: str):
        def operation(_state):
            calls.append(name)
            return {f"{name}_status": "created", "external_write": True}

        return operation

    monkeypatch.setattr(
        api,
        "_CONNECTOR_HANDOFFS",
        tuple(
            (name, make_operation(name), make_operation(name))
            for name, _, _ in api._CONNECTOR_HANDOFFS
        ),
    )
    state = api.workflow_store.start_demo()

    result = api._connector_handoff_info(
        state,
        {"scope": "configured", "tenant_id": "driftline-demo"},
    )

    assert calls == ["jira", "confluence", "slack"]
    assert result["jira_external_write"] is True
    assert result["confluence_external_write"] is True
    assert result["slack_external_write"] is True
    assert result["github_status"] == "not_selected"
    assert result["github_external_write"] is False
    assert result["external_write"] is True


def test_legacy_connector_write_is_still_reversed_when_target_is_not_mapped(monkeypatch) -> None:
    calls: list[str] = []

    def reverse_github(_state):
        calls.append("github")
        return {"github_status": "reversed", "external_write": True}

    monkeypatch.setattr(
        api,
        "_CONNECTOR_HANDOFFS",
        (("github", lambda _state: {}, reverse_github),),
    )
    state = api.workflow_store.start_demo()
    state.action_record = {
        "github_status": "created",
        "github_external_write": True,
    }

    result = api._connector_handoff_info(
        state,
        {"scope": "configured", "tenant_id": "driftline-demo"},
        reverse=True,
    )

    assert calls == ["github"]
    assert result["github_status"] == "reversed"
    assert result["github_external_write"] is True
    assert result["external_write"] is True


def test_reconciliation_reuses_confirmed_reversal_without_duplicate_write(
    monkeypatch,
) -> None:
    def duplicate_reversal(_state):
        raise AssertionError("confirmed reversal must not run twice")

    monkeypatch.setattr(
        api,
        "_CONNECTOR_HANDOFFS",
        (("jira", lambda _state: {}, duplicate_reversal),),
    )
    state = api.workflow_store.start_demo()
    state.action_record = {
        "jira_status": "reversed",
        "jira_external_write": True,
        "jira_issue_key": "KAN-19",
    }

    result = api._connector_handoff_info(
        state,
        {"scope": "configured", "tenant_id": "driftline-demo"},
        reverse=True,
    )

    assert result["jira_status"] == "reversed"
    assert result["jira_issue_key"] == "KAN-19"
    assert result["external_write"] is True


def test_reconciliation_keeps_outstanding_connector_failure_recoverable(
    monkeypatch,
) -> None:
    state = api.workflow_store.start_demo()
    state.operation = {"attempts": 2}
    monkeypatch.setattr(
        api,
        "_connector_handoff_info",
        lambda *_args, **_kwargs: {
            "jira_status": "failed",
            "jira_external_write": False,
        },
    )
    monkeypatch.setattr(
        api,
        "persist_action_artifact",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("artifact must wait for connector recovery")
        ),
    )

    with pytest.raises(api.ConnectorError, match="remains unavailable"):
        api._execute_claimed_side_effects(
            state,
            {"scope": "configured", "tenant_id": "driftline-demo"},
            reverse=False,
        )


def test_partial_connector_results_survive_before_reconciliation(monkeypatch) -> None:
    state = api.workflow_store.start_demo()
    state.operation = {"attempts": 1}
    state.action_record = {
        "jira_status": "created",
        "jira_external_write": True,
    }
    monkeypatch.setattr(
        api,
        "_connector_handoff_info",
        lambda *_args, **_kwargs: {
            "jira_status": "reversed",
            "jira_external_write": True,
            "jira_issue_key": "KAN-19",
            "confluence_status": "failed",
            "confluence_external_write": False,
            "external_write": True,
        },
    )

    with pytest.raises(api.ConnectorError, match="remains unavailable"):
        api._execute_claimed_side_effects(
            state,
            {"scope": "configured", "tenant_id": "driftline-demo"},
            reverse=True,
        )

    assert state.action_record["jira_status"] == "reversed"
    assert state.action_record["jira_issue_key"] == "KAN-19"
    assert state.action_record["jira_external_write"] is True
    assert state.action_record["confluence_status"] == "failed"
    assert state.action_record["external_systems_changed"] is True


def test_source_history_endpoint_is_explicitly_append_only() -> None:
    response = client.get("/api/sources/public/pricing/history")
    assert response.status_code == 200
    assert response.json()["append_only"] is True
    assert "memory" in response.json()


def test_memory_summary_is_ui_ready_and_bounded() -> None:
    response = client.get("/api/memory/summary?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["append_only"] is True
    assert "change_genomes" in payload
    assert set(payload["work_summary"]) >= {
        "unresolved",
        "reversed",
        "unresolved_count",
        "reversed_count",
    }


def test_competitor_source_builds_offering_impact_graph_and_handoffs() -> None:
    started = client.post("/api/workflows/demo?source_id=competitor/pricing")
    assert started.status_code == 200
    payload = started.json()
    assert payload["evidence"]["source_id"] == "competitor/pricing"
    assert payload["impact_graph"]["summary"]["category"] == "Competitor pricing"
    assert "Comparison map" in {item["name"] for item in payload["impacts"]}
    assert {item["system"] for item in payload["integration_targets"]} >= {
        "Jira",
        "Confluence",
        "Slack",
    }
    approved = client.post(
        f"/api/workflows/{payload['workflow_id']}/approve",
        json={
            "approver": "Demo operator",
            "decision": "approve_competitive_response",
            "artifact_decisions": {
                item["name"]: "packet" if item["risk"] == "high" else "owner_review"
                for item in payload["impacts"]
            },
        },
    )
    assert approved.status_code == 200
    assert approved.json()["approval"]["decision"] == "approve_competitive_response"


def test_custom_copilot_routing_keeps_reviewed_option_and_audit_reason() -> None:
    state = api.workflow_store.start_demo()
    copilot = fallback_copilot(state)
    state.agent_trace = {
        "decision_copilot": {
            **copilot.model_dump(),
            "policy_review": red_team_review(copilot, state).model_dump(),
        }
    }
    api.persist_workflow(state)
    option = copilot.options[0]
    custom = dict(option.artifact_decisions)
    custom["Renewal playbook"] = "owner_review"

    response = client.post(
        f"/api/workflows/{state.workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": option.workflow_decision,
            "artifact_decisions": custom,
            "copilot_option_id": option.option_id,
            "copilot_artifact_override": True,
            "copilot_override_reason": "Narrow renewal work to owner review",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval"]["copilot_option_id"] == option.option_id
    assert payload["approval"]["copilot_artifact_override"] is True
    assert payload["approval"]["copilot_override_reason"] == (
        "Narrow renewal work to owner review"
    )
    recorded = next(
        event for event in payload["events"] if event["outcome"] == "approval_recorded"
    )
    assert recorded["copilot_artifact_override"] is True
    assert recorded["override_reason"] == "Narrow renewal work to owner review"


def test_approved_action_item_can_be_claimed_and_completed_by_same_human() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    actions = approved.json()["action_items"]
    assert len(actions) == 4
    item_id = actions[0]["item_id"]

    claimed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    assert claimed.status_code == 200
    assert (
        next(
            item
            for item in claimed.json()["action_items"]
            if item["item_id"] == item_id
        )["status"]
        == "claimed"
    )

    wrong_actor = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Taylor Lee"},
    )
    assert wrong_actor.status_code == 409

    completed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )
    assert completed.status_code == 200
    assert (
        next(
            item
            for item in completed.json()["action_items"]
            if item["item_id"] == item_id
        )["status"]
        == "completed"
    )

    duplicate_complete = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )
    assert duplicate_complete.status_code == 200


def test_action_claim_is_idempotent_for_the_same_human() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]

    first = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    event_count = len(first.json()["events"])
    duplicate = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert len(duplicate.json()["events"]) == event_count
    assert duplicate.json()["action_items"][0]["attempts"] == 1


def test_idempotent_action_retry_does_not_consume_mutation_quota(monkeypatch) -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]
    reservations: list[str | None] = []

    def reserve(tenant_id: str | None = None) -> bool:
        reservations.append(tenant_id)
        return True

    monkeypatch.setattr(api, "_reserve_demo_mutation", reserve)
    first = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    duplicate = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert len(reservations) == 1


def test_failed_action_can_be_retried_and_repeated_retry_is_idempotent() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]
    claimed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    assert claimed.status_code == 200

    failed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/fail",
        json={"actor": "Alex Kim", "reason": "Owner review timed out"},
    )
    assert failed.status_code == 200
    retried = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/retry",
        json={"actor": "Alex Kim"},
    )
    duplicate_retry = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/retry",
        json={"actor": "Alex Kim"},
    )

    assert retried.status_code == 200
    assert duplicate_retry.status_code == 200
    item = duplicate_retry.json()["action_items"][0]
    assert item["status"] == "queued"
    assert item["retry_count"] == 1


def test_completed_action_can_be_reversed_idempotently() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]
    client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )

    reversed_once = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/reverse",
        json={"actor": "Alex Kim"},
    )
    reversed_twice = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/reverse",
        json={"actor": "Alex Kim"},
    )

    assert reversed_once.status_code == 200
    assert reversed_twice.status_code == 200
    assert reversed_twice.json()["action_items"][0]["status"] == "reversed"


def test_live_agent_query_is_bounded_before_execution() -> None:
    response = client.post("/api/agent/run", json={"query": "x" * 2001})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_public_live_agent_route_uses_fixed_allowlisted_input(monkeypatch) -> None:
    captured: dict[str, str] = {}

    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        captured["query"] = query
        captured["user_id"] = user_id
        return {"status": "ok"}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post(
        "/api/agent/run",
        json={
            "query": "Inspect the pricing change",
            "user_id": "operator-1",
            "source_id": "public/pricing",
        },
    )

    assert response.status_code == 200
    assert captured["user_id"] == "public-demo"
    assert captured["query"] == (
        "Inspect the allowlisted public/pricing change, verify the evidence, "
        "map affected artifacts, and stop at the human approval gate."
    )


@pytest.mark.asyncio
async def test_live_agent_route_propagates_signed_tenant(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_run_agent_task(
        query: str,
        user_id: str,
        run_mode: str = "demo",
        *,
        tenant_id: str | None = None,
    ) -> dict:
        captured.update(
            query=query,
            user_id=user_id,
            run_mode=run_mode,
            tenant_id=tenant_id,
        )
        return {"status": "ok", "tenant_id": tenant_id}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "agent-tenant-secret"
    tenant_id = "agent-tenant"
    operator = "Tenant operator"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    token = hmac.new(
        secret.encode(),
        f"agent-run:public/pricing:{operator}".encode(),
        hashlib.sha256,
    ).hexdigest()
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._tenant_agent_call_times.clear()

    response = client.post(
        "/api/agent/run",
        json={
            "query": "Inspect the tenant source",
            "user_id": "tenant-operator",
            "source_id": "public/pricing",
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert captured["tenant_id"] == tenant_id
    assert captured["run_mode"] == "live"
    assert 'source_id "public/pricing"' in str(captured["query"])


@pytest.mark.asyncio
async def test_signed_agent_route_attaches_bounded_internal_context(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_connector_context(_tenant_id: str) -> dict[str, object]:
        return {
            "status": "partial",
            "verified_connector_count": 1,
            "connectors": {
                "jira": {
                    "status": "ok",
                    "external_read": True,
                    "scope": "project:DRIFT",
                    "open_issue_count": 18,
                    "raw_issue": "must never be copied",
                }
            },
        }

    async def fake_run_agent_task(
        query: str,
        user_id: str,
        run_mode: str = "demo",
        *,
        tenant_id: str | None = None,
        internal_context: dict[str, object] | None = None,
    ) -> dict:
        captured.update(
            query=query,
            user_id=user_id,
            run_mode=run_mode,
            tenant_id=tenant_id,
            internal_context=internal_context,
        )
        return {"status": "ok", "tenant_id": tenant_id}

    monkeypatch.setattr(api, "_connector_context_info", fake_connector_context)
    monkeypatch.setattr(api, "_reserve_connector_call", lambda _tenant_id: True)
    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "agent-tenant-secret"
    tenant_id = "agent-tenant"
    operator = "Tenant operator"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    token = hmac.new(
        secret.encode(),
        f"agent-run:public/pricing:{operator}".encode(),
        hashlib.sha256,
    ).hexdigest()
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._tenant_agent_call_times.clear()

    response = client.post(
        "/api/agent/run",
        json={
            "query": "Inspect the tenant source",
            "user_id": "tenant-operator",
            "source_id": "public/pricing",
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert captured["tenant_id"] == tenant_id
    assert captured["run_mode"] == "live"
    context = captured["internal_context"]
    assert isinstance(context, dict)
    assert context["verified_connector_count"] == 1
    assert context["connectors"]["jira"]["open_issue_count"] == 18
    assert "raw_issue" not in str(context)


@pytest.mark.asyncio
async def test_live_agent_route_accepts_registered_source_for_signed_tenant(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    tenant_id = "agent-tenant"
    source.register_operator_source(
        source_id="custom/agent-pricing",
        name="Agent pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id=tenant_id,
    )
    captured: dict[str, object] = {}

    async def fake_run_agent_task(
        query: str,
        user_id: str,
        run_mode: str = "demo",
        *,
        tenant_id: str | None = None,
    ) -> dict:
        captured.update(query=query, user_id=user_id, run_mode=run_mode, tenant_id=tenant_id)
        return {"status": "ok", "tenant_id": tenant_id}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "agent-tenant-secret"
    operator = "Tenant operator"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    token = hmac.new(
        secret.encode(),
        f"agent-run:custom/agent-pricing:{operator}".encode(),
        hashlib.sha256,
    ).hexdigest()
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._tenant_agent_call_times.clear()

    response = client.post(
        "/api/agent/run",
        json={
            "query": "Inspect the registered tenant source",
            "user_id": "tenant-operator",
            "source_id": "custom/agent-pricing",
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert response.status_code == 200
    assert captured["tenant_id"] == tenant_id
    assert captured["run_mode"] == "live"
    assert 'source_id "custom/agent-pricing"' in str(captured["query"])


def test_live_agent_route_rejects_partial_signed_identity() -> None:
    response = client.post(
        "/api/agent/run",
        json={"query": "Inspect it", "tenant_id": "agent-tenant"},
    )
    assert response.status_code == 401


def test_live_agent_route_rejects_unallowlisted_source() -> None:
    response = client.post(
        "/api/agent/run",
        json={"query": "Inspect it", "source_id": "https://evil.example"},
    )
    assert response.status_code == 422


def test_packet_endpoint_is_available_after_approval() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )

    assert approved.status_code == 200
    packet = client.get(f"/api/workflows/{workflow_id}/packet")
    assert packet.status_code == 200
    assert "External systems changed: **No**" in packet.text


def test_async_job_records_agent_trace_and_workflow(monkeypatch) -> None:
    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        state = api.workflow_store.start_demo()
        return {
            "workflow_id": state.workflow_id,
            "model": "test-model",
            "execution_mode": "google_adk",
            "tool_calls": ["inspect_source_change", "get_workflow_state"],
            "event_count": 4,
            "response": "Evidence verified; waiting for a human decision.",
            "agent_trace": {"model": "test-model", "event_count": 4},
        }

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post("/api/jobs/demo", json={"query": "test"})

    assert response.status_code == 200
    queued = response.json()
    payload = client.get(f"/api/jobs/{queued['job_id']}").json()
    assert payload["status"] == "needs_approval"
    assert payload["workflow"]["status"] == "needs_approval"
    assert payload["tool_calls"] == [
        "inspect_source_change",
        "get_workflow_state",
    ]
    assert payload["workflow"]["agent_trace"]["model"] == "test-model"

    workflow_id = payload["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Alex Kim",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    assert client.get(f"/api/jobs/{queued['job_id']}").json()["status"] == "complete"


def test_identity_free_demo_mutations_are_rate_limited(monkeypatch) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 1)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()

    first = client.post("/api/workflows/demo")
    second = client.post("/api/workflows/demo")

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "Demo workflow rate limit reached; retry later."
    assert second.headers["retry-after"] == str(api.DEMO_WINDOW_SECONDS)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()


def test_public_mutation_quota_is_fair_per_browser_not_proxy_header(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 1)
    monkeypatch.setattr(api, "PUBLIC_DEMO_GLOBAL_MAX_MUTATIONS", 3)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()
    first_browser = TestClient(app)
    second_browser = TestClient(app)
    proxy_headers = {
        "x-forwarded-for": "203.0.113.8",
        "forwarded": "for=203.0.113.8;proto=https",
    }

    first = first_browser.post("/api/workflows/demo", headers=proxy_headers)
    exhausted = first_browser.post(
        "/api/decision-twin/demo",
        headers={
            "x-forwarded-for": "198.51.100.19",
            "forwarded": "for=198.51.100.19;proto=https",
        },
    )
    independent = second_browser.post("/api/workflows/demo", headers=proxy_headers)

    assert first.status_code == 200
    assert exhausted.status_code == 429
    assert independent.status_code == 200
    assert len(api._demo_mutation_times) == 2
    assert sorted(len(times) for times in api._public_demo_mutation_times.values()) == [
        1,
        1,
    ]


def test_public_mutation_quota_keeps_a_global_emergency_ceiling(monkeypatch) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 2)
    monkeypatch.setattr(api, "PUBLIC_DEMO_GLOBAL_MAX_MUTATIONS", 2)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()

    responses = [
        TestClient(app).post("/api/workflows/demo")
        for _index in range(3)
    ]

    assert [response.status_code for response in responses] == [200, 200, 429]
    assert responses[-1].headers["retry-after"] == str(api.DEMO_WINDOW_SECONDS)
    assert len(api._demo_mutation_times) == 2


def test_public_mutation_quota_does_not_retain_rejected_or_stale_sessions(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 2)
    monkeypatch.setattr(api, "PUBLIC_DEMO_GLOBAL_MAX_MUTATIONS", 1)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()
    assert TestClient(app).post("/api/workflows/demo").status_code == 200
    assert len(api._public_demo_mutation_times) == 1

    for index in range(20):
        attacker = TestClient(app)
        attacker.cookies.set(
            api.PUBLIC_MUTATION_SESSION_COOKIE,
            f"invalid-{index}",
        )
        rejected = attacker.post("/api/workflows/demo")
        assert rejected.status_code == 429
    assert len(api._public_demo_mutation_times) == 1

    expired = api.monotonic() - api.DEMO_WINDOW_SECONDS - 1
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        for bucket in api._public_demo_mutation_times.values():
            bucket.clear()
            bucket.append(expired)
    assert TestClient(app).post("/api/workflows/demo").status_code == 200
    assert len(api._public_demo_mutation_times) == 1


def test_invalid_demo_source_is_quota_neutral(monkeypatch) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 1)
    monkeypatch.setattr(api, "PUBLIC_DEMO_GLOBAL_MAX_MUTATIONS", 1)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()

    invalid = TestClient(app).post(
        "/api/workflows/demo",
        params={"source_id": "not/allowlisted"},
    )

    assert invalid.status_code == 422
    assert not api._demo_mutation_times
    assert not api._public_demo_mutation_times


def test_public_mutation_cookie_is_server_validated_and_hardened(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 2)
    monkeypatch.setattr(api, "PUBLIC_DEMO_GLOBAL_MAX_MUTATIONS", 10)
    monkeypatch.setenv("K_SERVICE", "driftline")
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()
    browser = TestClient(app)
    browser.cookies.set(api.PUBLIC_MUTATION_SESSION_COOKIE, "attacker-chosen")

    response = browser.post("/api/workflows/demo")

    assert response.status_code == 200
    cookie_header = response.headers["set-cookie"]
    assert f"{api.PUBLIC_MUTATION_SESSION_COOKIE}=" in cookie_header
    assert "attacker-chosen" not in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=strict" in cookie_header
    assert "Secure" in cookie_header
    assert "Path=/api" in cookie_header


def test_unauthorized_decision_requests_do_not_consume_public_quota(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DECISION_TWIN_LIVE_COUNCIL", "false")
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 2)
    monkeypatch.setattr(api, "PUBLIC_DEMO_GLOBAL_MAX_MUTATIONS", 10)
    persistence._decision_cases_memory.clear()
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()
        api._public_demo_mutation_times.clear()
    owner = TestClient(app)
    shared_viewer = TestClient(app)
    case = owner.post("/api/decision-twin/demo").json()
    payload = {
        "approver": "Owner PM",
        "option_id": "segment",
        "expected_synthesis_hash": case["council"]["synthesis_hash"],
        "expected_generation": 1,
    }

    missing = shared_viewer.post(
        "/api/decision-twin/not-a-case/approve",
        json=payload,
    )
    denied = shared_viewer.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json=payload,
    )
    approved = owner.post(
        f"/api/decision-twin/{case['case_id']}/approve",
        json=payload,
    )

    assert missing.status_code == 404
    assert denied.status_code == 403
    assert approved.status_code == 200
    assert len(api._demo_mutation_times) == 2


def test_live_agent_rate_limit_includes_retry_after_header(monkeypatch) -> None:
    monkeypatch.setattr(api, "PUBLIC_AGENT_MAX_CALLS", 0)
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post(
        "/api/jobs/demo",
        json={"source_id": "competitor/pricing", "query": "run"},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Live agent demo rate limit reached; retry later."
    assert response.headers["retry-after"] == str(api.AGENT_WINDOW_SECONDS)


@pytest.mark.asyncio
async def test_duplicate_job_delivery_cannot_run_agent_twice(monkeypatch) -> None:
    calls = 0

    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        nonlocal calls
        calls += 1
        state = api.workflow_store.start_demo()
        return {"workflow_id": state.workflow_id, "model": "test-model"}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()
    job = JobState(job_id="job-idempotent", query="test")
    api._set_job(job)

    await api._run_job(job.job_id)
    await api._run_job(job.job_id)

    assert calls == 1
    assert api._resolve_job(job.job_id).run_attempts == 1


@pytest.mark.asyncio
async def test_monitor_job_completes_without_inventing_a_workflow(monkeypatch) -> None:
    async def fake_run_agent_task(query: str, user_id: str, run_mode: str) -> dict:
        assert run_mode == "monitor"
        return {
            "model": "test-model",
            "execution_mode": "google_adk",
            "tool_calls": ["inspect_source_change"],
            "event_count": 2,
            "response": "No material source change was found.",
            "source_status": "unchanged",
            "change_detected": False,
        }

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    job = JobState(job_id="job-monitor-unchanged", query="monitor", run_mode="monitor")
    api._set_job(job)

    await api._run_job(job.job_id)

    result = api._resolve_job(job.job_id)
    assert result.status == "complete"
    assert result.workflow_id is None
    assert result.response == "No material source change was found."
    assert result.source_status == "unchanged"
    assert result.change_detected is False


@pytest.mark.asyncio
async def test_monitor_source_failure_is_a_clear_durable_disposition(monkeypatch) -> None:
    async def fake_run_agent_task(query: str, user_id: str, run_mode: str) -> dict:
        assert run_mode == "monitor"
        return {
            "model": "test-model",
            "execution_mode": "google_adk",
            "tool_calls": ["inspect_source_change"],
            "event_count": 2,
            "response": "No material source change was found.",
            "source_status": "source_fetch_failed",
            "change_detected": False,
        }

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    job = JobState(job_id="job-monitor-source-failure", query="monitor", run_mode="monitor")
    api._set_job(job)

    await api._run_job(job.job_id)

    result = api._resolve_job(job.job_id)
    assert result.status == "complete"
    assert result.workflow_id is None
    assert result.source_status == "source_fetch_failed"
    assert result.change_detected is False
    assert result.error is None
    assert result.response == (
        "Source fetch failed; no workflow was created. "
        "The bounded scheduler will retry this source."
    )


@pytest.mark.asyncio
async def test_public_demo_falls_back_to_labelled_synthetic_replay_on_adk_failure(
    monkeypatch,
) -> None:
    async def unavailable(*args, **kwargs):
        raise RuntimeError("quota exhausted")

    monkeypatch.setattr(api, "run_agent_task", unavailable)
    job = JobState(
        job_id="job-demo-fallback",
        query='scan the allowlisted source_id "public/pricing"',
        run_mode="demo",
    )
    api._set_job(job)

    await api._run_job(job.job_id)

    result = api._resolve_job(job.job_id)
    assert result.status == "needs_approval"
    assert result.execution_mode == "deterministic_demo_fallback"
    assert result.model == "synthetic"
    assert result.error is None
    assert result.workflow_id
    workflow = api._resolve_workflow(result.workflow_id)
    assert workflow.data_mode == "synthetic_demo"
    assert "temporarily unavailable" in result.response


def test_approval_requires_explicit_signed_token_when_signed_mode_enabled(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "signed")
    tenant_state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(tenant_state)
    workflow_id = tenant_state.workflow_id

    rejected = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Alex Kim"},
    )
    assert rejected.status_code == 403

    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    token = hmac.new(
        secret.encode(), f"{workflow_id}:Alex Kim".encode(), hashlib.sha256
    ).hexdigest()
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Alex Kim",
            "approval_mode": "signed",
            "approval_token": token,
        },
    )
    assert approved.status_code == 200
    assert approved.json()["approval"]["approval_identity"]["mode"] == "signed"


def test_failed_workflow_cas_restores_pending_state(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    monkeypatch.setattr(api, "compare_and_set_workflow", lambda state, expected: False)

    response = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )

    assert response.status_code == 409
    assert client.get(f"/api/workflows/{workflow_id}").json()["status"] == (
        "needs_approval"
    )
