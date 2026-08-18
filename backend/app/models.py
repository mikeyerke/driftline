from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Stage(StrEnum):
    MONITOR = "monitor"
    VERIFY = "verify"
    MAP_IMPACT = "map_impact"
    DRAFT = "draft_updates"
    AWAIT_APPROVAL = "await_approval"
    PUBLISH = "publish"


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    NEEDS_APPROVAL = "needs_approval"
    COMPLETE = "complete"


@dataclass(frozen=True)
class SourceEvidence:
    source_id: str
    source_name: str
    before: str
    after: str
    evidence_hash: str
    confidence: float
    snapshot_label: str = "Synthetic demo fixture"


@dataclass(frozen=True)
class ArtifactImpact:
    name: str
    owner: str
    action: str
    risk: str
    status: str = "draft_ready"


@dataclass
class WorkflowState:
    workflow_id: str
    title: str
    stage: Stage = Stage.MONITOR
    status: WorkflowStatus = WorkflowStatus.RUNNING
    evidence: SourceEvidence | None = None
    impacts: list[ArtifactImpact] = field(default_factory=list)
    approval: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    data_mode: str = "synthetic_demo"

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
