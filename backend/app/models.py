from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


def utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()


class Stage(StrEnum):
    MONITOR = "monitor"
    VERIFY = "verify"
    MAP_IMPACT = "map_impact"
    DRAFT = "draft_updates"
    AWAIT_APPROVAL = "await_approval"
    PUBLISH = "publish"


class WorkflowStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_APPROVAL = "needs_approval"
    APPROVAL_EXECUTING = "approval_executing"
    REVERSAL_EXECUTING = "reversal_executing"
    COMPLETE = "complete"
    DISMISSED = "dismissed"
    FAILED = "failed"


class ActionItemStatus(StrEnum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


@dataclass(frozen=True)
class SourceEvidence:
    source_id: str
    source_name: str
    before: str
    after: str
    evidence_hash: str
    confidence: float
    snapshot_label: str = "Synthetic demo fixture"
    source_url: str | None = None
    retrieved_at: str | None = None
    snapshot_hash: str | None = None
    previous_snapshot_hash: str | None = None


@dataclass(frozen=True)
class ArtifactImpact:
    name: str
    owner: str
    action: str
    risk: str
    status: str = "draft_ready"
    detail: str = ""
    proposed: str = ""
    evidence_hash: str = ""


@dataclass
class WorkflowState:
    workflow_id: str
    title: str
    tenant_id: str | None = None
    stage: Stage = Stage.MONITOR
    status: WorkflowStatus = WorkflowStatus.RUNNING
    evidence: SourceEvidence | None = None
    impacts: list[ArtifactImpact] = field(default_factory=list)
    approval: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    data_mode: str = "synthetic_demo"
    artifact_packets: list[dict[str, Any]] = field(default_factory=list)
    action_record: dict[str, Any] | None = None
    action_items: list[dict[str, Any]] = field(default_factory=list)
    impact_graph: dict[str, Any] = field(default_factory=dict)
    change_card: dict[str, Any] = field(default_factory=dict)
    integration_targets: list[dict[str, Any]] = field(default_factory=list)
    # Bounded aggregate connector metadata captured only for a signed tenant
    # run.  Raw records, message text, document bodies, and credentials never
    # enter workflow state.
    internal_context: dict[str, Any] = field(default_factory=dict)
    agent_trace: dict[str, Any] | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a Firestore/API-safe representation of the state."""

        def serialise(value: Any) -> Any:
            if isinstance(value, StrEnum):
                return value.value
            if isinstance(value, dict):
                return {key: serialise(item) for key, item in value.items()}
            if isinstance(value, list):
                return [serialise(item) for item in value]
            return value

        return serialise(asdict(self))


@dataclass
class JobState:
    """Durable asynchronous execution record for a judge-visible run."""

    job_id: str
    kind: str = "change_scan"
    status: str = "queued"
    query: str = ""
    user_id: str = "demo-operator"
    tenant_id: str | None = None
    run_mode: str = "demo"
    source_id: str = "public/pricing"
    # Deterministic monitor disposition, kept separate from the job lifecycle.
    # ``complete`` only means the job finished; this field tells the operator
    # whether it established a baseline, confirmed a no-op, or found a change.
    source_status: str | None = None
    change_detected: bool | None = None
    # Links a bounded operator retry to its terminal predecessor.  Keeping
    # this on the durable job makes retry requests idempotent across Cloud Run
    # instances instead of relying on a browser button to prevent duplicates.
    retry_of: str | None = None
    workflow_id: str | None = None
    model: str | None = None
    execution_mode: str | None = None
    tool_calls: list[str] = field(default_factory=list)
    event_count: int = 0
    response: str = ""
    error: str | None = None
    # A durable claim prevents Cloud Tasks retries from starting a second
    # Gemini run for the same job.  It is intentionally opaque to callers.
    claim_id: str | None = None
    run_attempts: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
