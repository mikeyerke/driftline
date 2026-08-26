from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import (
    get_workflow_state,
    reset_run_mode,
    reset_source_id,
    reset_tenant_id,
    reset_workflow_id,
    root_agent,
    set_run_mode,
    set_source_id,
    set_tenant_id,
    set_workflow_id,
    source_id_from_query,
    workflow_id_from_context,
)
from .analysis import AnalysisUnavailable, analysis_trace, analyze_workflow
from .decision_copilot import (
    analyze_decision,
    decision_trace,
    fallback_copilot,
    red_team_review,
)
from .persistence import load_workflow, persist_workflow
from .workflow import workflow_store

APP_NAME = "driftline"


def _agent_trace_payload(
    *,
    started_at: str,
    tool_calls: list[dict[str, str]],
    event_count: int,
    analysis_info: dict[str, object],
    decision_info: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build the durable, redacted trace shared by API and Firestore state.

    The trace intentionally contains model/tool metadata and structured review
    outputs only; prompts, connector credentials, and source bodies never
    enter the workflow record.
    """
    payload: dict[str, object] = {
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "model": root_agent.model,
        "execution_mode": "google_adk",
        "tool_calls": tool_calls,
        "event_count": event_count,
        "structured_analysis": analysis_info,
    }
    if decision_info is not None:
        payload["decision_copilot"] = decision_info
    return payload


def _analysis_failure_result(
    *, run_mode: str, reason: str, artifact_count: int | None = None
) -> dict[str, object]:
    """Keep deterministic drafts limited to explicitly synthetic lanes.

    ``tenant_demo`` is the signed operator replay lane. It may use the same
    visibly labelled fallback as the anonymous demo when a structured Gemini
    turn is transiently unavailable; real monitor/live lanes still fail closed
    so a production source can never be presented as model-analysed when it
    was not.
    """
    if run_mode not in {"demo", "tenant_demo"}:
        raise AnalysisUnavailable(reason)
    result: dict[str, object] = {
        "mode": "deterministic_demo_fallback",
        "reason": reason,
    }
    if artifact_count is not None:
        result["artifact_count"] = artifact_count
    return result


def _workflow_id_from_turn(workflow_id: str | None) -> str | None:
    """Recover a workflow created by a tool even if Gemini omits a follow-up.

    The source tool binds the created workflow to the current ADK turn before
    returning its guarded payload. A model may legitimately stop after that
    tool call, so the runtime must use the turn-local binding as the durable
    source of truth instead of orphaning the workflow or retrying it as a new
    monitor run.
    """
    bound_workflow_id = workflow_id_from_context()
    if workflow_id and workflow_id != bound_workflow_id:
        raise PermissionError("workflow_turn_mismatch")
    return bound_workflow_id


def _require_bound_state(
    state: object,
    *,
    workflow_id: str,
    tenant_id: str | None,
) -> None:
    """Fail closed before post-turn analysis or persistence crosses a boundary."""
    if getattr(state, "workflow_id", None) != workflow_id:
        raise PermissionError("workflow_turn_mismatch")
    if getattr(state, "tenant_id", None) != tenant_id:
        raise PermissionError("workflow_tenant_mismatch")


def _ensure_state_verification(
    workflow_id: str | None,
    tool_calls: list[str],
    trace: list[dict[str, str]],
) -> None:
    """Guarantee one bounded state read when Gemini omits its final tool call.

    The coordinator is instructed to call ``get_workflow_state`` after source
    inspection. Provider turns can stop after the first tool response,
    though, so the runtime performs the same allowlisted read as a deterministic
    verifier. It is recorded with its origin instead of being silently added
    to the trace.
    """
    if not workflow_id or "get_workflow_state" in tool_calls:
        return
    get_workflow_state(workflow_id)
    tool_calls.append("get_workflow_state")
    trace.append(
        {
            "kind": "tool_call",
            "name": "get_workflow_state",
            "origin": "runtime_verifier",
        }
    )


async def run_agent_task(
    query: str,
    user_id: str = "demo-operator",
    run_mode: str = "demo",
    tenant_id: str | None = None,
    internal_context: dict[str, object] | None = None,
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
    data_mode: str | None = None
    trace: list[dict[str, str]] = []
    trace_event_count = 0
    mode_token = set_run_mode(run_mode)
    tenant_token = set_tenant_id(tenant_id)
    workflow_token = set_workflow_id(None)
    source_token = set_source_id(source_id_from_query(query))
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
                        if response.get("data_mode"):
                            data_mode = str(response["data_mode"])
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(
                    part.text or "" for part in event.content.parts if part.text
                )
        # The coordinator normally echoes the workflow id in a function
        # response. Recover the context-bound id when it stops after the
        # source inspection tool, so a real change cannot be orphaned.
        workflow_id = _workflow_id_from_turn(workflow_id)
        _ensure_state_verification(workflow_id, tool_calls, trace)
        trace_event_count = event_count
    finally:
        reset_run_mode(mode_token)
        reset_tenant_id(tenant_token)
        reset_workflow_id(workflow_token)
        reset_source_id(source_token)

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
            decision_info = {
                "mode": "unavailable",
                "reason": "Workflow state unavailable for decision copilot",
            }
        else:
            _require_bound_state(
                state,
                workflow_id=workflow_id,
                tenant_id=tenant_id,
            )
            if internal_context is not None:
                event_count_before_context = len(state.events)
                workflow_store.attach_internal_context(state, internal_context)
                data_mode = state.data_mode
                trace_event_count += max(
                    0, len(state.events) - event_count_before_context
                )
                _require_bound_state(
                    state,
                    workflow_id=workflow_id,
                    tenant_id=tenant_id,
                )
                persist_workflow(state)
            try:
                structured = await analyze_workflow(state)
                analysis_info = analysis_trace(structured, state.internal_context)
                # Gemini may replace deterministic draft text or risk labels
                # after the source tool creates the workflow. Rebuild the
                # decision card so the UI and durable state cannot drift from
                # the validated artifact set (including attached context).
                workflow_store.refresh_change_card(state)
                # Persist the coordinator and analysis trace before the
                # decision pass so a later bounded failure still leaves an
                # auditable record of what ran.
                state.agent_trace = _agent_trace_payload(
                    started_at=started_at,
                    tool_calls=trace,
                    event_count=trace_event_count,
                    analysis_info=analysis_info,
                )
                _require_bound_state(
                    state,
                    workflow_id=workflow_id,
                    tenant_id=tenant_id,
                )
                persist_workflow(state)
            except AnalysisUnavailable as exc:
                analysis_info = _analysis_failure_result(
                    run_mode=run_mode,
                    reason=str(exc),
                    artifact_count=len(state.impacts),
                )
                state.agent_trace = _agent_trace_payload(
                    started_at=started_at,
                    tool_calls=trace,
                    event_count=trace_event_count,
                    analysis_info=analysis_info,
                )
                _require_bound_state(
                    state,
                    workflow_id=workflow_id,
                    tenant_id=tenant_id,
                )
                persist_workflow(state)
            try:
                copilot, policy = await analyze_decision(state)
                decision_info = decision_trace(
                    copilot, policy, internal_context=state.internal_context
                )
            except AnalysisUnavailable as exc:
                if run_mode not in {"demo", "tenant_demo"}:
                    raise
                fallback = fallback_copilot(state)
                decision_info = decision_trace(
                    fallback,
                    red_team_review(fallback, state),
                    mode="deterministic_demo_fallback",
                    reason=str(exc),
                    internal_context=state.internal_context,
                )
            state.agent_trace = _agent_trace_payload(
                started_at=started_at,
                tool_calls=trace,
                event_count=trace_event_count,
                analysis_info=analysis_info,
                decision_info=decision_info,
            )
            _require_bound_state(
                state,
                workflow_id=workflow_id,
                tenant_id=tenant_id,
            )
            persist_workflow(state)
    else:
        analysis_info = {
            "mode": "deterministic_demo_fallback",
            "reason": "coordinator did not produce a workflow",
            "source_status": source_status,
        }
        decision_info = {
            "mode": "unavailable",
            "reason": "coordinator did not produce a workflow",
        }

    return {
        "session_id": session.id,
        "response": final_text,
        "event_count": trace_event_count,
        "tool_calls": tool_calls,
        "model": root_agent.model,
        "execution_mode": "google_adk",
        "workflow_id": workflow_id,
        "tenant_id": tenant_id,
        "data_mode": data_mode,
        "persisted": bool(
            workflow_id
            and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold()
            == "firestore"
        ),
        "source_status": source_status,
        "change_detected": change_detected,
        "agent_trace": _agent_trace_payload(
            started_at=started_at,
            tool_calls=trace,
            event_count=trace_event_count,
            analysis_info=analysis_info,
            decision_info=decision_info,
        ),
    }
