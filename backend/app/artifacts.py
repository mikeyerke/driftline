"""Versioned, evidence-carrying action artifacts in the isolated bucket."""

from __future__ import annotations

import json
import os
from typing import Any

from .models import WorkflowState
from .workflow import packet_markdown


def persist_action_artifact(state: WorkflowState, *, kind: str) -> dict[str, Any]:
    """Write one immutable packet or rollback marker when storage is configured.

    The object path is deterministic for a workflow/action pair. Cloud Storage
    object versioning is enabled on the dedicated bucket, so a later correction
    never destroys the original evidence. No signed URL is returned to callers.
    """
    bucket_name = os.getenv("DRIFTLINE_ARTIFACT_BUCKET", "").strip()
    action = state.action_record or {}
    action_id = str(action.get("action_id", "unknown"))
    if not bucket_name:
        return {"storage_status": "not_configured"}

    try:
        from google.cloud import storage

        client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
        bucket = client.bucket(bucket_name)
        suffix = "packet.md" if kind == "active" else "rollback.json"
        name = f"actions/{state.workflow_id}/{action_id}/{suffix}"
        blob = bucket.blob(name)
        if kind == "active":
            body = packet_markdown(state).encode("utf-8")
            content_type = "text/markdown; charset=utf-8"
        else:
            body = json.dumps(
                {
                    "workflow_id": state.workflow_id,
                    "action_id": action_id,
                    "status": "reversed",
                    "evidence_hash": (
                        state.evidence.evidence_hash if state.evidence else None
                    ),
                    "external_systems_changed": False,
                    "reversible": True,
                },
                sort_keys=True,
            ).encode("utf-8")
            content_type = "application/json"
        blob.upload_from_string(body, content_type=content_type)
        generation = str(blob.generation) if blob.generation is not None else None
        return {
            "storage_status": "persisted",
            "artifact_uri": f"gs://{bucket_name}/{name}",
            "artifact_generation": generation,
            "artifact_kind": kind,
        }
    except Exception:  # noqa: BLE001 - storage failures are recorded, never raised
        # Storage is an evidence enhancement, never a reason to claim that a
        # sandbox action changed an external system. The action remains visible
        # and explicitly records the failed persistence attempt.
        return {"storage_status": "failed", "artifact_kind": kind}
