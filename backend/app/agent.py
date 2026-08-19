from __future__ import annotations

import os
from contextvars import ContextVar, Token

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig, ThinkingConfig

from .persistence import load_workflow, persist_workflow
from .source import inspect_allowlisted_source
from .workflow import workflow_store

load_dotenv()
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")

_run_mode: ContextVar[str] = ContextVar("driftline_run_mode", default="demo")


def set_run_mode(mode: str) -> Token[str]:
    """Set the per-request source mode without leaking across async jobs."""
    return _run_mode.set(mode)


def reset_run_mode(token: Token[str]) -> None:
    _run_mode.reset(token)


def inspect_source_change(source_id: str) -> dict:
    """Detect and verify a material change in an approved source."""
    snapshot = inspect_allowlisted_source(
        source_id,
        force_replay=_run_mode.get() == "demo",
    )
    if snapshot.get("status") == "rejected":
        return snapshot
    if not snapshot.get("change_detected", True):
        return snapshot
    state = workflow_store.start_demo(
        source_id=str(snapshot.get("source_id", source_id)),
        source_name=(
            "Public terms snapshot"
            if source_id == "public/terms"
            else "Public pricing snapshot"
        ),
        data_mode=snapshot["data_mode"],
        source_url=snapshot["source_url"],
        snapshot_label=snapshot["snapshot_label"],
        after_text=snapshot["after"],
        snapshot_hash=snapshot["snapshot_hash"],
        previous_snapshot_hash=snapshot.get("previous_snapshot_hash"),
        retrieved_at=snapshot["retrieved_at"],
        before_text=snapshot.get("before") or None,
        confidence=float(snapshot.get("confidence", 0.99)),
    )
    persist_workflow(state)
    return state.to_dict()


def get_workflow_state(workflow_id: str) -> dict:
    """Return the evidence, stage, impacts, and audit events for a workflow."""
    try:
        state = workflow_store.get(workflow_id)
    except KeyError:
        state = load_workflow(workflow_id)
        if state is None:
            raise KeyError(f"Unknown workflow: {workflow_id}")
        state = workflow_store.restore(state)
    return state.to_dict()


root_agent = Agent(
    name="driftline_change_operator",
    model=os.getenv("MODEL_NAME", "gemini-3.5-flash"),
    generate_content_config=GenerateContentConfig(
        max_output_tokens=512,
        thinking_config=ThinkingConfig(thinking_level="LOW"),
    ),
    description=(
        "Autonomous enterprise change operator that turns verified source "
        "changes into bounded, auditable downstream actions."
    ),
    instruction="""
You are Driftline's change operations coordinator. Work only with approved
public or synthetic sources. Always gather hash-bound evidence before proposing
an action. Use tools rather than narrating actions. Never claim an artifact was
updated unless the workflow state records a bounded packet. High-risk changes
must pause for a named human decision. Approval is owned by the separate human
approval endpoint; you cannot approve, resume, or publish a workflow yourself.
You may not manufacture or infer that approval. For the judge-ready demo
request, call inspect_source_change with the exact allowlisted source_id
"public/pricing" before responding, then ground the response in the returned
workflow state. Call get_workflow_state with the returned workflow_id before
the final response so the state read is independently verified. For a monitor
run, if the source tool returns baseline_established or unchanged, do not
invent a workflow or approval; report that no material change was found. Name
whether the source was a public snapshot or synthetic replay.
Keep explanations concise and evidence-grounded.
Your final response must be a complete plain-text summary of no more than 80
words. Do not use markdown, tables, backticks, or a workflow ID; end with a
complete sentence.
""".strip(),
    tools=[inspect_source_change, get_workflow_state],
)
