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

    def _event(self, state: WorkflowState, action: str, outcome: str) -> None:
        state.events.append(
            {
                "event_id": f"evt-{uuid4().hex[:12]}",
                "timestamp": self._timestamp(),
                "action": action,
                "outcome": outcome,
                "stage": state.stage.value,
            }
        )

    def restore(self, state: WorkflowState) -> WorkflowState:
        """Register a state loaded from durable persistence."""
        self._runs[state.workflow_id] = state
        return state

    def start_demo(self) -> WorkflowState:
        state = WorkflowState(
            workflow_id=str(uuid4()),
            title="Enterprise plan packaging changed",
        )
        self._runs[state.workflow_id] = state
        self._event(state, "source_monitor", "change_detected")

        state.stage = Stage.VERIFY
        state.evidence = SourceEvidence(
            source_id="public/pricing",
            source_name="Public pricing page",
            before=DEMO_BEFORE,
            after=DEMO_AFTER,
            evidence_hash=_evidence_digest(DEMO_BEFORE, DEMO_AFTER),
            confidence=0.99,
            snapshot_label="Synthetic demo fixture · public/pricing",
        )
        self._event(state, "evidence_verifier", "verified")

        state.stage = Stage.MAP_IMPACT
        state.impacts = [
            ArtifactImpact(
                "Pricing battlecard", "Product Marketing", "Replace claim", "high"
            ),
            ArtifactImpact(
                "Renewal playbook", "Customer Success", "Add exception path", "high"
            ),
            ArtifactImpact(
                "Enterprise FAQ", "Support", "Revise retention answer", "medium"
            ),
            ArtifactImpact(
                "CRM guidance", "RevOps", "Update qualification note", "low"
            ),
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

    def approve(self, workflow_id: str, approver: str, decision: str) -> WorkflowState:
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

        state.approval = {
            "approver": cleaned_approver,
            "decision": decision,
            "timestamp": self._timestamp(),
            "evidence_hash": state.evidence.evidence_hash if state.evidence else None,
        }
        self._event(state, "policy_engine", "approval_recorded")
        state.stage = Stage.PUBLISH
        state.impacts = [
            ArtifactImpact(
                i.name,
                i.owner,
                i.action,
                i.risk,
                ["published", "published", "owner_review", "scheduled"][index],
            )
            for index, i in enumerate(state.impacts)
        ]
        self._event(state, "publisher", "2_published_1_queued_1_scheduled")
        state.status = WorkflowStatus.COMPLETE
        return state

    def undo(self, workflow_id: str, actor: str) -> WorkflowState:
        state = self.get(workflow_id)
        if state.status is not WorkflowStatus.COMPLETE or state.approval is None:
            raise PolicyViolation("There is no recorded human decision to undo")
        _require_named_human(actor, "actor")
        state.approval = None
        state.stage = Stage.AWAIT_APPROVAL
        state.status = WorkflowStatus.NEEDS_APPROVAL
        state.impacts = [
            ArtifactImpact(i.name, i.owner, i.action, i.risk) for i in state.impacts
        ]
        self._event(state, "policy_engine", "decision_undone")
        return state


workflow_store = DriftlineWorkflow()
