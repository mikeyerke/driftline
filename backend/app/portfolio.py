"""Read-only portfolio projection for a PM's decision inbox.

Driftline captures more source observations than a PM should ever have to
review.  This module turns durable workflow records into a bounded inbox:
duplicate observations collapse into one decision thread, related decisions
are linked through shared owners and commitments, and only material work is
promoted.  It never approves, publishes, or performs an external write.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any


def _value(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _timestamp(value: object) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=UTC)


def _status(value: object) -> str:
    return str(getattr(value, "value", value or "unknown"))


def _unique(values: Iterable[object], *, limit: int = 8) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))[:limit]


def _commitments(workflow: Any) -> list[str]:
    card = _value(workflow, "change_card", {}) or {}
    packets = card.get("role_packets") or []
    packet_artifacts = [packet.get("artifact") for packet in packets if isinstance(packet, dict)]
    impacts = _value(workflow, "impacts", []) or []
    return _unique([*packet_artifacts, *[_value(impact, "name", "") for impact in impacts]])


def _owners(workflow: Any) -> list[str]:
    card = _value(workflow, "change_card", {}) or {}
    if card.get("owners"):
        return _unique(card["owners"])
    return _unique(_value(impact, "owner", "") for impact in (_value(workflow, "impacts", []) or []))


def _reopened(workflow: Any) -> bool:
    return any(
        event.get("outcome") == "decision_reopened"
        for event in (_value(workflow, "events", []) or [])
        if isinstance(event, dict)
    )


def _item(workflow: Any, duplicate_count: int) -> dict[str, Any]:
    card = _value(workflow, "change_card", {}) or {}
    materiality = card.get("materiality") or {}
    closure = card.get("closure") or {}
    source = card.get("source") or {}
    evidence = _value(workflow, "evidence")
    source_after = source.get("after") or _value(evidence, "after", "A monitored source changed.")
    source_before = source.get("before") or _value(evidence, "before", "")
    confidence = source.get("confidence", _value(evidence, "confidence", 0.0))
    commitments = _commitments(workflow)
    owners = _owners(workflow)
    status = _status(_value(workflow, "status"))
    closure_state = str(closure.get("state", "approval_pending"))
    reopened = _reopened(workflow)
    if reopened or closure_state in {"needs_retry", "reversed"}:
        lane = "outcomes_to_review"
        attention = "Outcome crossed a review boundary"
    elif status == "needs_approval" or closure_state == "approval_pending":
        lane = "needs_decision"
        attention = "Human decision required"
    elif materiality.get("severity") == "high" and closure_state not in {"closed", "dismissed"}:
        lane = "commitments_at_risk"
        attention = "High-materiality commitment risk"
    elif closure_state in {"closed", "dismissed"}:
        lane = "monitoring_normally"
        attention = "No PM action required"
    else:
        lane = "important_changes"
        attention = "Material change needs triage"
    if closure_state == "dismissed":
        next_action = "Monitor quietly; reopen only if new evidence appears."
    elif reopened:
        next_action = "Review the measured outcome and approve a revised option or rollback."
    else:
        next_action = str(closure.get("next_step") or "Review the evidence-bound decision packet.")
    return {
        "decision_id": str(card.get("change_card_id") or _value(workflow, "workflow_id", "decision")),
        "workflow_id": str(_value(workflow, "workflow_id", "")),
        "title": str(_value(workflow, "title", "Product decision needs review")),
        "lane": lane,
        "attention": attention,
        "what_changed": str(source_after)[:320],
        "previous_state": str(source_before)[:240],
        "why_it_matters": str(
            materiality.get("reason")
            or "New evidence may affect an active product commitment."
        )[:320],
        "commitments": commitments,
        "owners": owners,
        "severity": str(materiality.get("severity", "medium")),
        "materiality_score": int(materiality.get("score", 0) or 0),
        "confidence": round(float(confidence or 0.0), 3),
        "decision_window": str(materiality.get("decision_window", "before the next owner review")),
        "next_action": next_action[:320],
        "status": status,
        "closure_state": closure_state,
        "source_name": str(source.get("name") or _value(evidence, "source_name", "Monitored source")),
        "source_id": str(source.get("id") or _value(evidence, "source_id", "")),
        "updated_at": str(_value(workflow, "updated_at", "")),
        "duplicate_observations_collapsed": max(0, duplicate_count - 1),
        "automation": {
            "completed": [
                "Source change verified",
                "Repeated observation deduplicated" if duplicate_count > 1 else "Materiality scored",
                "Affected owner work prepared",
            ],
            "requires_human": "Approve, dismiss, revise, or reopen the decision",
            "external_writes": False,
        },
    }


def build_decision_inbox(workflows: Iterable[Any], *, limit: int = 50) -> dict[str, Any]:
    """Build a deterministic, quiet-by-default portfolio view."""
    bounded = list(workflows)[: max(1, min(limit, 100))]
    latest_by_thread: dict[str, Any] = {}
    duplicate_counts: defaultdict[str, int] = defaultdict(int)
    for workflow in bounded:
        card = _value(workflow, "change_card", {}) or {}
        thread_id = str(card.get("change_card_id") or _value(workflow, "workflow_id", ""))
        if not thread_id:
            continue
        duplicate_counts[thread_id] += 1
        current = latest_by_thread.get(thread_id)
        if current is None or _timestamp(_value(workflow, "updated_at")) > _timestamp(
            _value(current, "updated_at")
        ):
            latest_by_thread[thread_id] = workflow

    items = [_item(workflow, duplicate_counts[thread_id]) for thread_id, workflow in latest_by_thread.items()]
    commitment_index: defaultdict[str, list[str]] = defaultdict(list)
    owner_index: defaultdict[str, list[str]] = defaultdict(list)
    for item in items:
        for commitment in item["commitments"]:
            commitment_index[commitment].append(item["decision_id"])
        for owner in item["owners"]:
            owner_index[owner].append(item["decision_id"])
    for item in items:
        related = []
        for commitment in item["commitments"]:
            related.extend(commitment_index[commitment])
        for owner in item["owners"]:
            related.extend(owner_index[owner])
        item["related_decision_ids"] = [
            decision_id
            for decision_id in _unique(related, limit=12)
            if decision_id != item["decision_id"]
        ]
        item["relationship_summary"] = (
            f"Linked to {len(item['related_decision_ids'])} other decision"
            f"{'s' if len(item['related_decision_ids']) != 1 else ''} through shared commitments or owners"
            if item["related_decision_ids"]
            else "No related decision detected in this bounded window"
        )

    relationships: list[dict[str, Any]] = []
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            shared_commitments = sorted(
                set(left["commitments"]).intersection(right["commitments"])
            )
            shared_owners = sorted(set(left["owners"]).intersection(right["owners"]))
            if not shared_commitments and not shared_owners:
                continue
            relationships.append(
                {
                    "from_decision_id": left["decision_id"],
                    "to_decision_id": right["decision_id"],
                    "types": [
                        *(["shared_commitment"] if shared_commitments else []),
                        *(["shared_owner"] if shared_owners else []),
                    ],
                    "shared_commitments": shared_commitments,
                    "shared_owners": shared_owners,
                }
            )

    commitment_health = []
    for commitment, decision_ids in commitment_index.items():
        affected = [item for item in items if item["decision_id"] in decision_ids]
        at_risk = [
            item
            for item in affected
            if item["lane"]
            in {"needs_decision", "outcomes_to_review", "commitments_at_risk"}
        ]
        commitment_health.append(
            {
                "commitment": commitment,
                "decision_count": len(affected),
                "at_risk_count": len(at_risk),
                "max_materiality_score": max(
                    (item["materiality_score"] for item in affected), default=0
                ),
                "owners": _unique(
                    owner for item in affected for owner in item["owners"]
                ),
                "state": "attention_required" if at_risk else "monitoring_normally",
            }
        )
    commitment_health.sort(
        key=lambda item: (
            -item["at_risk_count"],
            -item["max_materiality_score"],
            item["commitment"],
        )
    )

    lane_order = {
        "needs_decision": 0,
        "outcomes_to_review": 1,
        "commitments_at_risk": 2,
        "important_changes": 3,
        "monitoring_normally": 4,
    }
    items.sort(
        key=lambda item: (
            lane_order[item["lane"]],
            -item["materiality_score"],
            item["updated_at"],
        )
    )
    counts = {lane: sum(item["lane"] == lane for item in items) for lane in lane_order}
    quiet_count = counts["monitoring_normally"]
    findings: list[dict[str, Any]] = []
    duplicate_total = sum(duplicate_counts.values()) - len(items)
    if duplicate_total:
        findings.append(
            {
                "kind": "recurring_signal",
                "title": "Repeated observations consolidated",
                "finding": f"{duplicate_total} repeated observation{'s were' if duplicate_total != 1 else ' was'} folded into existing decision threads.",
                "sample_size": sum(duplicate_counts.values()),
                "recommended_response": "Review the decision thread once; do not create duplicate owner work.",
            }
        )
    if relationships:
        findings.append(
            {
                "kind": "decision_dependency",
                "title": "Decisions share commitments or owners",
                "finding": f"{len(relationships)} cross-decision relationship{'s' if len(relationships) != 1 else ''} can be reviewed together.",
                "sample_size": len(items),
                "recommended_response": "Resolve the shared commitment once, then route the bounded work to each owner.",
            }
        )
    outcome_exceptions = counts["outcomes_to_review"]
    if outcome_exceptions:
        findings.append(
            {
                "kind": "outcome_exception",
                "title": "Measured outcomes need review",
                "finding": f"{outcome_exceptions} decision{'s have' if outcome_exceptions != 1 else ' has'} crossed a reopen or retry boundary.",
                "sample_size": len(items),
                "recommended_response": "Review the outcome evidence before revising or rolling back the commitment.",
            }
        )
    owner_load = sorted(
        ((owner, len(decision_ids)) for owner, decision_ids in owner_index.items()),
        key=lambda pair: (-pair[1], pair[0]),
    )
    if owner_load and owner_load[0][1] > 1:
        owner, decision_count = owner_load[0]
        findings.append(
            {
                "kind": "owner_concentration",
                "title": "Decision load is concentrated",
                "finding": f"{owner} appears across {decision_count} active decision threads in this bounded window.",
                "sample_size": len(items),
                "recommended_response": "Sequence the shared owner work instead of creating parallel interruptions.",
            }
        )
    return {
        "version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "observed_workflows" if items else "empty",
        "summary": {
            "decision_threads": len(items),
            "requires_attention": len(items) - quiet_count,
            "monitoring_quietly": quiet_count,
            "duplicate_observations_collapsed": duplicate_total,
            "linked_decisions": sum(bool(item["related_decision_ids"]) for item in items),
        },
        "counts": counts,
        "items": items,
        "relationships": relationships,
        "commitment_health": commitment_health[:12],
        "findings": findings[:4],
        "automation_boundary": {
            "automated_for_pm": [
                "Monitor registered sources",
                "Deduplicate repeated observations",
                "Score deterministic materiality",
                "Link affected commitments and owners",
                "Prepare evidence-bound next steps",
                "Surface outcome-driven reopen candidates",
            ],
            "reserved_for_human": [
                "Approve or dismiss a decision",
                "Change a commitment",
                "Authorize an external write",
                "Publish a customer-facing claim",
            ],
            "external_writes": False,
        },
        "disclosure": "The inbox is a read-only projection of observed Driftline workflow records. Materiality is deterministic; AI may explain evidence but cannot approve or publish.",
    }
