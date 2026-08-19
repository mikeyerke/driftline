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
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
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
    ) -> SnapshotRecord:
        return cls(
            source_id=source_id,
            body=body,
            snapshot_hash=body_hash(body),
            source_url=source_url,
            retrieved_at=retrieved_at or utc_now(),
            data_mode=data_mode,
            snapshot_label=snapshot_label,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "body": self.body,
            "snapshot_hash": self.snapshot_hash,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "data_mode": self.data_mode,
            "snapshot_label": self.snapshot_label,
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
        )


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
        reference = self._client.collection(self._collection).document(
            _firestore_document_key(source_id)
        )
        observations = list(reference.collection("observations").stream())
        records = [
            SnapshotRecord.from_dict(snapshot.to_dict() or {})
            for snapshot in observations
        ]
        records.sort(key=lambda item: item.retrieved_at, reverse=True)
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
) -> dict[str, Any]:
    """Record a body and return an honest baseline/unchanged/changed result."""

    current = SnapshotRecord.create(
        source_id=source_id,
        body=body,
        source_url=source_url,
        data_mode=data_mode,
        snapshot_label=snapshot_label,
        retrieved_at=retrieved_at,
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
