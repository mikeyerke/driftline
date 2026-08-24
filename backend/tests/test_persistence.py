from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app import persistence
from app.decision_twin import approve_decision_case, build_demo_decision_case
from app.models import JobState
from app.trace_eval import build_quality_fixture, run_quality_gate


def test_decision_case_memory_compare_and_set_is_atomic(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")

    class SlowGetDict(dict):
        def get(self, key, default=None):
            value = super().get(key, default)
            time.sleep(0.02)
            return value

    store = SlowGetDict()
    monkeypatch.setattr(persistence, "_decision_cases_memory", store)
    case = build_demo_decision_case(case_id="decision-atomic-cas")
    persistence.persist_decision_case(case)
    targets = [
        approve_decision_case(
            case,
            option_id=option_id,
            approver="Concurrency Tester",
            expected_synthesis_hash=case.council.synthesis_hash,
            expected_generation=1,
        )
        for option_id in ("ship", "rollback")
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda target: persistence.compare_and_set_decision_case(
                    target,
                    expected_generation=1,
                    expected_statuses={"needs_approval"},
                ),
                targets,
            )
        )

    assert sorted(results) == [False, True]
    stored = persistence.load_decision_case(case.case_id)
    assert stored is not None
    assert stored.status == "experiment_active"
    assert stored.approval.option_id in {"ship", "rollback"}


def test_decision_case_firestore_audit_failure_rolls_back_parent(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")
    case = build_demo_decision_case(case_id="decision-atomic-audit")
    approved = approve_decision_case(
        case,
        option_id="segment",
        approver="Audit Tester",
        expected_synthesis_hash=case.council.synthesis_hash,
        expected_generation=1,
    )
    documents = {
        (persistence.DECISION_CASES_COLLECTION, case.case_id): case.model_dump(
            mode="json"
        )
    }

    class FakeSnapshot:
        def __init__(self, payload):
            self.exists = payload is not None
            self._payload = payload

        def to_dict(self):
            return dict(self._payload) if self._payload is not None else None

    class FakeDocument:
        def __init__(self, path):
            self.path = path

        def get(self, transaction=None):
            return FakeSnapshot(documents.get(self.path))

        def collection(self, name):
            return FakeCollection((*self.path, name))

    class FakeCollection:
        def __init__(self, path):
            self.path = path

        def document(self, document_id):
            return FakeDocument((*self.path, document_id))

    class FakeTransaction:
        def __init__(self):
            self.pending = []

        def set(self, reference, payload):
            self.pending.append(("set", reference, dict(payload)))

        def create(self, reference, payload):
            self.pending.append(("create", reference, dict(payload)))

        def run(self, callback):
            result = callback(self)
            if any(action == "create" for action, _, _ in self.pending):
                raise RuntimeError("audit-store-unavailable")
            for _, reference, payload in self.pending:
                documents[reference.path] = payload
            return result

    class FakeClient:
        def collection(self, name):
            return FakeCollection((name,))

        @staticmethod
        def transaction():
            return FakeTransaction()

    monkeypatch.setattr(persistence, "_client", lambda: FakeClient())
    monkeypatch.setattr(
        persistence.firestore,
        "transactional",
        lambda callback: lambda transaction: transaction.run(callback),
    )
    monkeypatch.setattr(
        persistence, "_retention_expiry", lambda _tenant_id: "expiry"
    )

    with pytest.raises(RuntimeError, match="audit-store-unavailable"):
        persistence.compare_and_set_decision_case(
            approved,
            expected_generation=1,
            expected_statuses={"needs_approval"},
        )

    assert documents[(persistence.DECISION_CASES_COLLECTION, case.case_id)][
        "status"
    ] == "needs_approval"


def test_tenant_bootstrap_is_atomic_in_memory(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    tenant_id = "atomic-bootstrap-acme"
    persistence._tenants_memory.pop(tenant_id, None)
    persistence._tenant_memberships_memory.pop((tenant_id, "owner@example.com"), None)

    def provision() -> bool:
        return persistence.provision_tenant_metadata(
            {"tenant_id": tenant_id, "status": "active"},
            {
                "tenant_id": tenant_id,
                "email": "owner@example.com",
                "role": "owner",
                "status": "active",
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: provision(), range(2)))

    assert sorted(results) == [False, True]
    assert persistence.load_tenant(tenant_id)["status"] == "active"


def test_trace_evaluation_ledger_is_append_only_and_tenant_scoped(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    persistence._evaluations_memory.clear()
    public_report = run_quality_gate(
        build_quality_fixture(),
        release_sha="a" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
        evaluation_id="eval-public-ledger",
    )
    tenant_report = run_quality_gate(
        build_quality_fixture(),
        release_sha="b" * 40,
        model="gemini-3.5-flash",
        execution_mode="google_adk",
        evaluation_id="eval-tenant-ledger",
    )
    tenant_report["tenant_id"] = "ledger-acme"

    stored_public = persistence.persist_evaluation(public_report)
    stored_tenant = persistence.persist_evaluation(tenant_report)

    assert stored_public["evaluation_id"] == "eval-public-ledger"
    assert stored_tenant["tenant_id"] == "ledger-acme"
    assert len(persistence.list_evaluations()) == 1
    assert len(persistence.list_evaluations("ledger-acme")) == 1
    assert persistence.load_latest_evaluation("ledger-acme")["evaluation_id"] == (
        "eval-tenant-ledger"
    )
    with pytest.raises(RuntimeError, match="already exists"):
        changed = dict(public_report)
        changed["overall_score"] = 0
        persistence.persist_evaluation(changed)


def test_workflow_state_roundtrip_preserves_aggregate_internal_context() -> None:
    restored = persistence._state_from_dict(
        {
            "workflow_id": "workflow-context-roundtrip",
            "title": "Competitor pricing",
            "tenant_id": "context-acme",
            "internal_context": {
                "status": "verified",
                "verified_connector_count": 1,
                "connectors": {
                    "jira": {
                        "status": "ok",
                        "external_read": True,
                        "scope": "project:DRIFT",
                        "open_issue_count": 12,
                    }
                },
            },
        }
    )

    assert restored.internal_context["status"] == "verified"
    assert restored.internal_context["connectors"]["jira"]["open_issue_count"] == 12


def test_job_roundtrip_preserves_monitor_disposition(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")

    class FakeSnapshot:
        exists = True

        @staticmethod
        def to_dict() -> dict[str, object]:
            return {
                "job_id": "job-monitor-roundtrip",
                "status": "complete",
                "run_mode": "monitor",
                "source_status": "unchanged",
                "change_detected": False,
                "created_at": "2026-08-22T00:00:00+00:00",
                "updated_at": "2026-08-22T00:00:01+00:00",
            }

    class FakeDocument:
        @staticmethod
        def get():
            return FakeSnapshot()

    class FakeCollection:
        @staticmethod
        def document(_job_id: str):
            return FakeDocument()

    class FakeClient:
        @staticmethod
        def collection(_name: str):
            return FakeCollection()

    monkeypatch.setattr(persistence, "_client", lambda: FakeClient())
    restored = persistence.load_job("job-monitor-roundtrip")

    assert isinstance(restored, JobState)
    assert restored.source_status == "unchanged"
    assert restored.change_detected is False


def test_tenant_bootstrap_audit_is_committed_with_metadata(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    tenant_id = "atomic-audit-acme"
    persistence._tenants_memory.pop(tenant_id, None)
    persistence._tenant_memberships_memory.pop((tenant_id, "owner@example.com"), None)
    persistence._tenant_audit_memory[:] = [
        event
        for event in persistence._tenant_audit_memory
        if event.get("tenant_id") != tenant_id
    ]

    created = persistence.provision_tenant_metadata(
        {"tenant_id": tenant_id, "status": "active"},
        {
            "tenant_id": tenant_id,
            "email": "owner@example.com",
            "role": "owner",
            "status": "active",
        },
        audit_payload={
            "event_id": "tenant-audit-atomic-audit-acme",
            "event_type": "tenant_provisioned",
            "status": "active",
        },
    )

    assert created is True
    events = persistence.list_tenant_audit_events(tenant_id)
    assert len(events) == 1
    assert events[0]["event_id"] == "tenant-audit-atomic-audit-acme"


def test_connector_binding_is_control_plane_metadata_not_ttl_content(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    binding = persistence.persist_connector_binding(
        {
            "tenant_id": "retention-acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-retention-acme-jira",
            "status": "active",
            "expires_at": "stale-test-value",
        }
    )

    assert "expires_at" not in binding
    loaded = persistence.load_connector_binding("retention-acme", "jira")
    assert loaded is not None
    assert "expires_at" not in loaded


def test_credential_enrollment_is_tenant_namespaced_and_secret_free(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    enrollment = persistence.persist_credential_enrollment(
        {
            "tenant_id": "enrollment-acme",
            "connector": "jira",
            "enrollment_id": "enroll-test-1",
            "status": "awaiting_secret",
            "secret_name": "driftline-tenant-enrollment-acme-jira",
            "allowed_operations": ["runtime", "read_context"],
            "expires_at": "2099-01-01T00:00:00+00:00",
            "access_token": "must-not-persist",
        }
    )

    assert enrollment["tenant_id"] == "enrollment-acme"
    assert enrollment["status"] == "awaiting_secret"
    assert "access_token" not in enrollment
    loaded = persistence.load_credential_enrollment(
        "enrollment-acme", "jira", "enroll-test-1"
    )
    assert loaded is not None
    assert loaded["secret_name"] == "driftline-tenant-enrollment-acme-jira"
    assert (
        persistence.load_credential_enrollment(
            "other-acme", "jira", "enroll-test-1"
        )
        is None
    )


def test_tenant_usage_is_period_scoped_and_aggregate_only(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    first = persistence.record_tenant_usage(
        "usage-acme", "agent_calls", period="2026-08"
    )
    second = persistence.record_tenant_usage(
        "usage-acme", "workflow_mutations", amount=2, period="2026-08"
    )
    current = persistence.load_tenant_usage("usage-acme", period="2026-08")
    other_period = persistence.load_tenant_usage("usage-acme", period="2026-07")

    assert first["agent_calls"] == 1
    assert second["workflow_mutations"] == 2
    assert current["agent_calls"] == 1
    assert current["workflow_mutations"] == 2
    assert current["connector_calls"] == 0
    assert current["monitor_jobs"] == 0
    assert other_period["agent_calls"] == 0
    assert set(current) >= {"tenant_id", "period", "agent_calls"}


def test_tenant_policy_is_bounded_and_keeps_defaults_for_missing_fields(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    tenant_id = "policy-acme"
    persistence.persist_tenant({"tenant_id": tenant_id, "status": "active"})

    assert persistence.load_tenant_policy(tenant_id) == {
        "agent_calls_per_window": 10,
        "workflow_mutations_per_window": 30,
        "connector_calls_per_window": 60,
        "retention_days": 30,
    }
    policy = persistence.persist_tenant_policy(
        tenant_id,
        {
            "agent_calls_per_window": 5000,
            "workflow_mutations_per_window": 0,
            "retention_days": 5000,
            "unexpected": "discarded",
        },
    )
    assert policy == {
        "agent_calls_per_window": 1000,
        "workflow_mutations_per_window": 1,
        "connector_calls_per_window": 60,
        "retention_days": 3650,
    }
    stored = persistence.load_tenant(tenant_id)
    assert stored["policy"] == policy
    assert "unexpected" not in stored["policy"]
    updated = persistence.persist_tenant_policy(
        tenant_id, {"agent_calls_per_window": 8}
    )
    assert updated["agent_calls_per_window"] == 8
    assert updated["retention_days"] == 3650


def test_tenant_retention_policy_controls_metadata_ttl(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")

    class FakeDocument:
        def get(self):
            return SimpleNamespace(
                exists=True,
                to_dict=lambda: {"policy": {"retention_days": 7}},
            )

    class FakeCollection:
        def document(self, _tenant_id):
            return FakeDocument()

    class FakeClient:
        def collection(self, _name):
            return FakeCollection()

    monkeypatch.setattr(persistence, "_client", lambda: FakeClient())
    now = datetime.now(UTC)
    expiry = persistence._retention_expiry("ttl-acme")
    seconds = (expiry - now).total_seconds()
    assert 6.9 * 86400 < seconds < 7.1 * 86400


def test_tenant_rate_limit_reservation_is_window_and_tenant_scoped(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    persistence._tenant_rate_limit_memory.clear()

    assert persistence.reserve_tenant_rate_limit(
        "quota-acme", "agent_calls", 2, 60, now=121
    )
    assert persistence.reserve_tenant_rate_limit(
        "quota-acme", "agent_calls", 2, 60, now=122
    )
    assert not persistence.reserve_tenant_rate_limit(
        "quota-acme", "agent_calls", 2, 60, now=123
    )
    assert persistence.reserve_tenant_rate_limit(
        "quota-other", "agent_calls", 2, 60, now=123
    )
    assert persistence.reserve_tenant_rate_limit(
        "quota-acme", "agent_calls", 2, 60, now=180
    )
    assert persistence.reserve_tenant_rate_limit(
        "quota-acme", "connector_calls", 1, 60, now=121
    )
    assert not persistence.reserve_tenant_rate_limit(
        "quota-acme", "connector_calls", 1, 60, now=122
    )


def test_connector_profile_is_bounded_non_secret_metadata(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    profile = persistence.persist_connector_profile(
        {
            "tenant_id": "profile-acme",
            "connector": "jira",
            "settings": {
                "base_url": "https://profile.atlassian.net",
                "project_key": "PROF",
            },
        }
    )

    assert profile["settings"]["project_key"] == "PROF"
    assert "token" not in str(profile).casefold()
    assert persistence.load_connector_profile("profile-acme", "jira") == profile
    with pytest.raises(ValueError, match="not_allowlisted"):
        persistence.persist_connector_profile(
            {
                "tenant_id": "profile-acme",
                "connector": "jira",
                "settings": {"token": "must-never-persist"},
            }
        )


def test_connector_profile_rejects_invalid_tenant_namespace(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    with pytest.raises(ValueError, match="tenant_id_invalid"):
        persistence.persist_connector_profile(
            {
                "tenant_id": "../other-tenant",
                "connector": "jira",
                "settings": {"project_key": "SAFE"},
            }
        )
