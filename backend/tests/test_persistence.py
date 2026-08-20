from __future__ import annotations

from app import persistence


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
