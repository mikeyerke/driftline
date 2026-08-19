from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import reset_run_mode, root_agent, set_run_mode
from .analysis import AnalysisUnavailable, analysis_trace, analyze_workflow
from .persistence import load_workflow, persist_workflow
from .workflow import workflow_store

APP_NAME = "driftline"


def _analysis_failure_result(
    *, run_mode: str, reason: str, artifact_count: int | None = None
) -> dict[str, object]:
    """Keep deterministic drafts demo-only; live runs fail closed."""
    if run_mode != "demo":
        raise AnalysisUnavailable(reason)
    result: dict[str, object] = {
        "mode": "deterministic_demo_fallback",
        "reason": reason,
    }
    if artifact_count is not None:
        result["artifact_count"] = artifact_count
    return result


async def run_agent_task(
    query: str, user_id: str = "demo-operator", run_mode: str = "demo"
) -> dict:
    """Run one real Gemini/ADK turn and return its final grounded response."""
    started_at = datetime.now(UTC).isoformat()
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=str(uuid4()),
    )
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    message = types.Content(role="user", parts=[types.Part(text=query)])

    final_text = ""
    event_count = 0
    tool_calls: list[str] = []
    workflow_id: str | None = None
    source_status: str | None = None
    change_detected: bool | None = None
    trace: list[dict[str, str]] = []
    mode_token = set_run_mode(run_mode)
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=message,
        ):
            event_count += 1
            for function_call in event.get_function_calls() or []:
                if function_call.name and function_call.name not in tool_calls:
                    tool_calls.append(function_call.name)
                    trace.append({"kind": "tool_call", "name": function_call.name})
            if event.content and event.content.parts:
                for part in event.content.parts:
                    function_response = getattr(part, "function_response", None)
                    response = getattr(function_response, "response", None)
                    if isinstance(response, dict):
                        if response.get("workflow_id"):
                            workflow_id = str(response["workflow_id"])
                        if response.get("status"):
                            source_status = str(response["status"])
                        if "change_detected" in response:
                            change_detected = bool(response["change_detected"])
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(
                    part.text or "" for part in event.content.parts if part.text
                )
    finally:
        reset_run_mode(mode_token)

    # The coordinator turn only discovers and verifies the source.  A second,
    # schema-constrained ADK turn performs the substantive impact mapping.  It
    # has no tools and no approval/publishing authority; the deterministic
    # workflow gate remains the only path to a decision.  If structured output
    # is unavailable, retain the reproducible fixture drafts and label the
    # fallback explicitly rather than presenting them as Gemini analysis.
    analysis_info: dict[str, object]
    if workflow_id:
        try:
            state = workflow_store.get(workflow_id)
        except KeyError:
            state = load_workflow(workflow_id)
        if state is None:
            analysis_info = _analysis_failure_result(
                run_mode=run_mode,
                reason="Workflow state unavailable for structured analysis",
            )
        else:
            try:
                structured = await analyze_workflow(state)
                analysis_info = analysis_trace(structured)
                persist_workflow(state)
            except AnalysisUnavailable as exc:
                analysis_info = _analysis_failure_result(
                    run_mode=run_mode,
                    reason=str(exc),
                    artifact_count=len(state.impacts),
                )
    else:
        analysis_info = {
            "mode": "deterministic_demo_fallback",
            "reason": "coordinator did not produce a workflow",
            "source_status": source_status,
        }

    return {
        "session_id": session.id,
        "response": final_text,
        "event_count": event_count,
        "tool_calls": tool_calls,
        "model": root_agent.model,
        "execution_mode": "google_adk",
        "workflow_id": workflow_id,
        "source_status": source_status,
        "change_detected": change_detected,
        "agent_trace": {
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat(),
            "model": root_agent.model,
            "execution_mode": "google_adk",
            "tool_calls": trace,
            "event_count": event_count,
            "structured_analysis": analysis_info,
        },
    }
