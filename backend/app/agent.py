from __future__ import annotations

import os
from contextvars import ContextVar, Token

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig, ThinkingConfig

from .guardrails import model_safe_state, untrusted_evidence_instruction
from .persistence import load_workflow, persist_workflow
from .source import inspect_allowlisted_source, source_definition
from .workflow import workflow_store

load_dotenv()
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")

_run_mode: ContextVar[str] = ContextVar("driftline_run_mode", default="demo")
_tenant_id: ContextVar[str | None] = ContextVar("driftline_tenant_id", default=None)
_workflow_id: ContextVar[str | None] = ContextVar("driftline_workflow_id", default=None)


def set_run_mode(mode: str) -> Token[str]:
    """Set the per-request source mode without leaking across async jobs."""
    return _run_mode.set(mode)


def reset_run_mode(token: Token[str]) -> None:
    _run_mode.reset(token)


def set_tenant_id(tenant_id: str | None) -> Token[str | None]:
    """Bind a tenant to the current ADK turn without global mutable state."""
    return _tenant_id.set(tenant_id)


def reset_tenant_id(token: Token[str | None]) -> None:
    _tenant_id.reset(token)


def set_workflow_id(workflow_id: str | None) -> Token[str | None]:
    """Bind the workflow created by the current source inspection call."""
    return _workflow_id.set(workflow_id)


def reset_workflow_id(token: Token[str | None]) -> None:
    _workflow_id.reset(token)


def inspect_source_change(source_id: str) -> dict:
    """Detect and verify a material change in an approved source."""
    snapshot = inspect_allowlisted_source(
        source_id,
        tenant_id=_tenant_id.get(),
        force_replay=_run_mode.get() == "demo",
    )
    if snapshot.get("status") == "rejected":
        return model_safe_state(snapshot)
    if not snapshot.get("change_detected", True):
        return model_safe_state(snapshot)
    state = workflow_store.start_demo(
        tenant_id=_tenant_id.get(),
        source_id=str(snapshot.get("source_id", source_id)),
        source_name=(source_definition(source_id, _tenant_id.get()) or {}).get(
            "name", "Allowlisted public snapshot"
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
    _workflow_id.set(state.workflow_id)
    # The persisted/API state remains raw and hash-bound. Only the copy sent
    # back across the ADK tool seam is guarded against source prompt injection.
    return model_safe_state(state.to_dict())


def get_workflow_state(workflow_id: str) -> dict:
    """Return the evidence, stage, impacts, and audit events for a workflow."""
    # Models occasionally use a placeholder after a tool response. Resolve it
    # only to the workflow created in this ADK turn; never select another
    # tenant's or another request's latest workflow.
    if workflow_id.strip().casefold() in {"", "default", "current"}:
        workflow_id = _workflow_id.get() or workflow_id
    try:
        state = workflow_store.get(workflow_id)
    except KeyError:
        state = load_workflow(workflow_id)
        if state is None:
            raise KeyError(f"Unknown workflow: {workflow_id}")
        state = workflow_store.restore(state)
    # Never expose raw operator-registered source text to the coordinator. The
    # UI/API reads the persisted state directly through their own route.
    return model_safe_state(state.to_dict())


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
    instruction=(
        untrusted_evidence_instruction()
        + """
You are Driftline's change operations coordinator. Work only with approved
public or synthetic sources. Always gather hash-bound evidence before proposing
an action. Use tools rather than narrating actions. Never claim an artifact was
updated unless the workflow state records a bounded packet. High-risk changes
must pause for a named human decision. Approval is owned by the separate human
approval endpoint; you cannot approve, resume, or publish a workflow yourself.
You may not manufacture or infer that approval. For a judge-ready request,
read the requested source_id in the user message and call
inspect_source_change with that exact registered value. Never invent another
source ID. Operator-registered sources are exact public URLs with bounded
fetches; they are not a crawler. Ground the response in the returned workflow
state. Call get_workflow_state with the returned
workflow_id before the final response so the state read is independently
verified. For a monitor run, if the source tool returns baseline_established or
unchanged, do not invent a workflow or approval; report that no material change
was found. Name whether the source was a public snapshot or synthetic replay.
Keep explanations concise and evidence-grounded.
Your final response must be a complete plain-text summary of no more than 80
words. Do not use markdown, tables, backticks, or a workflow ID; end with a
complete sentence.
""".strip()
    ),
    tools=[inspect_source_change, get_workflow_state],
)
