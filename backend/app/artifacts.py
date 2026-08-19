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
            ).encode()
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


def persist_operational_output(state: WorkflowState, *, kind: str) -> dict[str, Any]:
    """Publish one approved output into Driftline's isolated operational lane.

    This is the first real downstream side effect: an approved, low-risk packet
    becomes a versioned Google Cloud Storage object under a separate prefix.
    Undo never deletes evidence; it writes a signed-by-state reversal marker and
    reports the operational output as reversed.
    """

    bucket_name = os.getenv("DRIFTLINE_ARTIFACT_BUCKET", "").strip()
    action = state.action_record or {}
    action_id = str(action.get("action_id", "unknown"))
    packet = next(
        (item for item in state.artifact_packets if item.get("status") == "packet_ready"),
        None,
    )
    if kind == "active" and packet is None:
        return {"operational_status": "not_eligible"}
    if not bucket_name:
        return {"operational_status": "not_configured"}

    try:
        from google.cloud import storage

        client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
        bucket = client.bucket(bucket_name)
        if kind == "active":
            name = f"operational-outputs/{state.workflow_id}/{action_id}/approved.md"
            evidence = state.evidence
            body = (
                "# Approved Driftline operational output\n\n"
                f"- Workflow: `{state.workflow_id}`\n"
                f"- Action: `{action_id}`\n"
                f"- Source: {evidence.source_name if evidence else 'Unknown'}\n"
                f"- Evidence hash: `{evidence.evidence_hash if evidence else 'none'}`\n"
                f"- Owner: {packet['owner']}\n"
                f"- Artifact: {packet['artifact']}\n"
                "- Operational status: **Active**\n"
                "- External customer systems changed: **No**\n\n"
                "## Approved content\n\n"
                f"{packet['content']}\n"
            ).encode()
            content_type = "text/markdown; charset=utf-8"
        else:
            name = f"operational-outputs/{state.workflow_id}/{action_id}/reversed.json"
            body = json.dumps(
                {
                    "workflow_id": state.workflow_id,
                    "action_id": action_id,
                    "status": "reversed",
                    "evidence_hash": (
                        state.evidence.evidence_hash if state.evidence else None
                    ),
                    "external_customer_systems_changed": False,
                    "reversible": True,
                },
                sort_keys=True,
            ).encode("utf-8")
            content_type = "application/json"
        blob = bucket.blob(name)
        blob.metadata = {
            "driftline-workflow": state.workflow_id,
            "driftline-action": action_id,
            "driftline-kind": kind,
        }
        blob.upload_from_string(body, content_type=content_type)
        return {
            "operational_status": "active" if kind == "active" else "reversed",
            "operational_output_uri": f"gs://{bucket_name}/{name}",
            "operational_output_generation": (
                str(blob.generation) if blob.generation is not None else None
            ),
        }
    except Exception:  # noqa: BLE001 - state remains explicit if storage is down
        return {"operational_status": "failed"}
