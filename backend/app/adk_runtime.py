from __future__ import annotations

from uuid import uuid4

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "driftline"


async def run_agent_task(query: str, user_id: str = "demo-operator") -> dict:
    """Run one real Gemini/ADK turn and return its final grounded response."""
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
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=message,
    ):
        event_count += 1
        for function_call in event.get_function_calls() or []:
            if function_call.name and function_call.name not in tool_calls:
                tool_calls.append(function_call.name)
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
    }
