"""Append-only change memory and operator work summaries.

This module is intentionally read-only. Source observations and workflow
documents remain the system of record; the functions here produce a bounded,
UI-ready aggregate without inventing a change or mutating history.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def change_genome(source_id: str, before: str, after: str) -> str:
    """Return a stable fingerprint for one evidence-bound source transition."""
    payload = json.dumps(
        {
            "source_id": source_id,
            "before": " ".join(before.split()),
            "after": " ".join(after.split()),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _source_memory(source_id: str, observations: list[dict[str, Any]]) -> dict[str, Any]:
    chronological = sorted(observations, key=lambda item: item.get("retrieved_at", ""))
    hashes = Counter(str(item.get("snapshot_hash", "")) for item in chronological)
    transitions: list[dict[str, Any]] = []
    genomes: Counter[str] = Counter()
    for previous, current in pairwise(chronological):
        if previous.get("snapshot_hash") == current.get("snapshot_hash"):
            continue
        genome = change_genome(
            source_id,
            str(previous.get("body", "")),
            str(current.get("body", "")),
        )
        genomes[genome] += 1
        transitions.append(
            {
                "genome": genome,
                "from_hash": previous.get("snapshot_hash"),
                "to_hash": current.get("snapshot_hash"),
                "detected_at": current.get("retrieved_at"),
            }
        )
    return {
        "source_id": source_id,
        "observation_count": len(chronological),
        "unique_snapshot_count": len([key for key in hashes if key]),
        "first_seen": chronological[0].get("retrieved_at") if chronological else None,
        "last_seen": chronological[-1].get("retrieved_at") if chronological else None,
        "latest": chronological[-1] if chronological else None,
        "transitions": list(reversed(transitions[-20:])),
        "recurring_genomes": [
            {"genome": genome, "occurrences": count}
            for genome, count in genomes.items()
            if count > 1
        ],
    }


def build_memory_summary(
    source_observations: dict[str, list[dict[str, Any]]],
    workflows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate change genomes and unresolved/reversed operator work."""
    source_summaries = [
        _source_memory(source_id, observations)
        for source_id, observations in sorted(source_observations.items())
    ]
    genome_entries: defaultdict[str, dict[str, Any]] = defaultdict(
        lambda: {"genome": "", "occurrences": 0, "sources": [], "workflow_ids": []}
    )
    unresolved: list[dict[str, Any]] = []
    reversals: list[dict[str, Any]] = []
    completed = 0
    failed = 0
    workflow_count = 0

    for source in source_summaries:
        for transition in source["transitions"]:
            genome = str(transition["genome"])
            entry = genome_entries[genome]
            entry["genome"] = genome
            entry["occurrences"] += 1
            if source["source_id"] not in entry["sources"]:
                entry["sources"].append(source["source_id"])

    for workflow in workflows:
        workflow_count += 1
        workflow_id = str(workflow.get("workflow_id", ""))
        evidence = workflow.get("evidence") or {}
        source_id = str(evidence.get("source_id", "unknown"))
        before = str(evidence.get("before", ""))
        after = str(evidence.get("after", ""))
        if before and after and before != after:
            genome = change_genome(source_id, before, after)
            entry = genome_entries[genome]
            entry["genome"] = genome
            entry["occurrences"] += 1
            if source_id not in entry["sources"]:
                entry["sources"].append(source_id)
            if workflow_id and workflow_id not in entry["workflow_ids"]:
                entry["workflow_ids"].append(workflow_id)
        for item in workflow.get("action_items", []):
            status = item.get("status")
            summary = {
                "item_id": item.get("item_id"),
                "workflow_id": workflow_id,
                "artifact": item.get("artifact"),
                "owner": item.get("owner"),
                "status": status,
                "updated_at": workflow.get("updated_at"),
            }
            if status in {"queued", "claimed", "failed"}:
                unresolved.append(summary)
            elif status == "completed":
                completed += 1
            elif status == "reversed":
                reversals.append(summary)
            if status == "failed":
                failed += 1

    genomes = sorted(
        genome_entries.values(),
        key=lambda item: (item["occurrences"], item["genome"]),
        reverse=True,
    )
    return {
        "append_only": True,
        "generated_at": utc_now(),
        "sources": source_summaries,
        "change_genomes": genomes[:50],
        "recurring_changes": [item for item in genomes if item["occurrences"] > 1][:20],
        "work_summary": {
            "workflow_count": workflow_count,
            "unresolved_count": len(unresolved),
            "unresolved": unresolved[:50],
            "completed_count": completed,
            "failed_count": failed,
            "reversed_count": len(reversals),
            "reversed": reversals[:50],
        },
    }
