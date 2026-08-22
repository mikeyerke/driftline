from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .impact import build_impact_graph, integration_targets, profile_for
from .materiality import (
    build_change_card,
    change_card_id,
    normalize_internal_context,
)
from .models import (
    ActionItemStatus,
    ArtifactImpact,
    SourceEvidence,
    Stage,
    WorkflowState,
    WorkflowStatus,
)

DEMO_BEFORE = "Enterprise includes unlimited audit-log retention."
DEMO_AFTER = "Enterprise includes 365-day audit-log retention."
DEMO_SOURCE_URL = "https://raw.githubusercontent.com/mikeyerke/driftline/a48f7eb/fixtures/public-pricing-after.txt"


def _evidence_digest(before: str, after: str) -> str:
    return hashlib.sha256(f"{before}\n{after}".encode()).hexdigest()


class PolicyViolation(ValueError):
    """Raised when an action violates a deterministic workflow policy."""


_NON_HUMAN_IDENTITIES = frozenset(
    {"agent", "assistant", "driftline", "model", "system"}
)


def _require_named_human(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise PolicyViolation(f"A named human {field_name} is required")
    if any(token in _NON_HUMAN_IDENTITIES for token in cleaned.casefold().split()):
        raise PolicyViolation("An agent or system cannot approve or undo a decision")
    return cleaned


class DriftlineWorkflow:
    """Deterministic control plane around model-generated reasoning."""

    def __init__(self) -> None:
        self._runs: dict[str, WorkflowState] = {}

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat()

    def _event(self, state: WorkflowState, action: str, outcome: str) -> str:
        event_id = f"evt-{uuid4().hex[:12]}"
        state.events.append(
            {
                "event_id": event_id,
                "timestamp": self._timestamp(),
                "action": action,
                "outcome": outcome,
                "stage": state.stage.value,
                "evidence_hash": state.evidence.evidence_hash
                if state.evidence is not None
                else None,
            }
        )
        state.updated_at = self._timestamp()
        return event_id

    @staticmethod
    def _refresh_change_card(state: WorkflowState) -> None:
        if state.evidence is None:
            state.change_card = {}
            return
        state.change_card = build_change_card(
            workflow_id=state.workflow_id,
            evidence=state.evidence,
            impacts=state.impacts,
            impact_graph=state.impact_graph,
            data_mode=state.data_mode,
            internal_context=state.internal_context,
            approval=state.approval,
            action_items=state.action_items,
        )

    def refresh_change_card(self, state: WorkflowState) -> WorkflowState:
        """Rebuild the bounded decision card after verified context changes."""
        self._refresh_change_card(state)
        return state

    def attach_internal_context(
        self, state: WorkflowState, context: dict[str, object]
    ) -> WorkflowState:
        """Attach only normalized aggregate context to a tenant workflow."""
        normalized = normalize_internal_context(context)
        if int(normalized.get("verified_connector_count", 0)) < 1:
            return state
        state.internal_context = normalized
        state.data_mode = "connected_internal_data"
        self._refresh_change_card(state)
        self._event(state, "internal_context_reader", "aggregate_context_attached")
        return state

    def restore(self, state: WorkflowState) -> WorkflowState:
        """Register a state loaded from durable persistence."""
        self._runs[state.workflow_id] = state
        return state

    def start_demo(
        self,
        *,
        tenant_id: str | None = None,
        source_id: str = "public/pricing",
        source_name: str = "Public pricing snapshot",
        source_category: str | None = None,
        source_change_type: str | None = None,
        data_mode: str = "synthetic_demo",
        source_url: str | None = None,
        snapshot_label: str | None = None,
        before_text: str | None = None,
        after_text: str = DEMO_AFTER,
        snapshot_hash: str | None = None,
        previous_snapshot_hash: str | None = None,
        confidence: float = 0.99,
        retrieved_at: str | None = None,
    ) -> WorkflowState:
        profile = profile_for(
            source_id,
            category=source_category,
            change_type=source_change_type,
            source_name=source_name,
        )
        state = WorkflowState(
            workflow_id=str(uuid4()),
            title=profile["title"],
            tenant_id=tenant_id,
            data_mode=data_mode,
        )
        self._runs[state.workflow_id] = state
        self._event(state, "source_monitor", "change_detected")

        state.stage = Stage.VERIFY
        state.evidence = SourceEvidence(
            source_id=source_id,
            source_name=source_name,
            before=before_text or DEMO_BEFORE,
            after=after_text,
            evidence_hash=_evidence_digest(before_text or DEMO_BEFORE, after_text),
            confidence=confidence,
            snapshot_label=snapshot_label or "Synthetic demo fixture · public/pricing",
            source_url=source_url or DEMO_SOURCE_URL,
            retrieved_at=retrieved_at,
            snapshot_hash=snapshot_hash,
            previous_snapshot_hash=previous_snapshot_hash,
        )
        self._event(state, "evidence_verifier", "verified")

        state.stage = Stage.MAP_IMPACT
        state.impacts = [
            ArtifactImpact(
                item["name"],
                item["owner"],
                item["action"],
                item["risk"],
                "draft_ready",
                item["detail"],
                item["proposed"],
                state.evidence.evidence_hash,
            )
            for item in profile["impacts"]
        ]
        state.impact_graph = build_impact_graph(
            source_name,
            source_id,
            [
                {
                    **item,
                    "evidence_hash": state.evidence.evidence_hash,
                }
                for item in profile["impacts"]
            ],
            category=source_category,
            change_type=source_change_type,
        )
        state.integration_targets = integration_targets(profile["impacts"])
        self._refresh_change_card(state)
        self._event(
            state,
            "impact_mapper",
            f"{len(state.impacts)}_artifacts_mapped",
        )

        state.stage = Stage.DRAFT
        self._event(
            state,
            "content_orchestrator",
            f"{len(state.impacts)}_updates_drafted",
        )

        state.stage = Stage.AWAIT_APPROVAL
        state.status = WorkflowStatus.NEEDS_APPROVAL
        self._event(state, "policy_gate", "human_decision_requested")
        return state

    def get(self, workflow_id: str) -> WorkflowState:
        try:
            return self._runs[workflow_id]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow: {workflow_id}") from exc

    def approve(
        self,
        workflow_id: str,
        approver: str,
        decision: str,
        artifact_decisions: dict[str, str] | None = None,
        approval_metadata: dict[str, object] | None = None,
    ) -> WorkflowState:
        state = self.get(workflow_id)
        if state.status is not WorkflowStatus.NEEDS_APPROVAL:
            raise PolicyViolation("Workflow is not waiting for approval")
        if state.evidence is None or state.evidence.evidence_hash != _evidence_digest(
            state.evidence.before, state.evidence.after
        ):
            raise PolicyViolation("Evidence hash no longer matches the source snapshot")
        cleaned_approver = _require_named_human(approver, "approver")
        if decision not in {
            "grandfather_existing_customers",
            "approve_competitive_response",
        }:
            raise PolicyViolation("Decision is not in the allowlisted policy set")

        allowed_actions = {"packet", "owner_review", "queued"}
        requested_actions = artifact_decisions or {
            item.name: (
                "queued"
                if item.name == "CRM guidance"
                else "packet"
                if item.risk == "high"
                else "owner_review"
            )
            for item in state.impacts
        }
        unknown_names = set(requested_actions) - {item.name for item in state.impacts}
        if unknown_names:
            raise PolicyViolation("Artifact decision includes an unknown artifact")
        if any(action not in allowed_actions for action in requested_actions.values()):
            raise PolicyViolation(
                "Artifact action is not in the allowlisted policy set"
            )

        state.approval = {
            "approver": cleaned_approver,
            "decision": decision,
            "timestamp": self._timestamp(),
            "evidence_hash": state.evidence.evidence_hash if state.evidence else None,
            "artifact_decisions": requested_actions,
        }
        if approval_metadata:
            state.approval.update(approval_metadata)
        self._event(state, "policy_engine", "approval_recorded")
        if approval_metadata and approval_metadata.get("copilot_artifact_override"):
            state.events[-1].update(
                {
                    "copilot_artifact_override": True,
                    "copilot_option_id": approval_metadata.get("copilot_option_id"),
                    "override_reason": approval_metadata.get("copilot_override_reason"),
                }
            )
        state.stage = Stage.PUBLISH
        packets: list[dict[str, object]] = []
        updated_impacts: list[ArtifactImpact] = []
        for item in state.impacts:
            action = requested_actions.get(item.name, "owner_review")
            status = {
                "packet": "packet_ready",
                "owner_review": "owner_review",
                "queued": "queued",
            }[action]
            updated_impacts.append(
                ArtifactImpact(
                    item.name,
                    item.owner,
                    item.action,
                    item.risk,
                    status,
                    item.detail,
                    item.proposed,
                    item.evidence_hash,
                )
            )
            packet_event_id = self._event(
                state,
                "bounded_packet",
                f"{item.name}:{status}",
            )
            packets.append(
                {
                    "event_id": packet_event_id,
                    "artifact": item.name,
                    "owner": item.owner,
                    "action": item.action,
                    "risk": item.risk,
                    "status": status,
                    "content": item.proposed,
                    "evidence_hash": item.evidence_hash,
                    "reversible": True,
                }
            )
        state.impacts = updated_impacts
        state.artifact_packets = packets
        card_id = change_card_id(
            state.evidence.source_id if state.evidence else "unknown",
            state.evidence.evidence_hash if state.evidence else "none",
        )
        action_id = f"action-{card_id.removeprefix('card-')}"
        state.action_record = {
            "action_id": action_id,
            "change_card_id": card_id,
            "kind": "firestore_change_packet",
            "status": "active",
            "workflow_id": state.workflow_id,
            "evidence_hash": state.evidence.evidence_hash,
            "packet_count": len(packets),
            "external_systems_changed": False,
            "reversible": True,
            "created_at": self._timestamp(),
            "integration_targets": [
                target["system"] for target in state.integration_targets
            ],
            "external_handoffs_prepared": len(state.integration_targets),
        }
        state.action_items = [
            {
                "item_id": f"item-{uuid4().hex[:12]}",
                "action_id": action_id,
                "workflow_id": state.workflow_id,
                "artifact": packet["artifact"],
                "owner": packet["owner"],
                "status": ActionItemStatus.QUEUED.value,
                "attempts": 0,
                "evidence_hash": packet["evidence_hash"],
                "idempotency_key": f"{card_id}:{packet['artifact']}",
                "created_at": self._timestamp(),
                "due_at": (
                    datetime.now(UTC)
                    + timedelta(
                        hours={"high": 48, "medium": 96, "low": 168}.get(
                            packet.get("risk", "medium"), 72
                        )
                    )
                ).isoformat(),
                "priority": packet.get("risk", "medium"),
            }
            for packet in packets
        ]
        state.action_record["action_item_count"] = len(state.action_items)
        self._refresh_change_card(state)
        packet_count = sum(
            1 for value in requested_actions.values() if value == "packet"
        )
        review_count = sum(
            1 for value in requested_actions.values() if value == "owner_review"
        )
        queued_count = sum(
            1 for value in requested_actions.values() if value == "queued"
        )
        self._event(
            state,
            "bounded_publisher",
            f"{packet_count}_packets_created_{review_count}_owner_review_{queued_count}_queued",
        )
        state.status = WorkflowStatus.COMPLETE
        state.updated_at = self._timestamp()
        return state

    def dismiss(self, workflow_id: str, actor: str, reason: str) -> WorkflowState:
        """Record a human-reviewed no-op so noisy signals remain auditable."""
        state = self.get(workflow_id)
        if state.status is not WorkflowStatus.NEEDS_APPROVAL:
            raise PolicyViolation("Only approval-gated workflows can be dismissed")
        if state.evidence is None or state.evidence.evidence_hash != _evidence_digest(
            state.evidence.before, state.evidence.after
        ):
            raise PolicyViolation("Evidence hash no longer matches the source snapshot")
        cleaned_actor = _require_named_human(actor, "actor")
        cleaned_reason = " ".join(reason.split())
        if not cleaned_reason:
            raise PolicyViolation("Dismissal reason is required")
        state.approval = {
            "approver": cleaned_actor,
            "decision": "dismissed",
            "reason": cleaned_reason,
            "timestamp": self._timestamp(),
        }
        state.stage = Stage.MONITOR
        state.status = WorkflowStatus.DISMISSED
        state.artifact_packets = []
        state.action_items = []
        self._refresh_change_card(state)
        self._event(state, "policy_engine", "signal_dismissed")
        state.updated_at = self._timestamp()
        return state

    def undo(self, workflow_id: str, actor: str) -> WorkflowState:
        state = self.get(workflow_id)
        if state.status is not WorkflowStatus.COMPLETE or state.approval is None:
            raise PolicyViolation("There is no recorded human decision to undo")
        _require_named_human(actor, "actor")
        state.approval = None
        state.stage = Stage.AWAIT_APPROVAL
        state.status = WorkflowStatus.NEEDS_APPROVAL
        state.artifact_packets = []
        if state.action_record is not None:
            state.action_record = {
                **state.action_record,
                "status": "reversed",
                "reversed_at": self._timestamp(),
            }
        state.action_items = [
            {
                **item,
                "status": ActionItemStatus.REVERSED.value,
                "reversed_at": self._timestamp(),
            }
            for item in state.action_items
        ]
        state.impacts = [
            ArtifactImpact(
                i.name,
                i.owner,
                i.action,
                i.risk,
                "draft_ready",
                i.detail,
                i.proposed,
                i.evidence_hash,
            )
            for i in state.impacts
        ]
        self._refresh_change_card(state)
        self._event(state, "policy_engine", "decision_reopened")
        state.updated_at = self._timestamp()
        return state


def packet_markdown(state: WorkflowState) -> str:
    """Render the bounded, evidence-carrying output packet for a workflow."""
    evidence = state.evidence
    lines = [
        "# Driftline change packet",
        "",
        f"- Workflow: `{state.workflow_id}`",
        f"- Change Card: `{(state.change_card or {}).get('change_card_id', 'none')}`",
        f"- Source: {evidence.source_name if evidence else 'Unknown'}",
        f"- Source ID: `{evidence.source_id if evidence else 'unknown'}`",
        f"- Evidence hash: `{evidence.evidence_hash if evidence else 'none'}`",
        f"- Data mode: `{state.data_mode}`",
        "- External systems changed: **No** (isolated public-demo output)",
        f"- Firestore action record: `{(state.action_record or {}).get('action_id', 'none')}`",
        f"- Action status: `{(state.action_record or {}).get('status', 'none')}`",
        f"- Google Cloud operational output: `{(state.action_record or {}).get('operational_side_effect', 'not yet published')}`",
        "",
        "## Materiality and exposure",
        "",
        f"- Materiality: `{(state.change_card.get('materiality') or {}).get('severity', 'unknown')}` / `{(state.change_card.get('materiality') or {}).get('score', 'unknown')}/100`",
        f"- Decision window: {(state.change_card.get('materiality') or {}).get('decision_window', 'Owner review')}",
        f"- Exposure: {(state.change_card.get('exposure') or {}).get('label', 'Unavailable')}",
        f"- Evidence confidence: {round(float((state.change_card.get('source_quality') or {}).get('confidence', 0.0)) * 100)}%",
        f"- Evidence strength heuristic: {(state.change_card.get('source_quality') or {}).get('evidence_strength', {}).get('score', 'unknown')}/100",
        f"- Evidence strength label: {(state.change_card.get('source_quality') or {}).get('evidence_strength', {}).get('label', 'not assessed')}",
        f"- Evidence next review: {(state.change_card.get('source_quality') or {}).get('evidence_strength', {}).get('next_review', 'not assessed')}",
        f"- Contradiction review: {(state.change_card.get('source_quality') or {}).get('contradiction_status', 'not_checked')}",
        f"- Closure: {(state.change_card.get('closure') or {}).get('state', 'approval_pending')}",
        f"- Decision reason: {(state.approval or {}).get('reason', 'not recorded')}",
        "",
        "## Source change",
        "",
        f"> Removed: {evidence.before if evidence else 'Unavailable'}",
        f"> Added: {evidence.after if evidence else 'Unavailable'}",
        "",
        "## Artifact actions",
        "",
    ]
    for packet in state.artifact_packets:
        lines.extend(
            [
                f"### {packet['artifact']}",
                f"- Owner: {packet['owner']}",
                f"- Action: {packet['action']}",
                f"- Risk: {packet['risk']}",
                f"- Status: {packet['status']}",
                f"- Proposed content: {packet['content']}",
                f"- Evidence hash: `{packet['evidence_hash']}`",
                "",
            ]
        )
    role_packets = state.change_card.get("role_packets") or []
    if role_packets:
        lines.extend(["## Role packets", ""])
        for packet in role_packets:
            lines.extend(
                [
                    f"- **{packet.get('role', 'Owner')}** · {packet.get('artifact', 'Work surface')}",
                    f"  - Next action: {packet.get('next_action', 'Review the cited evidence')}",
                    f"  - Status: `{packet.get('status', 'prepared')}` · evidence bound: `{packet.get('evidence_bound', False)}`",
                ]
            )
        lines.append("")
    if state.action_items:
        lines.extend(["## Owner deadlines", ""])
        for item in state.action_items:
            lines.append(
                f"- {item.get('artifact', 'Owner action')} · {item.get('owner', 'Owner')} · "
                f"priority `{item.get('priority', 'medium')}` · due `{item.get('due_at', 'not set')}`"
            )
        lines.append("")
    return "\n".join(lines)


workflow_store = DriftlineWorkflow()
