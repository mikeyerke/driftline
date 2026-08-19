"""Product-marketing impact profiles and graph construction.

The source monitor answers *what changed*.  This module answers the more
valuable commercial question: which offering surfaces and operating systems
could now be out of sync?  Profiles are intentionally explicit and reviewable;
they are not an arbitrary crawler or an unconstrained model-generated graph.
"""

from __future__ import annotations

from typing import Any

IMPACT_PROFILES: dict[str, dict[str, Any]] = {
    "public/pricing": {
        "category": "Own pricing",
        "change_type": "Pricing and packaging",
        "offering": "Enterprise plan",
        "title": "Enterprise plan packaging changed",
        "impacts": [
            {
                "name": "Pricing battlecard",
                "owner": "Product Marketing",
                "action": "Replace claim",
                "risk": "high",
                "detail": "Claims and positioning",
                "proposed": "Enterprise: 365-day audit-log retention.",
                "area": "Positioning",
                "target_systems": ["Confluence", "Jira", "Slack"],
            },
            {
                "name": "Renewal playbook",
                "owner": "Customer Success",
                "action": "Add exception path",
                "risk": "high",
                "detail": "Renewal motions",
                "proposed": "Grandfather existing customers through their next renewal; renewals after that use 365-day retention.",
                "area": "Customer lifecycle",
                "target_systems": ["Confluence", "Jira"],
            },
            {
                "name": "Enterprise FAQ",
                "owner": "Support",
                "action": "Revise retention answer",
                "risk": "medium",
                "detail": "Support answers",
                "proposed": "Enterprise audit logs are retained for 365 days.",
                "area": "Customer education",
                "target_systems": ["Confluence", "Slack"],
            },
            {
                "name": "CRM guidance",
                "owner": "RevOps",
                "action": "Update qualification note",
                "risk": "low",
                "detail": "Sales qualification",
                "proposed": "Confirm retention expectations before positioning Enterprise.",
                "area": "Revenue enablement",
                "target_systems": ["Jira", "Slack"],
            },
        ],
    },
    "public/terms": {
        "category": "Own terms",
        "change_type": "Contractual promise",
        "offering": "Enterprise contract",
        "title": "Enterprise contract terms changed",
        "impacts": [
            {
                "name": "Security battlecard",
                "owner": "Product Marketing",
                "action": "Replace contract claim",
                "risk": "high",
                "detail": "Trust and positioning",
                "proposed": "Enterprise contracts include 365-day audit history.",
                "area": "Positioning",
                "target_systems": ["Confluence", "Jira", "Slack"],
            },
            {
                "name": "Renewal playbook",
                "owner": "Customer Success",
                "action": "Add renewal exception",
                "risk": "high",
                "detail": "Customer commitments",
                "proposed": "Existing contracts retain their recorded commitment through renewal.",
                "area": "Customer lifecycle",
                "target_systems": ["Confluence", "Jira"],
            },
            {
                "name": "Enterprise FAQ",
                "owner": "Support",
                "action": "Revise contract answer",
                "risk": "medium",
                "detail": "Support answers",
                "proposed": "Contracts renew annually with 365-day audit history.",
                "area": "Customer education",
                "target_systems": ["Confluence", "Slack"],
            },
            {
                "name": "Legal review ticket",
                "owner": "Legal",
                "action": "Review language",
                "risk": "high",
                "detail": "Contract language",
                "proposed": "Confirm the revised retention statement is consistent across public terms and order forms.",
                "area": "Risk and compliance",
                "target_systems": ["Jira", "Slack"],
            },
        ],
    },
    "competitor/pricing": {
        "category": "Competitor pricing",
        "change_type": "Competitive pricing move",
        "offering": "Competitor Pro plan",
        "title": "Competitor pricing moved",
        "impacts": [
            {
                "name": "Comparison map",
                "owner": "Product Marketing",
                "action": "Re-score price/value",
                "risk": "high",
                "detail": "Competitive positioning",
                "proposed": "Refresh the competitor price/value row with the captured source and timestamp.",
                "area": "Competitive intelligence",
                "target_systems": ["Confluence", "Jira", "Slack"],
            },
            {
                "name": "Pricing battlecard",
                "owner": "Product Marketing",
                "action": "Draft response",
                "risk": "medium",
                "detail": "Sales objection handling",
                "proposed": "Add an evidence-cited response for the competitor's new price point; do not invent a discount.",
                "area": "Positioning",
                "target_systems": ["Confluence", "Slack"],
            },
            {
                "name": "Deal desk guidance",
                "owner": "RevOps",
                "action": "Review discount guardrail",
                "risk": "high",
                "detail": "Commercial operations",
                "proposed": "Review whether the current discount guardrail still protects the intended price/value position.",
                "area": "Revenue enablement",
                "target_systems": ["Jira", "Slack"],
            },
            {
                "name": "Executive weekly brief",
                "owner": "Product Marketing",
                "action": "Add market signal",
                "risk": "low",
                "detail": "Market narrative",
                "proposed": "Include the observed competitor price change with source, timestamp, and confidence.",
                "area": "Planning",
                "target_systems": ["Confluence", "Slack"],
            },
        ],
    },
    "competitor/offerings": {
        "category": "Competitor offering",
        "change_type": "Product capability change",
        "offering": "Competitor Business plan",
        "title": "Competitor offering changed",
        "impacts": [
            {
                "name": "Feature comparison map",
                "owner": "Product Marketing",
                "action": "Update capability row",
                "risk": "high",
                "detail": "Competitive positioning",
                "proposed": "Mark the observed capability as available on the competitor Business plan and cite the source.",
                "area": "Competitive intelligence",
                "target_systems": ["Confluence", "Jira", "Slack"],
            },
            {
                "name": "Launch narrative",
                "owner": "Product Marketing",
                "action": "Review differentiation",
                "risk": "medium",
                "detail": "Messaging",
                "proposed": "Review whether the current differentiator still holds against the observed capability.",
                "area": "Positioning",
                "target_systems": ["Confluence", "Slack"],
            },
            {
                "name": "Sales enablement note",
                "owner": "Sales Enablement",
                "action": "Add objection answer",
                "risk": "medium",
                "detail": "Field readiness",
                "proposed": "Draft an evidence-bound answer for the new competitor capability.",
                "area": "Revenue enablement",
                "target_systems": ["Confluence", "Jira"],
            },
            {
                "name": "Roadmap review",
                "owner": "Product",
                "action": "Create decision brief",
                "risk": "low",
                "detail": "Product planning",
                "proposed": "Review the signal without treating competitor movement as an automatic roadmap requirement.",
                "area": "Planning",
                "target_systems": ["Jira", "Slack"],
            },
        ],
    },
    "competitor/blog": {
        "category": "Competitor narrative",
        "change_type": "Market narrative change",
        "offering": "Competitor product narrative",
        "title": "Competitor product narrative changed",
        "impacts": [
            {
                "name": "Comparison map",
                "owner": "Product Marketing",
                "action": "Add observed claim",
                "risk": "medium",
                "detail": "Competitive intelligence",
                "proposed": "Add the observed competitor claim with publication date and source citation.",
                "area": "Competitive intelligence",
                "target_systems": ["Confluence", "Jira", "Slack"],
            },
            {
                "name": "Messaging brief",
                "owner": "Product Marketing",
                "action": "Review counter-message",
                "risk": "medium",
                "detail": "Market narrative",
                "proposed": "Draft a response only if the claim is material to a current segment or deal motion.",
                "area": "Positioning",
                "target_systems": ["Confluence", "Slack"],
            },
            {
                "name": "Sales talk track",
                "owner": "Sales Enablement",
                "action": "Queue talk-track review",
                "risk": "low",
                "detail": "Field readiness",
                "proposed": "Queue a review of the talk track; preserve the source as observed, not verified product behavior.",
                "area": "Revenue enablement",
                "target_systems": ["Jira", "Slack"],
            },
            {
                "name": "Executive weekly brief",
                "owner": "Product Marketing",
                "action": "Add market signal",
                "risk": "low",
                "detail": "Planning context",
                "proposed": "Add the dated market signal and confidence to the weekly brief.",
                "area": "Planning",
                "target_systems": ["Confluence", "Slack"],
            },
        ],
    },
}


def profile_for(source_id: str) -> dict[str, Any]:
    """Return an explicit profile, with pricing as the safe fallback."""
    return IMPACT_PROFILES.get(source_id, IMPACT_PROFILES["public/pricing"])


def build_impact_graph(
    source_name: str, source_id: str, impacts: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build a compact source → offering → domain → artifact → system graph."""
    profile = profile_for(source_id)
    nodes: list[dict[str, Any]] = [
        {
            "id": "source",
            "kind": "source",
            "label": source_name,
            "meta": profile["category"],
        },
        {
            "id": "offering",
            "kind": "offering",
            "label": profile["offering"],
            "meta": profile["change_type"],
        },
    ]
    edges = [{"from": "source", "to": "offering"}]
    domains: dict[str, str] = {}
    systems: dict[str, str] = {}
    for index, item in enumerate(impacts):
        area = str(item.get("area") or "Downstream work")
        area_id = f"area-{area.lower().replace(' ', '-') }"
        if area_id not in domains:
            domains[area_id] = area
            nodes.append({"id": area_id, "kind": "domain", "label": area, "meta": "Impact area"})
            edges.append({"from": "offering", "to": area_id})
        artifact_id = f"artifact-{index}"
        nodes.append(
            {
                "id": artifact_id,
                "kind": "artifact",
                "label": item["name"],
                "meta": item["owner"],
                "risk": item["risk"],
            }
        )
        edges.append({"from": area_id, "to": artifact_id})
        for system in item.get("target_systems", []):
            system_id = f"system-{system.lower()}"
            if system_id not in systems:
                systems[system_id] = system
                nodes.append({"id": system_id, "kind": "system", "label": system, "meta": "Prepared handoff"})
            edges.append({"from": artifact_id, "to": system_id})
    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "category": profile["category"],
            "change_type": profile["change_type"],
            "offering": profile["offering"],
            "domains": list(domains.values()),
            "systems": list(systems.values()),
            "artifact_count": len(impacts),
        },
    }


def integration_targets(impacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Describe safe, target-specific handoffs without claiming external writes."""
    counts: dict[str, int] = {}
    for item in impacts:
        for system in item.get("target_systems", []):
            counts[system] = counts.get(system, 0) + 1
    return [
        {
            "system": system,
            "kind": "draft_handoff",
            "status": "prepared",
            "artifact_count": count,
            "external_write": False,
            "description": {
                "Jira": "Issue payload with owner, acceptance criteria, and evidence hash",
                "Confluence": "Draft page update with source citation and timestamp",
                "Slack": "Approval-gated notification with deep link to Driftline",
                "GitHub": "Draft PR payload for versioned docs or comparison maps",
            }.get(system, "Evidence-bound handoff payload"),
        }
        for system, count in sorted(counts.items())
    ]
