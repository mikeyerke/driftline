from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "driftline"


async def run_agent_task(query: str, user_id: str = "demo-operator") -> dict:
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
    trace: list[dict[str, str]] = []
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
                if isinstance(response, dict) and response.get("workflow_id"):
                    workflow_id = str(response["workflow_id"])
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(
                part.text or "" for part in event.content.parts if part.text
            )

    return {
        "session_id": session.id,
        "response": final_text,
        "event_count": event_count,
        "tool_calls": tool_calls,
        "model": root_agent.model,
        "execution_mode": "google_adk",
        "workflow_id": workflow_id,
        "agent_trace": {
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat(),
            "model": root_agent.model,
            "execution_mode": "google_adk",
            "tool_calls": trace,
            "event_count": event_count,
        },
    }
