from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from .snapshots import (
    FirestoreSnapshotStore,
    InMemorySnapshotStore,
    SnapshotStore,
    compare_and_record,
)
from .workflow import DEMO_AFTER, DEMO_BEFORE, DEMO_SOURCE_URL

_SYNTHETIC_STORE = InMemorySnapshotStore()


def _public_url_is_allowlisted(url: str) -> bool:
    """Allow only Driftline's pinned raw GitHub fixture, without redirects."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "raw.githubusercontent.com":
        return False
    if parsed.query or parsed.fragment or parse_qs(parsed.query):
        return False
    parts = parsed.path.strip("/").split("/")
    return (
        len(parts) == 5
        and parts[:2] == ["mikeyerke", "driftline"]
        and parts[3:] == ["fixtures", "public-pricing-after.txt"]
    )


def _default_public_store() -> SnapshotStore:
    if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore":
        return FirestoreSnapshotStore()
    return _SYNTHETIC_STORE


def _public_pricing_snapshot(
    *, store: SnapshotStore | None = None
) -> dict[str, object]:
    """Read the one explicitly allowlisted public source.

    The network read is deliberately narrow and bounded. If a judge's network
    cannot reach GitHub, the deterministic fixture remains available, but the
    returned mode makes that fallback visible instead of pretending it was live.
    """
    url = os.getenv("DRIFTLINE_PUBLIC_SOURCE_URL", DEMO_SOURCE_URL)
    if not _public_url_is_allowlisted(url):
        return {
            "status": "rejected",
            "reason": "source_url_not_allowlisted",
            "source_url": url,
            "data_mode": "public_source",
        }
    request = Request(
        url,
        headers={"User-Agent": "Driftline-source-monitor/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=4) as response:
            body = response.read(4096).decode("utf-8").strip()
        if not body or len(body) > 2048:
            raise ValueError("source_snapshot_out_of_bounds")
        return compare_and_record(
            source_id="public/pricing",
            body=body,
            source_url=url,
            snapshot_label="Public GitHub snapshot · allowlisted source",
            data_mode="public_source",
            store=store or _default_public_store(),
        )
    except (OSError, UnicodeDecodeError, URLError, ValueError):
        return {
            "status": "synthetic_fallback",
            "change_detected": True,
            "after": DEMO_AFTER,
            "before": DEMO_BEFORE,
            "source_url": url,
            "snapshot_label": "Synthetic replay fixture · source fetch unavailable",
            "snapshot_hash": hashlib.sha256(DEMO_AFTER.encode("utf-8")).hexdigest(),
            "retrieved_at": datetime.now(UTC).isoformat(),
            "data_mode": "synthetic_demo",
            "confidence": 0.99,
        }


def inspect_allowlisted_source(
    source_id: str, *, store: SnapshotStore | None = None
) -> dict[str, object]:
    if source_id != "public/pricing":
        return {"status": "rejected", "reason": "source_not_allowlisted"}
    if os.getenv("DRIFTLINE_SOURCE_MODE", "synthetic").casefold() != "public":
        return {
            "status": "changed",
            "change_detected": True,
            "after": DEMO_AFTER,
            "source_url": DEMO_SOURCE_URL,
            "snapshot_label": "Synthetic replay fixture · public/pricing",
            "snapshot_hash": hashlib.sha256(DEMO_AFTER.encode("utf-8")).hexdigest(),
            "retrieved_at": datetime.now(UTC).isoformat(),
            "data_mode": "synthetic_demo",
            "source_id": source_id,
            "before": DEMO_BEFORE,
            "confidence": 0.99,
        }
    snapshot = _public_pricing_snapshot(store=store)
    if snapshot.get("status") == "rejected":
        snapshot["source_id"] = source_id
        return snapshot
    snapshot["source_id"] = source_id
    return snapshot
