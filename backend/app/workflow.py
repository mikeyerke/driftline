from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from .models import (
    ArtifactImpact,
    SourceEvidence,
    Stage,
    WorkflowState,
    WorkflowStatus,
)

DEMO_BEFORE = "Enterprise includes unlimited audit-log retention."
DEMO_AFTER = "Enterprise includes 365-day audit-log retention."
DEMO_SOURCE_URL = "https://raw.githubusercontent.com/mikeyerke/driftline/main/fixtures/public-pricing-after.txt"

_DEFAULT_IMPACTS = (
    (
        "Pricing battlecard",
        "Product Marketing",
        "Replace claim",
        "high",
        "Claims and positioning",
        "Enterprise: 365-day audit-log retention.",
    ),
    (
        "Renewal playbook",
        "Customer Success",
        "Add exception path",
        "high",
        "Renewal motions",
        "Grandfather existing customers through their next renewal; renewals after that use 365-day retention.",
    ),
    (
        "Enterprise FAQ",
        "Support",
        "Revise retention answer",
        "medium",
        "Support answers",
        "Enterprise audit logs are retained for 365 days.",
    ),
    (
        "CRM guidance",
        "RevOps",
        "Update qualification note",
        "low",
        "Sales qualification",
        "Confirm retention expectations before positioning Enterprise.",
    ),
)


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

    def restore(self, state: WorkflowState) -> WorkflowState:
        """Register a state loaded from durable persistence."""
        self._runs[state.workflow_id] = state
        return state

    def start_demo(
        self,
        *,
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
        state = WorkflowState(
            workflow_id=str(uuid4()),
            title="Enterprise plan packaging changed",
            data_mode=data_mode,
        )
        self._runs[state.workflow_id] = state
        self._event(state, "source_monitor", "change_detected")

        state.stage = Stage.VERIFY
        state.evidence = SourceEvidence(
            source_id="public/pricing",
            source_name="Public pricing snapshot",
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
                name,
                owner,
                action,
                risk,
                "draft_ready",
                detail,
                proposed,
                state.evidence.evidence_hash,
            )
            for name, owner, action, risk, detail, proposed in _DEFAULT_IMPACTS
        ]
        self._event(state, "impact_mapper", "4_artifacts_mapped")

        state.stage = Stage.DRAFT
        self._event(state, "content_orchestrator", "4_updates_drafted")

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
    ) -> WorkflowState:
        state = self.get(workflow_id)
        if state.status is not WorkflowStatus.NEEDS_APPROVAL:
            raise PolicyViolation("Workflow is not waiting for approval")
        if state.evidence is None or state.evidence.evidence_hash != _evidence_digest(
            state.evidence.before, state.evidence.after
        ):
            raise PolicyViolation("Evidence hash no longer matches the source snapshot")
        cleaned_approver = _require_named_human(approver, "approver")
        if decision != "grandfather_existing_customers":
            raise PolicyViolation("Decision is not in the allowlisted policy set")

        allowed_actions = {"packet", "owner_review", "queued"}
        requested_actions = artifact_decisions or {
            "Pricing battlecard": "packet",
            "Renewal playbook": "packet",
            "Enterprise FAQ": "owner_review",
            "CRM guidance": "queued",
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
        self._event(state, "policy_engine", "approval_recorded")
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

    def undo(self, workflow_id: str, actor: str) -> WorkflowState:
        state = self.get(workflow_id)
        if state.status is not WorkflowStatus.COMPLETE or state.approval is None:
            raise PolicyViolation("There is no recorded human decision to undo")
        _require_named_human(actor, "actor")
        state.approval = None
        state.stage = Stage.AWAIT_APPROVAL
        state.status = WorkflowStatus.NEEDS_APPROVAL
        state.artifact_packets = []
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
        f"- Source: {evidence.source_name if evidence else 'Unknown'}",
        f"- Source ID: `{evidence.source_id if evidence else 'unknown'}`",
        f"- Evidence hash: `{evidence.evidence_hash if evidence else 'none'}`",
        f"- Data mode: `{state.data_mode}`",
        "- External systems changed: **No** (sandbox output)",
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
    return "\n".join(lines)


workflow_store = DriftlineWorkflow()
