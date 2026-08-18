from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from google.cloud import firestore

from .models import ArtifactImpact, SourceEvidence, Stage, WorkflowState, WorkflowStatus

COLLECTION = "driftline_workflows"


def _enabled() -> bool:
    return os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"


def _client() -> firestore.Client:
    kwargs: dict[str, Any] = {
        "database": os.getenv("FIRESTORE_DATABASE", "(default)"),
    }
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project:
        kwargs["project"] = project
    return firestore.Client(**kwargs)


def _state_from_dict(payload: dict[str, Any]) -> WorkflowState:
    evidence_payload = payload.get("evidence")
    evidence = (
        SourceEvidence(**evidence_payload) if evidence_payload is not None else None
    )
    impacts = [ArtifactImpact(**item) for item in payload.get("impacts", [])]
    events = [dict(item) for item in payload.get("events", [])]
    return WorkflowState(
        workflow_id=payload["workflow_id"],
        title=payload["title"],
        stage=Stage(payload.get("stage", Stage.MONITOR.value)),
        status=WorkflowStatus(payload.get("status", WorkflowStatus.RUNNING.value)),
        evidence=evidence,
        impacts=impacts,
        approval=payload.get("approval"),
        events=events,
        data_mode=payload.get("data_mode", "synthetic_demo"),
    )


def persist_workflow(state: WorkflowState) -> None:
    """Persist state and its audit events when cloud persistence is enabled."""
    if not _enabled():
        return

    client = _client()
    document = client.collection(COLLECTION).document(state.workflow_id)
    payload = state.to_dict()
    payload["updated_at"] = datetime.now(UTC).isoformat()
    document.set(payload)
    audit_collection = document.collection("audit_events")
    for index, event in enumerate(state.events):
        audit_collection.document(f"{index:04d}").set(event)


def load_workflow(workflow_id: str) -> WorkflowState | None:
    """Load a workflow from Firestore, when durable persistence is enabled."""
    if not _enabled():
        return None
    snapshot = _client().collection(COLLECTION).document(workflow_id).get()
    if not snapshot.exists:
        return None
    return _state_from_dict(snapshot.to_dict() or {})
