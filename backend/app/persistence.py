from __future__ import annotations

import base64
import os
import time
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any
from uuid import uuid4

from google.api_core.exceptions import AlreadyExists, InvalidArgument
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
JOB_FAILURES_COLLECTION = "driftline_job_failures"
OUTCOMES_COLLECTION = "driftline_outcome_measurements"
SALESFORCE_COLLECTION = "driftline_salesforce_connections"
SALESFORCE_OAUTH_STATES_COLLECTION = "driftline_salesforce_oauth_states"
CONNECTOR_BINDINGS_COLLECTION = "driftline_connector_bindings"
TENANTS_COLLECTION = "driftline_tenants"
TENANT_MEMBERSHIPS_COLLECTION = "driftline_tenant_memberships"
TENANT_AUDIT_COLLECTION = "driftline_tenant_audit_events"
TENANT_USAGE_COLLECTION = "driftline_tenant_usage"
TENANT_RATE_LIMITS_COLLECTION = "driftline_tenant_rate_limits"
TENANT_CONNECTOR_PROFILES_COLLECTION = "driftline_tenant_connector_profiles"
CREDENTIAL_ACCESS_COLLECTION = "driftline_credential_access_events"
TENANT_CREDENTIALS_SUBCOLLECTION = "credentials"
_connector_bindings_memory: dict[tuple[str, str], dict[str, Any]] = {}
_connector_profiles_memory: dict[tuple[str, str], dict[str, Any]] = {}
_tenants_memory: dict[str, dict[str, Any]] = {}
_tenant_memberships_memory: dict[tuple[str, str], dict[str, Any]] = {}
_tenant_audit_memory: list[dict[str, Any]] = []
_tenant_usage_memory: dict[tuple[str, str], dict[str, Any]] = {}
_tenant_rate_limit_memory: dict[tuple[str, str, int], int] = {}
_job_failures_memory: dict[str, dict[str, Any]] = {}
_credential_access_memory: list[dict[str, Any]] = []
_tenant_provision_lock = Lock()


def _enabled() -> bool:
    return os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"


def _retention_expiry() -> datetime:
    try:
        days = int(os.getenv("DRIFTLINE_RETENTION_DAYS", "30"))
    except ValueError:
        days = 30
    return datetime.now(UTC) + timedelta(days=max(1, min(days, 3650)))


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
        tenant_id=payload.get("tenant_id"),
        stage=Stage(payload.get("stage", Stage.MONITOR.value)),
        status=WorkflowStatus(payload.get("status", WorkflowStatus.RUNNING.value)),
        evidence=evidence,
        impacts=impacts,
        approval=payload.get("approval"),
        events=events,
        data_mode=payload.get("data_mode", "synthetic_demo"),
        artifact_packets=[dict(item) for item in payload.get("artifact_packets", [])],
        action_record=payload.get("action_record"),
        action_items=[dict(item) for item in payload.get("action_items", [])],
        impact_graph=dict(payload.get("impact_graph") or {}),
        change_card=dict(payload.get("change_card") or {}),
        integration_targets=[
            dict(item) for item in payload.get("integration_targets", [])
        ],
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
    payload["expires_at"] = _retention_expiry()
    document.set(payload)
    _create_audit_events(document.collection("audit_events"), state.events)


def _create_audit_events(
    audit_collection: Any, events: Iterable[dict[str, Any]]
) -> None:
    """Create audit events without ever overwriting an event id.

    Replaying an identical workflow snapshot is safe, but an existing id with
    different content is treated as tampering/corruption rather than silently
    replaced.  Audit history is append-only even when the parent workflow is
    updated with ``set``.
    """
    for index, event in enumerate(events):
        event_id = event.get("event_id") or f"event-{index:04d}"
        reference = audit_collection.document(event_id)
        try:
            reference.create(dict(event))
        except AlreadyExists:
            existing = reference.get()
            if not existing.exists or (existing.to_dict() or {}) != event:
                raise RuntimeError(
                    f"Audit event {event_id} already exists with different content"
                )


def compare_and_set_workflow(state: WorkflowState, expected_status: str) -> bool:
    """Persist a workflow transition only if its durable status is unchanged.

    The API mutates an in-memory workflow first because the existing workflow
    policy engine owns the transition rules.  This seam makes the final write
    a Firestore transaction, so two Cloud Run instances cannot both commit an
    approval or reopen transition from the same prior status.
    """
    if not _enabled():
        persist_workflow(state)
        return True

    client = _client()
    document = client.collection(COLLECTION).document(state.workflow_id)
    payload = state.to_dict()
    payload["updated_at"] = datetime.now(UTC).isoformat()
    payload["expires_at"] = _retention_expiry()
    @firestore.transactional
    def transition(tx: Any) -> bool:
        snapshot = document.get(transaction=tx)
        if not snapshot.exists:
            return False
        current = snapshot.to_dict() or {}
        if current.get("status") != expected_status:
            return False
        tx.set(document, payload)
        return True

    # Firestore can expire a transaction during a cold-start/network hiccup.
    # Retry once with a fresh transaction; never reuse a transaction object
    # after an unsuccessful commit attempt.
    committed = False
    for attempt in range(2):
        try:
            committed = transition(client.transaction())
            break
        except InvalidArgument as exc:
            if "transaction" not in str(exc).casefold() or attempt == 1:
                raise
            time.sleep(0.05)
    if committed:
        _create_audit_events(document.collection("audit_events"), state.events)
    return committed


def load_workflow(workflow_id: str) -> WorkflowState | None:
    """Load a workflow from Firestore, when durable persistence is enabled."""
    if not _enabled():
        return None
    snapshot = _client().collection(COLLECTION).document(workflow_id).get()
    if not snapshot.exists:
        return None
    return _state_from_dict(snapshot.to_dict() or {})


def list_workflows(limit: int = 50) -> list[WorkflowState]:
    """Return a bounded durable workflow window for change-memory summaries."""
    if not _enabled():
        return []
    bounded_limit = max(1, min(limit, 100))
    query = (
        _client()
        .collection(COLLECTION)
        .order_by("updated_at", direction=firestore.Query.DESCENDING)
        .limit(bounded_limit)
    )
    return [
        _state_from_dict(snapshot.to_dict() or {})
        for snapshot in query.stream()
    ]


def persist_job(job: JobState) -> None:
    if not _enabled():
        return
    payload = job.to_dict()
    payload["updated_at"] = datetime.now(UTC).isoformat()
    payload["expires_at"] = _retention_expiry()
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
        tenant_id=payload.get("tenant_id"),
        run_mode=payload.get("run_mode", "demo"),
        workflow_id=payload.get("workflow_id"),
        model=payload.get("model"),
        execution_mode=payload.get("execution_mode"),
        tool_calls=list(payload.get("tool_calls", [])),
        event_count=int(payload.get("event_count", 0)),
        response=payload.get("response", ""),
        error=payload.get("error"),
        claim_id=payload.get("claim_id"),
        run_attempts=int(payload.get("run_attempts", 0)),
        created_at=payload.get("created_at") or "",
        updated_at=payload.get("updated_at") or "",
    )


def list_jobs(limit: int = 8) -> list[JobState]:
    """Return the newest durable jobs for the operator run history."""
    bounded_limit = max(1, min(limit, 50))
    if not _enabled():
        return []
    query = (
        _client()
        .collection(JOBS_COLLECTION)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(bounded_limit)
    )
    jobs: list[JobState] = []
    for snapshot in query.stream():
        payload = snapshot.to_dict() or {}
        jobs.append(
            JobState(
                job_id=payload["job_id"],
                kind=payload.get("kind", "change_scan"),
                status=payload.get("status", "queued"),
                query=payload.get("query", ""),
                user_id=payload.get("user_id", "demo-operator"),
                tenant_id=payload.get("tenant_id"),
                run_mode=payload.get("run_mode", "demo"),
                workflow_id=payload.get("workflow_id"),
                model=payload.get("model"),
                execution_mode=payload.get("execution_mode"),
                tool_calls=list(payload.get("tool_calls", [])),
                event_count=int(payload.get("event_count", 0)),
                response=payload.get("response", ""),
                error=payload.get("error"),
                claim_id=payload.get("claim_id"),
                run_attempts=int(payload.get("run_attempts", 0)),
                created_at=payload.get("created_at") or "",
                updated_at=payload.get("updated_at") or "",
            )
        )
    return jobs


def persist_job_failure(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist one bounded dead-letter-style job failure marker.

    Cloud Tasks removes a task after its retry policy is exhausted. Keeping a
    separate metadata-only marker lets an operator see that terminal failure,
    while the normal job record remains the canonical execution history. The
    marker intentionally excludes prompts, source bodies, credentials, and
    exception text.
    """
    job_id = str(payload.get("job_id", "")).strip()
    if not job_id:
        raise ValueError("job_failure_id_required")
    safe = {
        "job_id": job_id,
        "workflow_id": str(payload.get("workflow_id", "")) or None,
        "tenant_id": str(payload.get("tenant_id", "")) or "",
        "status": "dead_lettered",
        "attempts": max(0, int(payload.get("attempts", 0))),
        "error_code": "agent_failed_after_bounded_retries",
        "failed_at": payload.get("failed_at") or utc_now(),
        "expires_at": _retention_expiry(),
    }
    _job_failures_memory[job_id] = dict(safe)
    if _enabled():
        _client().collection(JOB_FAILURES_COLLECTION).document(job_id).set(safe)
    return dict(safe)


def list_job_failures(
    tenant_id: str | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """List bounded terminal failures, optionally filtered to one tenant."""
    bounded_limit = max(1, min(limit, 100))
    if _enabled():
        collection = _client().collection(JOB_FAILURES_COLLECTION)
        query = (
            collection.where("tenant_id", "==", tenant_id)
            if tenant_id is not None
            else collection
        )
        failures = [snapshot.to_dict() or {} for snapshot in query.stream()]
    else:
        failures = [
            dict(item)
            for item in _job_failures_memory.values()
            if tenant_id is None or item.get("tenant_id") == tenant_id
        ]
    failures.sort(key=lambda item: str(item.get("failed_at", "")), reverse=True)
    return failures[:bounded_limit]


def persist_outcome_measurement(payload: dict[str, Any]) -> None:
    """Persist an aggregate operator-reported outcome without raw customer data."""
    if not _enabled():
        return
    stored = dict(payload)
    stored["expires_at"] = _retention_expiry()
    _client().collection(OUTCOMES_COLLECTION).document(
        str(payload["measurement_id"])
    ).create(stored)


def list_outcome_measurements(limit: int = 50) -> list[dict[str, Any]]:
    """Return a bounded, redacted outcome ledger for the operator console."""
    if not _enabled():
        return []
    bounded_limit = max(1, min(limit, 100))
    query = (
        _client()
        .collection(OUTCOMES_COLLECTION)
        .order_by("captured_at", direction=firestore.Query.DESCENDING)
        .limit(bounded_limit)
    )
    return [
        {
            key: value
            for key, value in (snapshot.to_dict() or {}).items()
            if key not in {"operator_email", "identity_subject"}
        }
        for snapshot in query.stream()
    ]


def persist_salesforce_connection(payload: dict[str, Any]) -> None:
    """Persist Salesforce connection metadata without storing bearer tokens.

    The refresh token is kept in Secret Manager; this document is only the
    tenant-scoped pointer and non-sensitive connection health metadata.
    """
    if not _enabled():
        return
    tenant_id = str(payload["tenant_id"])
    safe = {
        key: value
        for key, value in payload.items()
        if key not in {"access_token", "refresh_token", "client_secret"}
    }
    _client().collection(SALESFORCE_COLLECTION).document(tenant_id).set(safe)


def load_salesforce_connection(tenant_id: str) -> dict[str, Any] | None:
    if not _enabled():
        return None
    snapshot = _client().collection(SALESFORCE_COLLECTION).document(tenant_id).get()
    return snapshot.to_dict() if snapshot.exists else None


def delete_salesforce_connection(tenant_id: str) -> None:
    if not _enabled():
        return
    _client().collection(SALESFORCE_COLLECTION).document(tenant_id).delete()


def persist_salesforce_oauth_state(state: str, payload: dict[str, Any]) -> None:
    if not _enabled():
        return
    _client().collection(SALESFORCE_OAUTH_STATES_COLLECTION).document(state).set(payload)


def consume_salesforce_oauth_state(state: str) -> dict[str, Any] | None:
    if not _enabled():
        return None
    document = _client().collection(SALESFORCE_OAUTH_STATES_COLLECTION).document(state)
    snapshot = document.get()
    if not snapshot.exists:
        return None
    document.delete()
    return snapshot.to_dict()


def persist_connector_binding(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist connector-to-tenant secret metadata, never credential values.

    A binding is control-plane configuration, not ephemeral customer content.
    It must survive the normal content-retention window until an owner
    disconnects or rotates it, so it intentionally has no Firestore TTL field.
    """
    from .tenant import validate_connector_name, validate_tenant_id

    tenant_id = validate_tenant_id(str(payload["tenant_id"]))
    connector = validate_connector_name(str(payload["connector"]))
    safe = {
        key: value
        for key, value in payload.items()
        if key not in {"token", "secret_value", "access_token", "refresh_token"}
    }
    safe.setdefault("updated_at", utc_now())
    safe.pop("expires_at", None)
    # Every binding carries the same derived namespace used by the broker.
    # Older records may not have this field; the migration-compatible read path
    # below fills it only when the active project identity is available.
    if "credential_namespace" not in safe:
        try:
            from .tenant import tenant_credential_namespace

            safe["credential_namespace"] = tenant_credential_namespace(
                tenant_id, connector
            )
        except (ValueError, TypeError):
            # Local contract tests do not need a configured Google project.
            pass
    _connector_bindings_memory[(tenant_id, connector)] = dict(safe)
    if _enabled():
        # Canonical SaaS layout: credentials live below their tenant document,
        # preventing a caller from querying one flat global credential index.
        _client().collection(TENANTS_COLLECTION).document(tenant_id).collection(
            TENANT_CREDENTIALS_SUBCOLLECTION
        ).document(connector).set(safe)
        # Keep the legacy collection in sync during the zero-downtime migration
        # so an older revision can still read an already-provisioned binding.
        _client().collection(CONNECTOR_BINDINGS_COLLECTION).document(
            f"{tenant_id}:{connector}"
        ).set(safe)
    return dict(safe)


def _hydrate_credential_namespace(
    payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Backfill namespace metadata on a legacy binding without reading a secret."""
    if not payload or payload.get("credential_namespace"):
        return dict(payload) if payload else None
    tenant_id = str(payload.get("tenant_id", ""))
    connector = str(payload.get("connector", ""))
    try:
        from .tenant import tenant_credential_namespace

        namespace = tenant_credential_namespace(tenant_id, connector)
    except (ValueError, TypeError):
        return dict(payload)
    hydrated = {**payload, "credential_namespace": namespace}
    _connector_bindings_memory[(tenant_id, connector)] = dict(hydrated)
    if _enabled():
        _client().collection(TENANTS_COLLECTION).document(tenant_id).collection(
            TENANT_CREDENTIALS_SUBCOLLECTION
        ).document(connector).set(hydrated)
        _client().collection(CONNECTOR_BINDINGS_COLLECTION).document(
            f"{tenant_id}:{connector}"
        ).set(hydrated)
    return hydrated


def load_connector_binding(tenant_id: str, connector: str) -> dict[str, Any] | None:
    """Load one tenant connector binding without reading the referenced secret."""
    from .tenant import validate_connector_name, validate_tenant_id

    tenant_id = validate_tenant_id(tenant_id)
    connector = validate_connector_name(connector)
    if _enabled():
        canonical = (
            _client()
            .collection(TENANTS_COLLECTION)
            .document(tenant_id)
            .collection(TENANT_CREDENTIALS_SUBCOLLECTION)
            .document(connector)
            .get()
        )
        if canonical.exists:
            return _hydrate_credential_namespace(canonical.to_dict())
        snapshot = _client().collection(CONNECTOR_BINDINGS_COLLECTION).document(
            f"{tenant_id}:{connector}"
        ).get()
        if snapshot.exists:
            return _hydrate_credential_namespace(snapshot.to_dict())
        return None
    payload = _connector_bindings_memory.get((tenant_id, connector))
    return _hydrate_credential_namespace(payload)


def list_connector_bindings(tenant_id: str) -> list[dict[str, Any]]:
    """Return bounded, metadata-only bindings for an authenticated tenant."""
    from .tenant import validate_tenant_id

    tenant_id = validate_tenant_id(tenant_id)
    if _enabled():
        canonical = list(
            _client()
            .collection(TENANTS_COLLECTION)
            .document(tenant_id)
            .collection(TENANT_CREDENTIALS_SUBCOLLECTION)
            .stream()
        )
        if canonical:
            return [
                _hydrate_credential_namespace(snapshot.to_dict()) or {}
                for snapshot in canonical
            ]
        query = _client().collection(CONNECTOR_BINDINGS_COLLECTION).where(
            "tenant_id", "==", tenant_id
        )
        return [
            _hydrate_credential_namespace(snapshot.to_dict()) or {}
            for snapshot in query.stream()
        ]
    return [
        dict(payload)
        for (bound_tenant, _), payload in _connector_bindings_memory.items()
        if bound_tenant == tenant_id
    ]


def persist_credential_access_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Append metadata for one short-lived credential lease.

    The access ledger is deliberately separate from connector bindings: a
    binding describes durable control-plane state, while this collection is a
    bounded operational trail of which tenant/operation resolved a pinned
    secret version.  Credential values and provider response bodies are
    rejected before persistence and every event receives the normal retention
    expiry.
    """
    forbidden = {
        "value",
        "token",
        "secret_value",
        "access_token",
        "refresh_token",
        "client_secret",
    }
    safe = {key: value for key, value in payload.items() if key not in forbidden}
    safe.setdefault("event_id", f"credential-access-{uuid4().hex}")
    safe.setdefault("created_at", utc_now())
    safe["expires_at"] = _retention_expiry()
    _credential_access_memory.append(dict(safe))
    if _enabled():
        _client().collection(CREDENTIAL_ACCESS_COLLECTION).document(
            str(safe["event_id"])
        ).create(safe)
    return dict(safe)


def list_credential_access_events(
    tenant_id: str, limit: int = 100
) -> list[dict[str, Any]]:
    """Return one tenant's bounded, metadata-only credential access trail."""
    bounded_limit = max(1, min(limit, 200))
    if _enabled():
        query = _client().collection(CREDENTIAL_ACCESS_COLLECTION).where(
            "tenant_id", "==", tenant_id
        )
        events = [snapshot.to_dict() or {} for snapshot in query.stream()]
    else:
        events = [
            dict(event)
            for event in _credential_access_memory
            if event.get("tenant_id") == tenant_id
        ]
    events.sort(key=lambda event: str(event.get("created_at", "")), reverse=True)
    return events[:bounded_limit]


def persist_connector_profile(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist non-secret target metadata for one tenant connector.

    Profiles are control-plane configuration and intentionally have no content
    TTL. The validator rejects credentials and arbitrary provider fields before
    anything reaches Firestore.
    """
    from .tenant import validate_connector_name, validate_connector_profile

    tenant_id = str(payload["tenant_id"])
    connector = validate_connector_name(str(payload["connector"]))
    settings = validate_connector_profile(
        connector, dict(payload.get("settings") or {})
    )
    safe = {
        "tenant_id": tenant_id,
        "connector": connector,
        "settings": settings,
        "status": str(payload.get("status", "active")),
        "updated_at": payload.get("updated_at", utc_now()),
    }
    _connector_profiles_memory[(tenant_id, connector)] = dict(safe)
    if _enabled():
        _client().collection(TENANT_CONNECTOR_PROFILES_COLLECTION).document(
            f"{tenant_id}:{connector}"
        ).set(safe)
    return dict(safe)


def load_connector_profile(tenant_id: str, connector: str) -> dict[str, Any] | None:
    """Load one tenant's non-secret destination profile."""
    from .tenant import validate_connector_name

    safe_connector = validate_connector_name(connector)
    if _enabled():
        snapshot = _client().collection(
            TENANT_CONNECTOR_PROFILES_COLLECTION
        ).document(f"{tenant_id}:{safe_connector}").get()
        if snapshot.exists:
            return snapshot.to_dict()
        return None
    payload = _connector_profiles_memory.get((tenant_id, safe_connector))
    return dict(payload) if payload else None


def list_connector_profiles(tenant_id: str) -> list[dict[str, Any]]:
    """List one tenant's bounded, non-secret connector profiles."""
    if _enabled():
        query = _client().collection(TENANT_CONNECTOR_PROFILES_COLLECTION).where(
            "tenant_id", "==", tenant_id
        )
        return [snapshot.to_dict() or {} for snapshot in query.stream()]
    return [
        dict(payload)
        for (bound_tenant, _), payload in _connector_profiles_memory.items()
        if bound_tenant == tenant_id
    ]


def persist_tenant_audit_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Append one tenant control-plane event without accepting credentials."""
    safe = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "token",
            "secret_value",
            "access_token",
            "refresh_token",
            "client_secret",
        }
    }
    safe.setdefault("event_id", f"tenant-audit-{uuid4().hex}")
    safe.setdefault("created_at", utc_now())
    _tenant_audit_memory.append(dict(safe))
    if _enabled():
        _client().collection(TENANT_AUDIT_COLLECTION).document(
            str(safe["event_id"])
        ).create(safe)
    return dict(safe)


def list_tenant_audit_events(tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return bounded metadata-only control-plane events for one tenant."""
    safe_limit = max(1, min(limit, 200))
    if _enabled():
        query = _client().collection(TENANT_AUDIT_COLLECTION).where(
            "tenant_id", "==", tenant_id
        )
        events = [snapshot.to_dict() or {} for snapshot in query.stream()]
    else:
        events = [
            dict(event)
            for event in _tenant_audit_memory
            if event.get("tenant_id") == tenant_id
        ]
    events.sort(key=lambda event: str(event.get("created_at", "")), reverse=True)
    return events[:safe_limit]


_USAGE_METRICS = frozenset({"agent_calls", "workflow_mutations", "monitor_jobs"})


def _usage_period(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).strftime("%Y-%m")


def record_tenant_usage(
    tenant_id: str, metric: str, amount: int = 1, *, period: str | None = None
) -> dict[str, Any]:
    """Increment bounded tenant-period usage without retaining request content."""
    if metric not in _USAGE_METRICS or amount <= 0:
        raise ValueError("usage_metric_invalid")
    usage_period = period or _usage_period()
    key = (tenant_id, usage_period)
    payload = _tenant_usage_memory.setdefault(
        key,
        {
            "tenant_id": tenant_id,
            "period": usage_period,
            "agent_calls": 0,
            "workflow_mutations": 0,
            "monitor_jobs": 0,
        },
    )
    payload[metric] = int(payload.get(metric, 0)) + amount
    payload["updated_at"] = utc_now()
    if _enabled():
        _client().collection(TENANT_USAGE_COLLECTION).document(
            f"{tenant_id}:{usage_period}"
        ).set(
            {
                "tenant_id": tenant_id,
                "period": usage_period,
                metric: firestore.Increment(amount),
                "updated_at": payload["updated_at"],
            },
            merge=True,
        )
    return dict(payload)


def reserve_tenant_rate_limit(
    tenant_id: str,
    metric: str,
    limit: int,
    window_seconds: int,
    *,
    now: float | None = None,
) -> bool:
    """Atomically reserve one tenant quota slot for a fixed time window.

    Firestore deployments use a transaction so multiple Cloud Run instances
    cannot race past the same tenant limit. Local runs retain a deterministic
    in-memory fallback for tests and development.
    """
    if metric not in _USAGE_METRICS or limit <= 0 or window_seconds <= 0:
        raise ValueError("rate_limit_arguments_invalid")
    timestamp = float(now if now is not None else time.time())
    window_start = int(timestamp // window_seconds) * window_seconds
    memory_key = (tenant_id, metric, window_start)
    if not _enabled():
        current = _tenant_rate_limit_memory.get(memory_key, 0)
        if current >= limit:
            return False
        _tenant_rate_limit_memory[memory_key] = current + 1
        return True

    document = _client().collection(TENANT_RATE_LIMITS_COLLECTION).document(
        f"{tenant_id}:{metric}:{window_start}"
    )
    transaction = _client().transaction()

    @firestore.transactional
    def reserve(transaction: firestore.Transaction) -> bool:
        snapshot = next(iter(transaction.get(document)))
        current = int((snapshot.to_dict() or {}).get("count", 0)) if snapshot.exists else 0
        if current >= limit:
            return False
        expires_at = datetime.fromtimestamp(
            window_start + window_seconds, UTC
        )
        transaction.set(
            document,
            {
                "tenant_id": tenant_id,
                "metric": metric,
                "window_start": window_start,
                "count": current + 1,
                "limit": limit,
                "expires_at": expires_at,
                "updated_at": utc_now(),
            },
            merge=True,
        )
        return True

    return bool(reserve(transaction))


def load_tenant_usage(tenant_id: str, period: str | None = None) -> dict[str, Any]:
    """Return one tenant's aggregate usage for the requested month."""
    usage_period = period or _usage_period()
    if _enabled():
        snapshot = _client().collection(TENANT_USAGE_COLLECTION).document(
            f"{tenant_id}:{usage_period}"
        ).get()
        if snapshot.exists:
            return snapshot.to_dict() or {}
    return dict(
        _tenant_usage_memory.get(
            (tenant_id, usage_period),
            {
                "tenant_id": tenant_id,
                "period": usage_period,
                "agent_calls": 0,
                "workflow_mutations": 0,
                "monitor_jobs": 0,
            },
        )
    )


def persist_tenant(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist non-secret control-plane metadata for one tenant."""
    tenant_id = str(payload["tenant_id"])
    safe = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "token",
            "secret_value",
            "access_token",
            "refresh_token",
            "client_secret",
        }
    }
    safe.setdefault("status", "active")
    safe.setdefault("updated_at", utc_now())
    # Tenant configuration is retained until an explicit deprovisioning action;
    # content TTL must never silently remove the tenant control plane.
    safe.pop("expires_at", None)
    _tenants_memory[tenant_id] = dict(safe)
    if _enabled():
        _client().collection(TENANTS_COLLECTION).document(tenant_id).set(safe)
    return dict(safe)


def provision_tenant_metadata(
    tenant_payload: dict[str, Any],
    membership_payload: dict[str, Any],
    *,
    audit_payload: dict[str, Any] | None = None,
) -> bool:
    """Atomically create/reactivate a tenant and its initial owner metadata.

    Returns ``False`` when another active tenant already owns the identifier.
    No credential-shaped fields are persisted, and the Firestore path uses a
    transaction so concurrent Cloud Run instances cannot swap the owner email.
    When supplied, the initial audit event is committed in that same
    transaction; a tenant can never be visible without its bootstrap record.
    """
    tenant_id = str(tenant_payload["tenant_id"])
    email = str(membership_payload["email"]).strip().casefold()
    safe_tenant = {
        key: value
        for key, value in tenant_payload.items()
        if key
        not in {
            "token",
            "secret_value",
            "access_token",
            "refresh_token",
            "client_secret",
        }
    }
    safe_tenant.setdefault("status", "active")
    safe_tenant.setdefault("updated_at", utc_now())
    safe_tenant.pop("expires_at", None)
    safe_membership = {
        key: value
        for key, value in membership_payload.items()
        if key
        not in {
            "token",
            "secret_value",
            "access_token",
            "refresh_token",
            "identity_token",
        }
    }
    safe_membership["tenant_id"] = tenant_id
    safe_membership["email"] = email
    safe_membership.setdefault("status", "active")
    safe_membership.setdefault("updated_at", utc_now())
    safe_membership.pop("expires_at", None)
    membership_id = base64.urlsafe_b64encode(
        f"{tenant_id}:{email}".encode()
    ).decode("ascii").rstrip("=")
    safe_membership["membership_id"] = membership_id

    safe_audit: dict[str, Any] | None = None
    if audit_payload is not None:
        safe_audit = {
            key: value
            for key, value in audit_payload.items()
            if key
            not in {
                "token",
                "secret_value",
                "access_token",
                "refresh_token",
                "client_secret",
            }
        }
        safe_audit.setdefault("event_id", f"tenant-audit-{uuid4().hex}")
        safe_audit.setdefault("created_at", utc_now())
        safe_audit["tenant_id"] = tenant_id

    if not _enabled():
        with _tenant_provision_lock:
            existing = _tenants_memory.get(tenant_id)
            existing_status = str((existing or {}).get("status", "")).casefold()
            if existing and existing_status not in {"disabled", "deprovisioned"}:
                return False
            _tenants_memory[tenant_id] = dict(safe_tenant)
            _tenant_memberships_memory[(tenant_id, email)] = dict(safe_membership)
            if safe_audit is not None:
                _tenant_audit_memory.append(dict(safe_audit))
        return True

    client = _client()
    tenant_document = client.collection(TENANTS_COLLECTION).document(tenant_id)
    membership_document = client.collection(TENANT_MEMBERSHIPS_COLLECTION).document(
        membership_id
    )

    @firestore.transactional
    def provision(transaction: Any) -> bool:
        snapshot = tenant_document.get(transaction=transaction)
        existing = snapshot.to_dict() if snapshot.exists else None
        existing_status = str((existing or {}).get("status", "")).casefold()
        if existing and existing_status not in {"disabled", "deprovisioned"}:
            return False
        transaction.set(tenant_document, safe_tenant)
        transaction.set(membership_document, safe_membership)
        if safe_audit is not None:
            audit_document = client.collection(TENANT_AUDIT_COLLECTION).document(
                str(safe_audit["event_id"])
            )
            transaction.create(audit_document, safe_audit)
        return True

    created = provision(client.transaction())
    if created:
        _tenants_memory[tenant_id] = dict(safe_tenant)
        _tenant_memberships_memory[(tenant_id, email)] = dict(safe_membership)
    return created


def load_tenant(tenant_id: str) -> dict[str, Any] | None:
    """Load one tenant's metadata without connector credentials."""
    if _enabled():
        snapshot = _client().collection(TENANTS_COLLECTION).document(tenant_id).get()
        if snapshot.exists:
            return snapshot.to_dict()
        return None
    payload = _tenants_memory.get(tenant_id)
    return dict(payload) if payload else None


def persist_tenant_membership(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist one tenant membership and role without identity tokens."""
    tenant_id = str(payload["tenant_id"])
    email = str(payload["email"]).strip().casefold()
    safe = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "token",
            "secret_value",
            "access_token",
            "refresh_token",
            "identity_token",
        }
    }
    safe["tenant_id"] = tenant_id
    safe["email"] = email
    safe.setdefault("status", "active")
    safe.setdefault("updated_at", utc_now())
    safe.pop("expires_at", None)
    key = (tenant_id, email)
    document_id = base64.urlsafe_b64encode(
        f"{tenant_id}:{email}".encode()
    ).decode("ascii").rstrip("=")
    safe["membership_id"] = document_id
    _tenant_memberships_memory[key] = dict(safe)
    if _enabled():
        _client().collection(TENANT_MEMBERSHIPS_COLLECTION).document(document_id).set(
            safe
        )
    return dict(safe)


def load_tenant_membership(tenant_id: str, email: str) -> dict[str, Any] | None:
    """Load one metadata-only tenant membership."""
    normalized_email = email.strip().casefold()
    if _enabled():
        document_id = base64.urlsafe_b64encode(
            f"{tenant_id}:{normalized_email}".encode()
        ).decode("ascii").rstrip("=")
        snapshot = (
            _client()
            .collection(TENANT_MEMBERSHIPS_COLLECTION)
            .document(document_id)
            .get()
        )
        if snapshot.exists:
            return snapshot.to_dict()
        return None
    payload = _tenant_memberships_memory.get((tenant_id, normalized_email))
    return dict(payload) if payload else None


def list_tenant_memberships(tenant_id: str) -> list[dict[str, Any]]:
    """Return bounded membership metadata for one authenticated tenant."""
    if _enabled():
        query = _client().collection(TENANT_MEMBERSHIPS_COLLECTION).where(
            "tenant_id", "==", tenant_id
        )
        return [snapshot.to_dict() or {} for snapshot in query.stream()]
    return [
        dict(payload)
        for (bound_tenant, _), payload in _tenant_memberships_memory.items()
        if bound_tenant == tenant_id
    ]


def claim_job(job_id: str, claim_id: str) -> bool:
    """Atomically claim a queued job for one execution attempt.

    Cloud Tasks may deliver the same task more than once.  Only the first
    transaction that observes ``queued`` wins; later deliveries return false
    before the agent runtime is invoked.
    """
    if not _enabled():
        return True

    client = _client()
    document = client.collection(JOBS_COLLECTION).document(job_id)
    transaction = client.transaction()
    now = datetime.now(UTC).isoformat()

    @firestore.transactional
    def claim(tx: Any) -> bool:
        snapshot = document.get(transaction=tx)
        if not snapshot.exists:
            return False
        payload = snapshot.to_dict() or {}
        if payload.get("status", "queued") != "queued":
            return False
        tx.update(
            document,
            {
                "status": "running",
                "claim_id": claim_id,
                "run_attempts": firestore.Increment(1),
                "updated_at": now,
            },
        )
        return True

    return claim(transaction)


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
