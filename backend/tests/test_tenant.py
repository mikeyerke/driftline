from __future__ import annotations

import pytest

from app import persistence
from app.tenant import (
    principal_for_claims,
    tenant_connector_secret_name,
    tenant_credential_namespace,
    tenant_secret_resource_name,
    tenant_service_account_email,
    tenant_service_account_id,
    validate_connector_profile,
)


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


def test_single_persisted_membership_is_discovered_without_default_tenant(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.delenv("DRIFTLINE_TENANT_MEMBERS", raising=False)
    persistence.persist_tenant({"tenant_id": "discovered-acme", "status": "active"})
    persistence.persist_tenant_membership(
        {
            "tenant_id": "discovered-acme",
            "email": "discover@example.com",
            "role": "operator",
            "status": "active",
        }
    )

    principal = principal_for_claims(
        subject="subject-discovered",
        email="discover@example.com",
    )

    assert principal.tenant_id == "discovered-acme"
    assert principal.role == "operator"


def test_multiple_persisted_memberships_require_explicit_tenant_selection(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.delenv("DRIFTLINE_TENANT_MEMBERS", raising=False)
    for tenant_id in ("choice-acme", "choice-beta"):
        persistence.persist_tenant({"tenant_id": tenant_id, "status": "active"})
        persistence.persist_tenant_membership(
            {
                "tenant_id": tenant_id,
                "email": "multi@example.com",
                "role": "viewer",
                "status": "active",
            }
        )

    import pytest

    with pytest.raises(PermissionError, match="tenant_selection_required"):
        principal_for_claims(subject="subject-multi", email="multi@example.com")


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


def test_firestore_membership_directory_does_not_fall_back_to_env_mapping(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")
    monkeypatch.setenv("DRIFTLINE_TENANT_MEMBERS", "owner@example.com=env-acme:owner")
    monkeypatch.setattr(persistence, "load_tenant_membership", lambda *_args: None)

    try:
        principal_for_claims(
            subject="owner-subject",
            email="owner@example.com",
            requested_tenant_id="env-acme",
        )
    except PermissionError as exc:
        assert str(exc) == "tenant_membership_required"
    else:  # pragma: no cover - explicit fail-closed assertion
        raise AssertionError("Firestore auth unexpectedly used environment mapping")


def test_firestore_status_check_failure_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")
    monkeypatch.delenv("DRIFTLINE_TENANT_MEMBERS", raising=False)
    monkeypatch.setattr(
        persistence,
        "load_tenant_membership",
        lambda *_args: {
            "tenant_id": "status-acme",
            "email": "owner@example.com",
            "role": "owner",
            "status": "active",
        },
    )
    monkeypatch.setattr(
        persistence,
        "load_tenant",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("firestore unavailable")),
    )

    try:
        principal_for_claims(
            subject="owner-subject",
            email="owner@example.com",
            requested_tenant_id="status-acme",
        )
    except PermissionError as exc:
        assert str(exc) == "tenant_disabled"
    else:  # pragma: no cover - explicit fail-closed assertion
        raise AssertionError("Firestore status failure unexpectedly authorized")


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


def test_salesforce_uses_shared_tenant_secret_namespace() -> None:
    assert (
        tenant_connector_secret_name("acme", "salesforce")
        == "driftline-tenant-acme-salesforce"
    )
    assert validate_connector_profile(
        "salesforce", {"instance_url": "https://acme.my.salesforce.com"}
    )["instance_url"].startswith("https://")


@pytest.mark.parametrize(
    ("connector", "key", "value"),
    [
        ("jira", "base_url", "https://evil-atlassian.net.example/"),
        ("slack", "base_url", "https://collector.example/api/"),
        ("github", "api_url", "https://169.254.169.254/"),
        ("salesforce", "instance_url", "https://force.com.example/"),
    ],
)
def test_connector_profile_rejects_untrusted_service_hosts(
    connector: str, key: str, value: str
) -> None:
    with pytest.raises(ValueError, match="connector_profile_url_not_allowlisted"):
        validate_connector_profile(connector, {key: value})


def test_tenant_service_identity_is_deterministic_and_bounded(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "driftline-hackathon-2026")
    first = tenant_service_account_id("a-long-customer-tenant-name")
    assert first == tenant_service_account_id("a-long-customer-tenant-name")
    assert len(first) <= 30
    assert first.startswith("driftline-a-long-custo-")
    assert tenant_service_account_email("a-long-customer-tenant-name").endswith(
        "@driftline-hackathon-2026.iam.gserviceaccount.com"
    )
    assert tenant_service_account_id("a-long-customer-tenant-name") != tenant_service_account_id(
        "a-long-customer-tenant-names"
    )


def test_tenant_credential_namespace_is_fully_qualified(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "driftline-hackathon-2026")
    resource = tenant_secret_resource_name("acme", "jira")
    namespace = tenant_credential_namespace("acme", "jira")
    assert resource == (
        "projects/driftline-hackathon-2026/secrets/"
        "driftline-tenant-acme-jira"
    )
    assert namespace["schema_version"] == 1
    assert namespace["tenant_id"] == "acme"
    assert namespace["connector"] == "jira"
    assert namespace["secret_resource"] == resource
    assert namespace["service_account"].startswith("driftline-acme-")
