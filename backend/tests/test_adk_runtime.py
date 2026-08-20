import pytest

from app import adk_runtime
from app.analysis import AnalysisUnavailable


def test_structured_analysis_fallback_is_explicitly_demo_only() -> None:
    result = adk_runtime._analysis_failure_result(
        run_mode="demo",
        reason="Gemini returned no structured analysis",
        artifact_count=4,
    )

    assert result == {
        "mode": "deterministic_demo_fallback",
        "reason": "Gemini returned no structured analysis",
        "artifact_count": 4,
    }


@pytest.mark.parametrize("run_mode", ["monitor", "live", "production"])
def test_structured_analysis_failure_fails_closed_for_live_modes(run_mode: str) -> None:
    with pytest.raises(AnalysisUnavailable, match="Gemini unavailable"):
        adk_runtime._analysis_failure_result(
            run_mode=run_mode,
            reason="Gemini unavailable",
            artifact_count=4,
        )


def test_agent_trace_payload_is_redacted_and_contains_decision_metadata() -> None:
    payload = adk_runtime._agent_trace_payload(
        started_at="2026-08-20T00:00:00+00:00",
        tool_calls=[{"kind": "tool_call", "name": "inspect_source_change"}],
        event_count=7,
        analysis_info={"mode": "gemini_structured", "evidence_hash": "abc"},
        decision_info={"mode": "gemini_structured", "policy_review": {"status": "pass"}},
    )

    assert payload["execution_mode"] == "google_adk"
    assert payload["tool_calls"] == [
        {"kind": "tool_call", "name": "inspect_source_change"}
    ]
    assert payload["decision_copilot"] == {
        "mode": "gemini_structured",
        "policy_review": {"status": "pass"},
    }
    assert "prompt" not in payload
    assert "source_body" not in payload
    assert "credential" not in payload
