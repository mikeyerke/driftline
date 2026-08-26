import pytest

from app import adk_runtime
from app.analysis import AnalysisUnavailable


@pytest.mark.parametrize("run_mode", ["demo", "tenant_demo"])
def test_structured_analysis_fallback_is_explicitly_synthetic_only(run_mode: str) -> None:
    result = adk_runtime._analysis_failure_result(
        run_mode=run_mode,
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


def test_workflow_id_is_recovered_when_model_stops_after_source_tool() -> None:
    token = adk_runtime.set_workflow_id("workflow-from-tool-context")
    try:
        assert adk_runtime._workflow_id_from_turn(None) == "workflow-from-tool-context"
        assert (
            adk_runtime._workflow_id_from_turn("workflow-from-tool-context")
            == "workflow-from-tool-context"
        )
        with pytest.raises(PermissionError, match="workflow_turn_mismatch"):
            adk_runtime._workflow_id_from_turn("workflow-from-response")
    finally:
        adk_runtime.reset_workflow_id(token)


def test_workflow_id_response_requires_a_turn_binding() -> None:
    token = adk_runtime.set_workflow_id(None)
    try:
        with pytest.raises(PermissionError, match="workflow_turn_mismatch"):
            adk_runtime._workflow_id_from_turn("foreign-workflow")
    finally:
        adk_runtime.reset_workflow_id(token)


def test_post_turn_state_requires_exact_workflow_and_tenant() -> None:
    state = type(
        "State",
        (),
        {"workflow_id": "wf-a", "tenant_id": "tenant-a"},
    )()
    adk_runtime._require_bound_state(
        state,
        workflow_id="wf-a",
        tenant_id="tenant-a",
    )

    with pytest.raises(PermissionError, match="workflow_turn_mismatch"):
        adk_runtime._require_bound_state(
            state,
            workflow_id="wf-b",
            tenant_id="tenant-a",
        )
    with pytest.raises(PermissionError, match="workflow_tenant_mismatch"):
        adk_runtime._require_bound_state(
            state,
            workflow_id="wf-a",
            tenant_id="tenant-b",
        )


def test_runtime_verifier_records_missing_state_read(monkeypatch) -> None:
    calls = []

    def fake_get_workflow_state(workflow_id: str) -> dict:
        calls.append(workflow_id)
        return {"workflow_id": workflow_id}

    monkeypatch.setattr(adk_runtime, "get_workflow_state", fake_get_workflow_state)
    tool_calls: list[str] = ["inspect_source_change"]
    trace: list[dict[str, str]] = []
    adk_runtime._ensure_state_verification("wf-1", tool_calls, trace)

    assert calls == ["wf-1"]
    assert tool_calls == ["inspect_source_change", "get_workflow_state"]
    assert trace == [
        {
            "kind": "tool_call",
            "name": "get_workflow_state",
            "origin": "runtime_verifier",
        }
    ]


def test_runtime_verifier_does_not_duplicate_model_state_read(monkeypatch) -> None:
    monkeypatch.setattr(
        adk_runtime,
        "get_workflow_state",
        lambda workflow_id: (_ for _ in ()).throw(AssertionError("duplicate read")),
    )
    tool_calls: list[str] = ["inspect_source_change", "get_workflow_state"]
    trace: list[dict[str, str]] = []
    adk_runtime._ensure_state_verification("wf-1", tool_calls, trace)
    assert tool_calls == ["inspect_source_change", "get_workflow_state"]
    assert trace == []
