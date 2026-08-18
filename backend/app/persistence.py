from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from google.cloud import firestore

from .models import (
    ArtifactImpact,
    JobState,
    SourceEvidence,
    Stage,
    WorkflowState,
    WorkflowStatus,
    utc_now,
)

COLLECTION = "driftline_workflows"
JOBS_COLLECTION = "driftline_jobs"


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
        artifact_packets=[dict(item) for item in payload.get("artifact_packets", [])],
        agent_trace=payload.get("agent_trace"),
        created_at=payload.get("created_at") or utc_now(),
        updated_at=payload.get("updated_at") or utc_now(),
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
        event_id = event.get("event_id") or f"event-{index:04d}"
        audit_collection.document(event_id).set(event)


def load_workflow(workflow_id: str) -> WorkflowState | None:
    """Load a workflow from Firestore, when durable persistence is enabled."""
    if not _enabled():
        return None
    snapshot = _client().collection(COLLECTION).document(workflow_id).get()
    if not snapshot.exists:
        return None
    return _state_from_dict(snapshot.to_dict() or {})


def persist_job(job: JobState) -> None:
    if not _enabled():
        return
    payload = job.to_dict()
    payload["updated_at"] = datetime.now(UTC).isoformat()
    _client().collection(JOBS_COLLECTION).document(job.job_id).set(payload)


def load_job(job_id: str) -> JobState | None:
    if not _enabled():
        return None
    snapshot = _client().collection(JOBS_COLLECTION).document(job_id).get()
    if not snapshot.exists:
        return None
    payload = snapshot.to_dict() or {}
    return JobState(
        job_id=payload["job_id"],
        kind=payload.get("kind", "change_scan"),
        status=payload.get("status", "queued"),
        query=payload.get("query", ""),
        user_id=payload.get("user_id", "demo-operator"),
        workflow_id=payload.get("workflow_id"),
        model=payload.get("model"),
        execution_mode=payload.get("execution_mode"),
        tool_calls=list(payload.get("tool_calls", [])),
        event_count=int(payload.get("event_count", 0)),
        response=payload.get("response", ""),
        error=payload.get("error"),
        created_at=payload.get("created_at") or "",
        updated_at=payload.get("updated_at") or "",
    )


def update_jobs_for_workflow(workflow_id: str, status: str) -> None:
    """Keep durable job status aligned after a human decision transition."""
    if not _enabled():
        return
    now = datetime.now(UTC).isoformat()
    query = (
        _client().collection(JOBS_COLLECTION).where("workflow_id", "==", workflow_id)
    )
    for snapshot in query.stream():
        snapshot.reference.update({"status": status, "updated_at": now})
