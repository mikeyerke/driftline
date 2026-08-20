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
