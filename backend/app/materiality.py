"""Deterministic materiality and change-card contracts.

The model can explain a change, but it must not invent business exposure or
decide that a signal is important.  This module keeps the first-pass decision
policy explicit and labels illustrative demo exposure separately from future
CRM-backed evidence.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from .guardrails import guard_untrusted_text

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


def _evidence_strength(
    *,
    evidence: Any,
    evidence_type: str,
    retrieved_at: object,
    exposure_mode: str,
) -> dict[str, Any]:
    """Return a deterministic review heuristic for source evidence quality.

    This is intentionally not a truth score and never changes materiality or
    approval policy. It makes the missing evidence legible: a direct snapshot
    can still be single-source, synthetic, stale, or uncorroborated.
    """
    before = str(_field(evidence, "before", "")).strip()
    after = str(_field(evidence, "after", "")).strip()
    direct_change = bool(before and after and before != after)
    if evidence_type == "synthetic_fixture":
        source_score = 10
        source_status = "synthetic_fixture"
    elif evidence_type.startswith("operator_registered_public_url"):
        source_score = 25
        source_status = "operator_registered_public_url"
    else:
        source_score = 25
        source_status = "allowlisted_public_snapshot"

    freshness_score = 0
    freshness_status = "unknown"
    age_hours: float | None = None
    try:
        observed_at = datetime.fromisoformat(str(retrieved_at))
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)
        age_hours = max(0.0, (datetime.now(UTC) - observed_at).total_seconds() / 3600)
        if age_hours <= 24:
            freshness_score = 20
            freshness_status = "fresh"
        elif age_hours <= 24 * 7:
            freshness_score = 12
            freshness_status = "aging"
        elif age_hours <= 24 * 30:
            freshness_score = 6
            freshness_status = "stale"
        else:
            freshness_status = "expired"
    except (TypeError, ValueError):
        pass

    direct_score = 35 if direct_change else 0
    corroboration_status = "not_evaluated"
    corroboration_note = (
        "No independent source-level artifact was supplied; aggregate connector context does not corroborate the claim."
        if exposure_mode == "connected_internal_data"
        else "No approved internal source was supplied for contradiction review."
    )
    total = direct_score + source_score + freshness_score
    if direct_change and source_status == "synthetic_fixture":
        label = "Direct demo fixture · single source"
    elif direct_change:
        label = "Direct snapshot · single source"
    else:
        label = "Insufficient before/after evidence"
    return {
        "score": total,
        "max_score": 100,
        "score_kind": "deterministic_review_heuristic",
        "label": label,
        "dimensions": {
            "direct_change": {
                "score": direct_score,
                "max_score": 35,
                "status": "pass" if direct_change else "missing",
            },
            "source_scope": {
                "score": source_score,
                "max_score": 25,
                "status": source_status,
            },
            "freshness": {
                "score": freshness_score,
                "max_score": 20,
                "status": freshness_status,
                "age_hours": round(age_hours, 2) if age_hours is not None else None,
            },
            "corroboration": {
                "score": 0,
                "max_score": 20,
                "status": corroboration_status,
                "note": corroboration_note,
            },
        },
        "next_review": corroboration_note,
    }


_CONTEXT_COUNT_FIELDS = (
    "open_issue_count",
    "open_pull_request_count",
    "recent_message_count",
    "page_count",
    "sampled_issue_count",
    "driftline_active_count",
)


def normalize_internal_context(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Keep connector context aggregate-only before it enters workflow state.

    Connector adapters already return bounded metadata, but this second seam
    prevents a future adapter from accidentally copying arbitrary response
    fields into a durable Change Card.  Only status, scope, bounded counts,
    and Salesforce object names/totals/field names survive normalization.
    """
    raw = value if isinstance(value, Mapping) else {}
    if isinstance(raw.get("connectors"), Mapping):
        raw = raw["connectors"]
    connectors: dict[str, dict[str, Any]] = {}
    attempted = 0
    verified = 0
    for connector, payload in sorted(raw.items()):
        if not isinstance(payload, Mapping):
            continue
        safe_name = str(connector).strip().casefold()
        if not safe_name or len(safe_name) > 32:
            continue
        attempted += 1
        external_read = bool(payload.get("external_read"))
        verified += int(external_read)
        safe: dict[str, Any] = {
            "status": str(payload.get("status", "unknown"))[:48],
            "external_read": external_read,
            "scope": str(payload.get("scope", "aggregate_context"))[:120],
            "redaction": "aggregate_metadata_only",
        }
        for field in _CONTEXT_COUNT_FIELDS:
            if field not in payload:
                continue
            try:
                safe[field] = max(0, min(int(payload[field]), 1_000_000))
            except (TypeError, ValueError):
                continue
        objects = payload.get("objects")
        if isinstance(objects, list) and safe_name == "salesforce":
            safe_objects: list[dict[str, Any]] = []
            for item in objects[:8]:
                if not isinstance(item, Mapping):
                    continue
                object_name = str(item.get("object", "")).strip()[:80]
                if not object_name:
                    continue
                try:
                    total = max(0, min(int(item.get("total", 0)), 1_000_000))
                except (TypeError, ValueError):
                    total = 0
                fields = sorted(
                    {
                        str(field).strip()[:80]
                        for field in item.get("fields", [])
                        if str(field).strip()
                    }
                )[:30]
                safe_objects.append(
                    {"object": object_name, "total": total, "fields": fields}
                )
            safe["objects"] = safe_objects
        connectors[safe_name] = safe
    if not attempted or not verified:
        status = "unavailable"
    elif verified == attempted:
        status = "verified"
    else:
        status = "partial"
    return {
        "status": status,
        "attempted_connector_count": attempted,
        "verified_connector_count": verified,
        "connectors": connectors,
        "redaction": "aggregate_metadata_only",
    }


def model_internal_context(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Project connector context into the model's aggregate-only input seam.

    ``normalize_internal_context`` is the durable-state boundary.  This
    second, explicit projection keeps the prompt contract just as narrow if a
    future normalization field is added for UI or audit use: Gemini receives
    connector status, scope, bounded counts, and the allowlisted Salesforce
    object metadata only.  It never receives connector response bodies,
    record fields, credentials, or customer outcomes.
    """
    normalized = normalize_internal_context(value)
    safe_connectors: dict[str, dict[str, Any]] = {}
    for connector, payload in normalized["connectors"].items():
        if not isinstance(payload, Mapping):
            continue
        safe: dict[str, Any] = {
            "status": guard_untrusted_text(
                payload.get("status", "unknown"), max_chars=48
            ).text,
            "external_read": bool(payload.get("external_read")),
            "scope": guard_untrusted_text(
                payload.get("scope", "aggregate_context"), max_chars=120
            ).text,
            "redaction": "aggregate_metadata_only",
        }
        for field in _CONTEXT_COUNT_FIELDS:
            if field in payload:
                safe[field] = int(payload[field])
        if connector == "salesforce" and isinstance(payload.get("objects"), list):
            safe["objects"] = [
                {
                    "object": guard_untrusted_text(
                        item.get("object", ""), max_chars=80
                    ).text,
                    "total": int(item.get("total", 0)),
                    "fields": [
                        guard_untrusted_text(field, max_chars=80).text
                        for field in item.get("fields", [])
                    ],
                }
                for item in payload["objects"]
                if isinstance(item, Mapping)
            ]
        safe_connectors[connector] = safe
    return {
        "status": str(normalized["status"]),
        "attempted_connector_count": int(normalized["attempted_connector_count"]),
        "verified_connector_count": int(normalized["verified_connector_count"]),
        "connectors": safe_connectors,
        "redaction": "aggregate_metadata_only",
    }


def model_context_provenance(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return prompt-use metadata safe to persist in the redacted trace."""
    projected = model_internal_context(value)
    return {
        "status": projected["status"],
        "attempted_connector_count": projected["attempted_connector_count"],
        "verified_connector_count": projected["verified_connector_count"],
        "connector_names": sorted(projected["connectors"]),
        "used_in_prompt": projected["verified_connector_count"] > 0,
        "redaction": "aggregate_metadata_only",
    }


def change_card_id(source_id: str, evidence_hash: str) -> str:
    """Return the stable identity for one source snapshot transition.

    A workflow run is ephemeral; the same verified source transition must not
    become a second downstream action merely because a scheduler retried it.
    """
    digest = sha256(f"{source_id.strip()}:{evidence_hash.strip()}".encode()).hexdigest()
    return f"card-{digest[:20]}"


def _closure(
    action_items: Iterable[dict[str, Any]], approval: dict[str, Any] | None
) -> dict[str, Any]:
    items = list(action_items)
    now = datetime.now(UTC)
    completed = sum(item.get("status") == "completed" for item in items)
    failed = sum(item.get("status") == "failed" for item in items)
    reversed_items = sum(item.get("status") == "reversed" for item in items)
    overdue = 0
    for item in items:
        if item.get("status") in {"completed", "reversed"} or not item.get("due_at"):
            continue
        try:
            due_at = datetime.fromisoformat(str(item["due_at"]))
            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=UTC)
            overdue += due_at < now
        except (TypeError, ValueError):
            continue
    if approval and approval.get("decision") == "dismissed":
        state = "dismissed"
    elif approval is None:
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
        "overdue": overdue,
        "completion_rate": round(completed / len(items), 3) if items else 0.0,
        "next_step": (
            "Recorded as an intentional no-op; reopen only if new evidence appears"
            if state == "dismissed"
            else "Named human approval is required"
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
    internal_context: Mapping[str, Any] | None = None,
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
    context = normalize_internal_context(internal_context)
    verified_context = context["verified_connector_count"] > 0
    # A public source snapshot is not an internal CRM read. Keep the exposure
    # contract fail-closed until a future connector-aware workflow explicitly
    # supplies verified internal context; never infer permissioned exposure
    # from the fact that a public source was fetched successfully.
    exposure_mode = (
        "connected_internal_data"
        if data_mode == "connected_internal_data" and verified_context
        else {
            "synthetic_demo": "synthetic_demo",
            "live": "connected_internal_data" if verified_context else "internal_context_unavailable",
        }.get(data_mode, "internal_context_unavailable")
    )
    salesforce = context["connectors"].get("salesforce", {})
    opportunity_count = None
    if isinstance(salesforce, Mapping):
        opportunity_count = next(
            (
                int(item["total"])
                for item in salesforce.get("objects", [])
                if isinstance(item, Mapping) and item.get("object") == "Opportunity"
            ),
            None,
        )
    exposure = {
        "mode": exposure_mode,
        "label": (
            "Illustrative scenario only — not CRM data"
            if exposure_mode == "synthetic_demo"
            else "Derived from permissioned internal systems"
            if exposure_mode == "connected_internal_data"
            else "No CRM context was read in this run"
        ),
        "opportunity_count": opportunity_count
        if exposure_mode == "connected_internal_data"
        else None,
        "renewal_count": None,
        "affected_asset_count": len(impact_items),
        "available": exposure_mode == "connected_internal_data",
        "context_status": context["status"],
        "verified_connector_count": context["verified_connector_count"],
        "next_connector": "Salesforce read-only consent"
        if exposure_mode != "connected_internal_data"
        else None,
    }
    snapshot_label = str(_field(evidence, "snapshot_label", ""))
    snapshot_label_lower = snapshot_label.casefold()
    synthetic_snapshot = data_mode in {"synthetic_demo", "synthetic_tenant_demo"} or any(
        marker in snapshot_label_lower
        for marker in ("synthetic", "demo replay")
    )
    if synthetic_snapshot:
        evidence_type = "synthetic_fixture"
        verification = "replayable_fixture"
    elif data_mode == "operator_registered_public":
        evidence_type = "operator_registered_public_url"
        verification = "observed_snapshot"
    else:
        evidence_type = "allowlisted_public_snapshot"
        verification = "observed_snapshot"
    if exposure_mode == "connected_internal_data":
        evidence_type = f"{evidence_type}_plus_aggregate_context"
    evidence_strength = _evidence_strength(
        evidence=evidence,
        evidence_type=evidence_type,
        retrieved_at=_field(evidence, "retrieved_at", ""),
        exposure_mode=exposure_mode,
    )
    source_quality = {
        "confidence": round(float(getattr(evidence, "confidence", 0.0)), 3),
        "evidence_type": evidence_type,
        "verification": verification,
        "evidence_strength": evidence_strength,
        "contradiction_status": (
            "not_evaluated_aggregate_only"
            if exposure_mode == "connected_internal_data"
            else "not_checked"
        ),
        "disclosure": (
            "Aggregate internal context was verified; source-level contradiction review was not performed. Evidence strength is a deterministic review heuristic, not a truth or approval score."
            if exposure_mode == "connected_internal_data"
            else "No contradictory internal source was evaluated in this run. Evidence strength is a deterministic review heuristic, not a truth or approval score."
        ),
    }
    claim_policy = {
        "status": "internal_review_only",
        "customer_facing_publish": "blocked_pending_corroboration",
        "reason": evidence_strength["next_review"],
        "allowed_actions": ["packet", "owner_review"],
        "blocked_actions": ["customer_facing_publish", "autonomous_external_write"],
        "corroboration_status": evidence_strength["dimensions"]["corroboration"]["status"],
    }
    return {
        "version": "1.0",
        "change_card_id": change_card_id(evidence.source_id, evidence.evidence_hash),
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
        "claim_policy": claim_policy,
        "internal_context": context,
        "owners": owners,
        "role_packets": role_packets,
        "closure": _closure(action_items, approval),
        "disclosures": [
            "Observed source evidence is separate from inferred impact.",
            (
                "Internal exposure is derived from a permissioned connector read."
                if exposure_mode == "connected_internal_data"
                else "No CRM or opportunity data was read in this run; exposure remains unavailable."
            ),
            "Approval and external actions remain deterministic and human-controlled.",
            "Customer-facing claims remain blocked until an independent source-level corroboration is reviewed.",
        ],
    }
