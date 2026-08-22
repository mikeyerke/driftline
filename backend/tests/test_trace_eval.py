from __future__ import annotations

from app.trace_eval import (
    QUALITY_CASES,
    build_quality_fixture,
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


def test_fixture_builder_does_not_mutate_between_runs() -> None:
    first = build_quality_fixture()
    second = build_quality_fixture()
    first["agent_trace"]["tool_calls"].append({"name": "unallowlisted_tool"})

    assert "unallowlisted_tool" not in {
        call["name"] for call in second["agent_trace"]["tool_calls"]
    }
