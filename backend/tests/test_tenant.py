from __future__ import annotations

from app import persistence
from app.tenant import principal_for_claims


def test_persisted_membership_can_authorize_a_tenant_without_env_mapping(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.delenv("DRIFTLINE_TENANT_MEMBERS", raising=False)
    monkeypatch.setenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
    monkeypatch.setenv("DRIFTLINE_DEFAULT_TENANT_ROLE", "viewer")
    persistence.persist_tenant_membership(
        {
            "tenant_id": "persisted-acme",
            "email": "operator@example.com",
            "role": "operator",
            "status": "active",
        }
    )

    principal = principal_for_claims(
        subject="subject-1",
        email="operator@example.com",
        requested_tenant_id="persisted-acme",
    )

    assert principal.tenant_id == "persisted-acme"
    assert principal.role == "operator"
    assert principal.can("operator") is True


def test_unprovisioned_oidc_identity_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.delenv("DRIFTLINE_TENANT_MEMBERS", raising=False)

    try:
        principal_for_claims(
            subject="unknown-subject",
            email="unknown@example.com",
            requested_tenant_id="arbitrary-acme",
        )
    except PermissionError as exc:
        assert str(exc) == "tenant_membership_required"
    else:  # pragma: no cover - explicit fail-closed assertion
        raise AssertionError("unprovisioned OIDC identity unexpectedly authorized")


def test_disabled_durable_membership_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.delenv("DRIFTLINE_TENANT_MEMBERS", raising=False)
    persistence.persist_tenant_membership(
        {
            "tenant_id": "disabled-acme",
            "email": "disabled@example.com",
            "role": "operator",
            "status": "disabled",
        }
    )

    try:
        principal_for_claims(
            subject="disabled-subject",
            email="disabled@example.com",
            requested_tenant_id="disabled-acme",
        )
    except PermissionError as exc:
        assert str(exc) == "tenant_membership_inactive"
    else:  # pragma: no cover - explicit fail-closed assertion
        raise AssertionError("disabled tenant membership unexpectedly authorized")
