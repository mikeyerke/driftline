from __future__ import annotations

import json

import pytest

from app.trace_eval import (
    QUALITY_CASES,
    build_quality_fixture,
    load_quality_baseline,
    run_quality_gate,
)


def test_quality_fixture_passes_independent_safety_and_usefulness_cases() -> None:
    report = run_quality_gate(
        build_quality_fixture(),
        release_sha="a" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    assert report["gate_status"] == "pass"
    assert report["safety_score"] == 1.0
    assert report["usefulness_score"] == 1.0
    assert report["trace_data_mode"] == "synthetic_demo"
    assert report["case_count"] == len(QUALITY_CASES)
    assert all(case["status"] == "pass" for case in report["cases"])
    assert report["trace_fingerprint"]


def test_gate_blocks_approval_bypass_and_preserves_case_level_reason() -> None:
    trace = build_quality_fixture()
    trace["status"] = "complete"
    trace["approval"] = {"approver": "driftline-agent"}

    report = run_quality_gate(
        trace,
        release_sha="b" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    assert report["gate_status"] == "fail"
    approval_case = next(
        case for case in report["cases"] if case["case_id"] == "safety_human_gate"
    )
    assert approval_case["status"] == "fail"
    assert approval_case["severity"] == "critical"
    assert approval_case["reason"]


def test_gate_requires_explicit_red_team_provenance() -> None:
    trace = build_quality_fixture()
    trace["agent_trace"]["decision_copilot"]["policy_review"].pop("reviewer")

    report = run_quality_gate(
        trace,
        release_sha="b" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    policy_case = next(
        case
        for case in report["cases"]
        if case["case_id"] == "safety_red_team_provenance"
    )
    assert policy_case["status"] == "fail"
    assert policy_case["severity"] == "critical"
    assert report["gate_status"] == "fail"


def test_gate_blocks_preapproval_connector_write_claim() -> None:
    trace = build_quality_fixture()
    trace["integration_targets"][0]["status"] = "created"
    trace["integration_targets"][0]["external_write"] = True

    report = run_quality_gate(
        trace,
        release_sha="b" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    handoff_case = next(
        case
        for case in report["cases"]
        if case["case_id"] == "safety_preapproval_handoff_boundary"
    )
    assert handoff_case["status"] == "fail"
    assert handoff_case["severity"] == "critical"
    assert report["gate_status"] == "fail"


def test_gate_accepts_signed_aggregate_context_and_rejects_raw_fields() -> None:
    trace = build_quality_fixture()
    trace["change_card"]["internal_context"] = {
        "status": "partial",
        "attempted_connector_count": 2,
        "verified_connector_count": 1,
        "redaction": "aggregate_metadata_only",
        "connectors": {
            "jira": {
                "status": "ok",
                "external_read": True,
                "scope": "project:DRIFT",
                "open_issue_count": 12,
                "redaction": "aggregate_metadata_only",
            },
            "salesforce": {
                "status": "reauthorization_required",
                "external_read": False,
                "scope": "read_only_crm",
                "redaction": "aggregate_metadata_only",
            },
        },
    }
    trace["change_card"]["exposure"] = {
        "mode": "connected_internal_data"
    }
    context_provenance = {
        "status": "partial",
        "attempted_connector_count": 2,
        "verified_connector_count": 1,
        "connector_names": ["jira", "salesforce"],
        "used_in_prompt": True,
        "redaction": "aggregate_metadata_only",
    }
    trace["agent_trace"]["structured_analysis"]["internal_context"] = context_provenance
    trace["agent_trace"]["decision_copilot"]["internal_context"] = context_provenance
    trace["events"].append(
        {
            "action": "internal_context_reader",
            "outcome": "aggregate_context_attached",
        }
    )

    report = run_quality_gate(
        trace,
        release_sha="a" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )
    context_case = next(
        case
        for case in report["cases"]
        if case["case_id"] == "safety_internal_context_boundary"
    )
    assert context_case["status"] == "pass"

    trace["change_card"]["internal_context"]["connectors"]["jira"]["issue_body"] = (
        "raw text"
    )
    report = run_quality_gate(
        trace,
        release_sha="b" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )
    context_case = next(
        case
        for case in report["cases"]
        if case["case_id"] == "safety_internal_context_boundary"
    )
    assert context_case["status"] == "fail"


def test_gate_rejects_missing_internal_context_prompt_provenance() -> None:
    trace = build_quality_fixture()
    trace["agent_trace"]["decision_copilot"].pop("internal_context")

    report = run_quality_gate(
        trace,
        release_sha="c" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    context_case = next(
        case
        for case in report["cases"]
        if case["case_id"] == "safety_internal_context_boundary"
    )
    assert context_case["status"] == "fail"
    assert report["gate_status"] == "fail"


def test_gate_rejects_missing_source_snapshot_provenance() -> None:
    trace = build_quality_fixture()
    trace["evidence"].pop("snapshot_hash")

    report = run_quality_gate(
        trace,
        release_sha="1" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    provenance_case = next(
        case for case in report["cases"] if case["case_id"] == "safety_source_provenance"
    )
    assert provenance_case["status"] == "fail"
    assert report["gate_status"] == "fail"


def test_gate_accepts_aggregate_context_mode_for_source_provenance() -> None:
    trace = build_quality_fixture()
    trace["data_mode"] = "connected_internal_data"

    report = run_quality_gate(
        trace,
        release_sha="d" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    provenance_case = next(
        case
        for case in report["cases"]
        if case["case_id"] == "safety_source_provenance"
    )
    assert provenance_case["status"] == "pass"


def test_gate_rejects_unstable_change_card_identity() -> None:
    previous = run_quality_gate(
        build_quality_fixture(),
        release_sha="3" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )
    trace = build_quality_fixture()
    trace["change_card"]["change_card_id"] = "card-not-derived-from-evidence"

    report = run_quality_gate(
        trace,
        release_sha="2" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
        previous_report=previous,
    )

    identity_case = next(
        case
        for case in report["cases"]
        if case["case_id"] == "usefulness_change_card_identity"
    )
    assert identity_case["status"] == "fail"
    assert report["gate_status"] == "fail"


def test_gate_marks_regression_against_previous_report() -> None:
    previous = run_quality_gate(
        build_quality_fixture(),
        release_sha="c" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )
    regressed = build_quality_fixture()
    regressed["impacts"] = regressed["impacts"][:2]

    report = run_quality_gate(
        regressed,
        release_sha="d" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
        previous_report=previous,
    )

    assert report["trend"]["status"] == "regressed"
    assert report["trend"]["overall_delta"] < 0
    assert report["gate_status"] == "fail"


def test_gate_marks_case_regression_even_when_pillar_score_is_unchanged() -> None:
    previous_trace = build_quality_fixture()
    previous_trace["agent_trace"]["structured_analysis"]["mode"] = "untrusted"
    previous = run_quality_gate(
        previous_trace,
        release_sha="e" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
    )

    current_trace = build_quality_fixture()
    current_trace["events"] = current_trace["events"][:4]
    report = run_quality_gate(
        current_trace,
        release_sha="f" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
        previous_report=previous,
    )

    assert report["trend"]["overall_delta"] == 0.0
    assert report["trend"]["usefulness_delta"] == 0.0
    assert report["trend"]["status"] == "regressed"
    assert report["trend"]["case_regressions"] == ["usefulness_audit_trace"]
    assert report["gate_status"] == "fail"


def test_quality_baseline_rejects_suite_contract_drift(tmp_path) -> None:
    baseline = {
        "evaluation_id": "baseline-trace-eval-v1",
        "suite_version": "trace-eval-v1",
        "case_ids": [case.case_id for case in QUALITY_CASES],
        "safety_score": 1.0,
        "usefulness_score": 1.0,
        "overall_score": 1.0,
        "cases": [
            {"case_id": case.case_id, "status": "pass"}
            for case in QUALITY_CASES
        ],
    }
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")

    loaded = load_quality_baseline(path)
    assert loaded["evaluation_id"] == "baseline-trace-eval-v1"
    assert loaded["overall_score"] == 1.0

    baseline["case_ids"] = baseline["case_ids"][:-1]
    path.write_text(json.dumps(baseline), encoding="utf-8")
    with pytest.raises(ValueError, match="case contract"):
        load_quality_baseline(path)


def test_fixture_builder_does_not_mutate_between_runs() -> None:
    first = build_quality_fixture()
    second = build_quality_fixture()
    first["agent_trace"]["tool_calls"].append({"name": "unallowlisted_tool"})

    assert "unallowlisted_tool" not in {
        call["name"] for call in second["agent_trace"]["tool_calls"]
    }
