from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

from .workflow import DEMO_AFTER, DEMO_BEFORE, DEMO_SOURCE_URL


def _public_pricing_snapshot() -> dict[str, str]:
    """Read the one explicitly allowlisted public source.

    The network read is deliberately narrow and bounded. If a judge's network
    cannot reach GitHub, the deterministic fixture remains available, but the
    returned mode makes that fallback visible instead of pretending it was live.
    """
    url = os.getenv("DRIFTLINE_PUBLIC_SOURCE_URL", DEMO_SOURCE_URL)
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
        snapshot_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        return {
            "after": body,
            "source_url": url,
            "snapshot_label": "Public GitHub snapshot · allowlisted source",
            "snapshot_hash": snapshot_hash,
            "retrieved_at": datetime.now(UTC).isoformat(),
            "data_mode": "public_source",
        }
    except (OSError, UnicodeDecodeError, URLError, ValueError):
        return {
            "after": DEMO_AFTER,
            "source_url": url,
            "snapshot_label": "Synthetic replay fixture · source fetch unavailable",
            "snapshot_hash": hashlib.sha256(DEMO_AFTER.encode("utf-8")).hexdigest(),
            "retrieved_at": datetime.now(UTC).isoformat(),
            "data_mode": "synthetic_demo",
        }


def inspect_allowlisted_source(source_id: str) -> dict[str, str]:
    if source_id != "public/pricing":
        return {"status": "rejected", "reason": "source_not_allowlisted"}
    if os.getenv("DRIFTLINE_SOURCE_MODE", "synthetic").casefold() != "public":
        return {
            "after": DEMO_AFTER,
            "source_url": DEMO_SOURCE_URL,
            "snapshot_label": "Synthetic replay fixture · public/pricing",
            "snapshot_hash": hashlib.sha256(DEMO_AFTER.encode("utf-8")).hexdigest(),
            "retrieved_at": datetime.now(UTC).isoformat(),
            "data_mode": "synthetic_demo",
            "source_id": source_id,
            "before": DEMO_BEFORE,
        }
    snapshot = _public_pricing_snapshot()
    snapshot["source_id"] = source_id
    snapshot["before"] = DEMO_BEFORE
    return snapshot
