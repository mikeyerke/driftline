from __future__ import annotations

import os

from google.adk.agents import Agent

from .workflow import workflow_store


def inspect_source_change(source_id: str) -> dict:
    """Detect and verify a material change in an approved source."""
    if source_id != "public/pricing":
        return {"status": "rejected", "reason": "source_not_allowlisted"}
    return workflow_store.start_demo().to_dict()


def get_workflow_state(workflow_id: str) -> dict:
    """Return the evidence, stage, impacts, and audit events for a workflow."""
    return workflow_store.get(workflow_id).to_dict()


root_agent = Agent(
    name="driftline_change_operator",
    model=os.getenv("MODEL_NAME", "gemini-3.5-flash"),
    description=(
        "Autonomous enterprise change operator that turns verified source "
        "changes into bounded, auditable downstream actions."
    ),
    instruction="""
You are Driftline's change operations coordinator. Work only with approved
public or synthetic sources. Always gather immutable evidence before proposing
an action. Use tools rather than narrating actions. Never claim an artifact was
updated unless the workflow state records it. High-risk changes must pause for
a named human decision. Approval is owned by the separate human approval
endpoint; you cannot approve, resume, or publish a workflow yourself. You may
not manufacture or infer that approval.
Keep explanations concise and evidence-grounded.
""".strip(),
    tools=[inspect_source_change, get_workflow_state],
)
