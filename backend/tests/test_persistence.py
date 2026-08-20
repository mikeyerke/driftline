from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from app import persistence


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
        "retention_days": 3650,
    }
    stored = persistence.load_tenant(tenant_id)
    assert stored["policy"] == policy
    assert "unexpected" not in stored["policy"]


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
