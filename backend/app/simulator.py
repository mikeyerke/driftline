"""Deterministic counterfactual decision simulation.

The simulator previews consequences without mutating workflow state, Firestore,
Cloud Storage, Jira, or any other connector.  It lets a reviewer compare the
three policy choices before crossing the real approval gate.
"""

from __future__ import annotations

from typing import Any

SCENARIOS = {
    "approve": {
        "label": "Approve now",
        "description": "Create the prepared packet and queue owner work immediately.",
    },
    "grandfather": {
        "label": "Grandfather existing customers",
        "description": "Preserve the old promise for existing customers through renewal.",
    },
    "defer": {
        "label": "Defer decision",
        "description": "Hold every downstream change for a later human review.",
    },
}


def _artifact_result(item: dict[str, Any], scenario: str) -> dict[str, Any]:
    risk = str(item.get("risk", "medium")).casefold()
    if scenario == "approve":
        outcome = "packet_ready" if risk in {"high", "medium"} else "queued"
        rationale = "Prepared output can move to its owner after approval."
    elif scenario == "grandfather":
        outcome = "grandfathered_owner_review" if risk == "high" else "owner_review"
        rationale = (
            "Existing commitments are preserved while the new wording is reviewed."
        )
    else:
        outcome = "deferred"
        rationale = "No downstream artifact is changed until a later decision."
    jira_status = {
        "approve": "would_create_or_reuse",
        "grandfather": "would_create_review_issue",
        "defer": "would_defer_issue",
    }[scenario]
    return {
        "artifact": item.get("name", "Unnamed artifact"),
        "owner": item.get("owner", "Unassigned"),
        "risk": risk,
        "outcome": outcome,
        "rationale": rationale,
        "jira": {"status": jira_status, "external_write": False},
    }


def simulate_scenarios(
    impacts: list[dict[str, Any]],
    evidence_hash: str | None,
    integration_targets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return all policy counterfactuals with explicit no-write semantics."""
    target_names = [
        str(item.get("system"))
        for item in (integration_targets or [])
        if item.get("system")
    ]
    scenarios: list[dict[str, Any]] = []
    for scenario, metadata in SCENARIOS.items():
        artifacts = [_artifact_result(item, scenario) for item in impacts]
        scenarios.append(
            {
                "id": scenario,
                **metadata,
                "evidence_hash": evidence_hash,
                "artifacts": artifacts,
                "integration_targets": target_names,
                "summary": {
                    "artifact_count": len(artifacts),
                    "deferred_count": sum(
                        item["outcome"] == "deferred" for item in artifacts
                    ),
                    "jira_actions": len(artifacts),
                    "external_writes": 0,
                },
            }
        )
    return {
        "scenarios": scenarios,
        "policy": "counterfactual_preview_only",
        "external_writes": False,
        "evidence_hash": evidence_hash,
    }
