"""Deterministic materiality and change-card contracts.

The model can explain a change, but it must not invent business exposure or
decide that a signal is important.  This module keeps the first-pass decision
policy explicit and labels illustrative demo exposure separately from future
CRM-backed evidence.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "Own pricing": {
        "score": 94,
        "severity": "high",
        "window": "before the next quote or renewal",
        "reason": "Pricing or packaging changes can create contradictory customer and seller promises.",
        "triggers": ["pricing_or_packaging", "high_risk_promise"],
    },
    "Own terms": {
        "score": 97,
        "severity": "high",
        "window": "before the next contract or renewal",
        "reason": "Contractual language changes require a reviewed exception path and consistent public claims.",
        "triggers": ["contractual_promise", "high_risk_promise"],
    },
    "Competitor pricing": {
        "score": 88,
        "severity": "high",
        "window": "before the next competitive deal",
        "reason": "A competitor price move can change buyer price perception and active deal guidance.",
        "triggers": ["competitor_price_move", "deal_guidance"],
    },
    "Competitor offering": {
        "score": 78,
        "severity": "medium",
        "window": "before the next comparison or roadmap review",
        "reason": "A capability change may invalidate a comparison claim, but it is not an automatic roadmap requirement.",
        "triggers": ["capability_change", "comparison_claim"],
    },
    "Competitor narrative": {
        "score": 64,
        "severity": "medium",
        "window": "before the next enablement refresh",
        "reason": "A narrative change is useful only when it affects a current segment, objection, or deal motion.",
        "triggers": ["narrative_change", "segment_relevance"],
    },
}


def _role_for_owner(owner: str) -> str:
    value = owner.casefold()
    if "product marketing" in value or "sales enablement" in value:
        return "PMM"
    if "revops" in value or "sales" in value:
        return "Sales / RevOps"
    if "customer success" in value:
        return "Customer Success"
    if "product" in value:
        return "Product"
    if "support" in value:
        return "Support"
    if "legal" in value:
        return "Legal"
    return owner or "Owner"


def _target_for_owner(owner: str) -> str:
    role = _role_for_owner(owner)
    return {
        "PMM": "comparison map or battlecard",
        "Sales / RevOps": "deal guidance or CRM context",
        "Customer Success": "renewal playbook",
        "Product": "roadmap review",
        "Support": "support answer",
        "Legal": "contract language review",
    }.get(role, "owner work surface")


def _field(item: Any, key: str, default: Any = "") -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _closure(
    action_items: Iterable[dict[str, Any]], approval: dict[str, Any] | None
) -> dict[str, Any]:
    items = list(action_items)
    completed = sum(item.get("status") == "completed" for item in items)
    failed = sum(item.get("status") == "failed" for item in items)
    reversed_items = sum(item.get("status") == "reversed" for item in items)
    if approval is None:
        state = "approval_pending"
    elif not items:
        state = "approved"
    elif completed == len(items):
        state = "closed"
    elif failed:
        state = "needs_retry"
    elif reversed_items == len(items):
        state = "reversed"
    else:
        state = "in_progress"
    return {
        "state": state,
        "item_count": len(items),
        "completed": completed,
        "failed": failed,
        "reversed": reversed_items,
        "completion_rate": round(completed / len(items), 3) if items else 0.0,
        "next_step": (
            "Named human approval is required"
            if approval is None
            else "Assign and close each owner action"
            if items and completed < len(items)
            else "Review the completed evidence trail"
        ),
    }


def build_change_card(
    *,
    workflow_id: str,
    evidence: Any,
    impacts: Iterable[Any],
    impact_graph: dict[str, Any],
    data_mode: str,
    approval: dict[str, Any] | None = None,
    action_items: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Build a bounded, UI-ready decision card from verified state only."""
    summary = impact_graph.get("summary", {})
    category = str(summary.get("category", "Change"))
    profile = _PROFILE_DEFAULTS.get(
        category,
        {
            "score": 55,
            "severity": "medium",
            "window": "before the next owner review",
            "reason": "The source change needs owner review before it becomes work.",
            "triggers": ["materiality_review"],
        },
    )
    impact_items = list(impacts)
    high_risk_count = sum(
        _field(item, "risk", "low") == "high" for item in impact_items
    )
    score = min(99, int(profile["score"]) + min(4, high_risk_count))
    owners = sorted({str(_field(item, "owner", "Owner")) for item in impact_items})
    role_packets = []
    for item in impact_items:
        owner = str(_field(item, "owner", "Owner"))
        artifact = str(_field(item, "name", "Work surface"))
        role = _role_for_owner(owner)
        role_packets.append(
            {
                "role": role,
                "owner": owner,
                "artifact": artifact,
                "headline": f"Review {artifact} against the verified source change",
                "next_action": f"Update the {_target_for_owner(owner)} only after reviewing the cited evidence.",
                "status": "prepared",
                "evidence_bound": True,
            }
        )
    exposure_mode = (
        "synthetic_demo" if data_mode == "synthetic_demo" else "connected_internal_data"
    )
    exposure = {
        "mode": exposure_mode,
        "label": (
            "Illustrative scenario only — not CRM data"
            if exposure_mode == "synthetic_demo"
            else "Derived from permissioned internal systems"
        ),
        "opportunity_count": None,
        "renewal_count": None,
        "affected_asset_count": len(impact_items),
        "available": exposure_mode != "synthetic_demo",
        "next_connector": "Salesforce read-only consent"
        if exposure_mode == "synthetic_demo"
        else None,
    }
    source_quality = {
        "confidence": round(float(getattr(evidence, "confidence", 0.0)), 3),
        "evidence_type": (
            "synthetic_fixture"
            if data_mode == "synthetic_demo"
            else "permissioned_public_snapshot"
        ),
        "verification": "replayable_fixture"
        if data_mode == "synthetic_demo"
        else "observed_snapshot",
        "contradiction_status": "not_checked",
        "disclosure": "No contradictory internal source was evaluated in this run.",
    }
    return {
        "version": "1.0",
        "workflow_id": workflow_id,
        "source": {
            "id": evidence.source_id,
            "name": evidence.source_name,
            "url": evidence.source_url,
            "before": evidence.before,
            "after": evidence.after,
            "evidence_hash": evidence.evidence_hash,
            "snapshot_label": evidence.snapshot_label,
            "retrieved_at": evidence.retrieved_at,
            "confidence": evidence.confidence,
        },
        "materiality": {
            "score": score,
            "severity": profile["severity"],
            "reason": profile["reason"],
            "decision_window": profile["window"],
            "triggers": profile["triggers"],
            "high_risk_artifacts": high_risk_count,
        },
        "exposure": exposure,
        "source_quality": source_quality,
        "owners": owners,
        "role_packets": role_packets,
        "closure": _closure(action_items, approval),
        "disclosures": [
            "Observed source evidence is separate from inferred impact.",
            "Synthetic exposure is illustrative until a permissioned CRM connection is verified.",
            "Approval and external actions remain deterministic and human-controlled.",
        ],
    }
