"""Evidence-bound source snapshot storage and comparison.

The source adapter deliberately separates fetching a bounded source body from
deciding whether it is new.  That makes the monitor honest: the first read
establishes a baseline, an identical hash is unchanged, and only a different
hash is a change.  The Firestore implementation stores one latest snapshot per
allowlisted source plus an immutable observation history while the in-memory
implementation mirrors that contract for local tests and the synthetic judge
fixture.
"""

from __future__ import annotations

import base64
import hashlib
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def body_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SnapshotRecord:
    """The exact bounded body observed for one source at one point in time."""

    source_id: str
    body: str
    snapshot_hash: str
    source_url: str
    retrieved_at: str
    data_mode: str
    snapshot_label: str
    tenant_id: str | None = None
    retention_days: int | None = None

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        body: str,
        source_url: str,
        data_mode: str,
        snapshot_label: str,
        retrieved_at: str | None = None,
        tenant_id: str | None = None,
        retention_days: int | None = None,
    ) -> SnapshotRecord:
        return cls(
            source_id=source_id,
            body=body,
            snapshot_hash=body_hash(body),
            source_url=source_url,
            retrieved_at=retrieved_at or utc_now(),
            data_mode=data_mode,
            snapshot_label=snapshot_label,
            tenant_id=tenant_id,
            retention_days=retention_days,
        )

    def to_dict(self) -> dict[str, Any]:
        retention_days = self.retention_days or retention_days_for_tenant(self.tenant_id)
        return {
            "source_id": self.source_id,
            "body": self.body,
            "snapshot_hash": self.snapshot_hash,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "data_mode": self.data_mode,
            "snapshot_label": self.snapshot_label,
            "tenant_id": self.tenant_id or "",
            "retention_days": retention_days,
            # Firestore TTL can delete expired snapshots without a scheduled
            # cleanup process. The body remains bounded and append-only until
            # this explicit retention window elapses.
            "expires_at": datetime.now(UTC) + timedelta(days=retention_days),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SnapshotRecord:
        return cls(
            source_id=str(payload["source_id"]),
            body=str(payload["body"]),
            snapshot_hash=str(payload["snapshot_hash"]),
            source_url=str(payload["source_url"]),
            retrieved_at=str(payload["retrieved_at"]),
            data_mode=str(payload["data_mode"]),
            snapshot_label=str(payload["snapshot_label"]),
            tenant_id=str(payload.get("tenant_id") or "") or None,
            retention_days=int(payload.get("retention_days", 0)) or None,
        )


def retention_days_for_tenant(tenant_id: str | None = None) -> int:
    """Resolve the bounded source/audit TTL for one tenant.

    Source history is content-bearing, so tenant policy applies here as well
    as to workflow and credential metadata. Older records without a tenant
    policy continue using the deployment default.
    """
    try:
        days = int(os.getenv("DRIFTLINE_RETENTION_DAYS", "30"))
    except ValueError:
        days = 30
    days = max(1, min(days, 3650))
    if tenant_id and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore":
        try:
            from .persistence import load_tenant_policy

            days = int(load_tenant_policy(tenant_id).get("retention_days", days))
            days = max(1, min(days, 3650))
        except Exception:  # noqa: BLE001 - bounded deployment fallback.
            days = max(1, min(days, 3650))
    return days


class SnapshotStore(Protocol):
    """Store contract: atomically return the prior record and write current."""

    def record(
        self, source_id: str, current: SnapshotRecord
    ) -> SnapshotRecord | None: ...

    def history(self, source_id: str, limit: int = 20) -> list[SnapshotRecord]: ...


class InMemorySnapshotStore:
    """Small process-local store for tests and explicitly synthetic runs."""

    def __init__(self) -> None:
        self._records: dict[str, SnapshotRecord] = {}
        self._history_records: dict[str, list[SnapshotRecord]] = {}
        self._lock = threading.Lock()

    def record(self, source_id: str, current: SnapshotRecord) -> SnapshotRecord | None:
        if current.source_id != source_id:
            raise ValueError("snapshot_source_id_mismatch")
        with self._lock:
            previous = self._records.get(source_id)
            self._records[source_id] = current
            self._history_records.setdefault(source_id, []).append(current)
            return previous

    def history(self, source_id: str, limit: int = 20) -> list[SnapshotRecord]:
        bounded_limit = max(1, min(limit, 100))
        with self._lock:
            return list(reversed(self._history_records.get(source_id, [])))[
                :bounded_limit
            ]

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._history_records.clear()


def _firestore_document_key(source_id: str) -> str:
    """Encode source IDs because Firestore document IDs cannot contain '/'."""
    return (
        base64.urlsafe_b64encode(source_id.encode("utf-8")).decode("ascii").rstrip("=")
    )


class FirestoreSnapshotStore:
    """Durable latest-snapshot store for the isolated Driftline project."""

    def __init__(
        self, client: Any | None = None, collection: str = "driftline_source_snapshots"
    ) -> None:
        if client is None:
            import os

            from google.cloud import firestore

            kwargs: dict[str, Any] = {
                "database": os.getenv("FIRESTORE_DATABASE", "(default)"),
            }
            project = os.getenv("GOOGLE_CLOUD_PROJECT")
            if project:
                kwargs["project"] = project
            client = firestore.Client(**kwargs)
        self._client = client
        self._collection = collection

    def record(self, source_id: str, current: SnapshotRecord) -> SnapshotRecord | None:
        if current.source_id != source_id:
            raise ValueError("snapshot_source_id_mismatch")

        from google.cloud import firestore

        reference = self._client.collection(self._collection).document(
            _firestore_document_key(source_id)
        )
        observation_id = hashlib.sha256(
            f"{source_id}|{current.retrieved_at}|{current.snapshot_hash}".encode()
        ).hexdigest()[:32]
        observation = reference.collection("observations").document(observation_id)
        previous: list[SnapshotRecord | None] = [None]
        transaction = self._client.transaction()

        @firestore.transactional
        def write(transaction: Any) -> None:
            existing = reference.get(transaction=transaction)
            if existing.exists:
                previous[0] = SnapshotRecord.from_dict(existing.to_dict() or {})
            # The observation path is append-only. A deterministic key makes a
            # retried monitor write idempotent while the current pointer remains
            # a cheap comparison read.
            transaction.set(
                observation,
                {**current.to_dict(), "observation_id": observation_id},
                merge=False,
            )
            transaction.set(reference, current.to_dict())

        write(transaction)
        return previous[0]

    def history(self, source_id: str, limit: int = 20) -> list[SnapshotRecord]:
        bounded_limit = max(1, min(limit, 100))
        from google.cloud import firestore

        reference = self._client.collection(self._collection).document(
            _firestore_document_key(source_id)
        )
        # Ask Firestore for only the newest bounded observations.  The old
        # implementation streamed the complete append-only subcollection and
        # sorted it in Python, which made the public monitor panels grow
        # linearly with a source's history even though they only render the
        # newest page.
        observations = list(
            reference.collection("observations")
            .order_by("retrieved_at", direction=firestore.Query.DESCENDING)
            .limit(bounded_limit)
            .stream()
        )
        records = [
            SnapshotRecord.from_dict(snapshot.to_dict() or {})
            for snapshot in observations
        ]
        return records[:bounded_limit]


def compare_and_record(
    *,
    source_id: str,
    body: str,
    source_url: str,
    data_mode: str,
    snapshot_label: str,
    store: SnapshotStore,
    retrieved_at: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Record a body and return an honest baseline/unchanged/changed result."""

    current = SnapshotRecord.create(
        source_id=source_id,
        body=body,
        source_url=source_url,
        data_mode=data_mode,
        snapshot_label=snapshot_label,
        retrieved_at=retrieved_at,
        tenant_id=tenant_id,
        retention_days=retention_days_for_tenant(tenant_id),
    )
    previous = store.record(source_id, current)
    if previous is None:
        status = "baseline_established"
        before = ""
        change_detected = False
        # A baseline has no comparison, so confidence is explicitly unknown.
        confidence = 0.0
    elif previous.snapshot_hash == current.snapshot_hash:
        status = "unchanged"
        before = previous.body
        change_detected = False
        # Exact hash equality is certain, but must not look like the old 0.99
        # change confidence used by the demo replay.
        confidence = 1.0
    else:
        status = "changed"
        before = previous.body
        change_detected = True
        confidence = 0.99

    return {
        "status": status,
        "change_detected": change_detected,
        "before": before,
        "after": current.body,
        "source_id": current.source_id,
        "source_url": current.source_url,
        "snapshot_label": current.snapshot_label,
        "snapshot_hash": current.snapshot_hash,
        "previous_snapshot_hash": previous.snapshot_hash if previous else None,
        "retrieved_at": current.retrieved_at,
        "data_mode": current.data_mode,
        "confidence": confidence,
    }


def snapshot_history(
    source_id: str, *, store: SnapshotStore, limit: int = 20
) -> list[dict[str, str]]:
    """Return newest immutable observations for a bounded source."""

    return [record.to_dict() for record in store.history(source_id, limit)]
