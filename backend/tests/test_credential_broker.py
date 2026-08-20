from __future__ import annotations

import pytest

from app.credential_broker import (
    CredentialBrokerError,
    normalize_allowed_operations,
    resolve_tenant_credential,
)
from app.tenant import tenant_credential_namespace


def test_new_enrollment_scope_defaults_read_only_and_rejects_unknown_operations() -> None:
    assert normalize_allowed_operations("jira", default="read_only") == [
        "read_context",
    ]
    with pytest.raises(CredentialBrokerError, match="credential_scope_not_allowlisted"):
        normalize_allowed_operations("jira", ["delete_project"])


def test_resolver_returns_scoped_lease_and_never_accepts_arbitrary_secret_name(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda tenant, connector: {
            "tenant_id": tenant,
            "connector": connector,
            "secret_name": "driftline-tenant-acme-jira",
            "secret_version": "7",
            "credential_id": "cred-acme-jira-1",
            "allowed_operations": ["runtime", "create_issue"],
            "status": "active",
        },
    )

    lease = resolve_tenant_credential(
        "acme",
        "jira",
        operation="create_issue",
        secret_reader=lambda name, version="latest": (
            f"value-for-{name}-v{version}"
        ),
    )

    assert lease.value == "value-for-driftline-tenant-acme-jira-v7"
    assert lease.tenant_id == "acme"
    assert lease.connector == "jira"
    assert lease.credential_id == "cred-acme-jira-1"
    assert lease.secret_version == "7"
    assert lease.operation == "create_issue"
    assert lease.expires_at > lease.issued_at


def test_resolver_fails_closed_for_cross_tenant_secret_reference(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-other-jira",
            "status": "active",
        },
    )

    with pytest.raises(CredentialBrokerError, match="secret_name_mismatch"):
        resolve_tenant_credential(
            "acme",
            "jira",
            secret_reader=lambda *_args, **_kwargs: "should-not-read",
        )


def test_resolver_fails_closed_for_namespace_schema_or_isolation_mismatch(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "driftline-hackathon-2026")
    namespace = tenant_credential_namespace(
        "acme", "jira", "driftline-hackathon-2026"
    )
    namespace["isolation"] = "deployment_shared"
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-acme-jira",
            "credential_namespace": namespace,
            "status": "active",
        },
    )

    with pytest.raises(CredentialBrokerError, match="credential_namespace_mismatch"):
        resolve_tenant_credential(
            "acme",
            "jira",
            secret_reader=lambda *_args, **_kwargs: "should-not-read",
        )


def test_resolver_fails_closed_for_unapproved_operation(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-acme-jira",
            "allowed_operations": ["runtime"],
            "status": "active",
        },
    )

    with pytest.raises(CredentialBrokerError, match="operation_not_allowed"):
        resolve_tenant_credential(
            "acme",
            "jira",
            operation="create_issue",
            secret_reader=lambda *_args, **_kwargs: "should-not-read",
        )


def test_read_only_enrollment_scope_cannot_lease_external_write(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-acme-jira",
            "allowed_operations": normalize_allowed_operations("jira", default="read_only"),
            "status": "active",
        },
    )
    with pytest.raises(CredentialBrokerError, match="operation_not_allowed"):
        resolve_tenant_credential(
            "acme",
            "jira",
            operation="create_issue",
            secret_reader=lambda *_args, **_kwargs: "should-not-read",
        )


def test_legacy_binding_without_scope_is_read_only_by_default(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-acme-jira",
            "status": "active",
        },
    )
    with pytest.raises(CredentialBrokerError, match="operation_not_allowed"):
        resolve_tenant_credential(
            "acme",
            "jira",
            operation="create_issue",
            secret_reader=lambda *_args, **_kwargs: "should-not-read",
        )


def test_resolver_records_metadata_only_access(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "salesforce",
            "secret_name": "driftline-tenant-acme-salesforce",
            "credential_id": "cred-acme-sf-1",
            "status": "active",
        },
    )
    events: list[dict[str, object]] = []

    lease = resolve_tenant_credential(
        "acme",
        "salesforce",
        secret_reader=lambda *_args, **_kwargs: "refresh-token",
        access_writer=events.append,
    )

    assert lease.value == "refresh-token"
    assert events and events[0]["tenant_id"] == "acme"
    assert events[0]["credential_id"] == "cred-acme-sf-1"
    assert events[0]["operation"] == "read_context"
    assert events[0]["outcome"] == "resolved"
    assert "value" not in events[0]
    assert "refresh-token" not in str(events[0])


def test_resolver_rejects_mismatched_credential_namespace(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "driftline-hackathon-2026")
    namespace = tenant_credential_namespace("acme", "jira")
    namespace["secret_resource"] = (
        "projects/driftline-hackathon-2026/secrets/driftline-tenant-other-jira"
    )
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "jira",
            "secret_name": "driftline-tenant-acme-jira",
            "credential_namespace": namespace,
            "status": "active",
        },
    )
    with pytest.raises(CredentialBrokerError, match="credential_namespace_mismatch"):
        resolve_tenant_credential(
            "acme",
            "jira",
            secret_reader=lambda *_args, **_kwargs: "should-not-read",
        )


def test_resolver_marks_migrated_namespace_in_lease(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "driftline-hackathon-2026")
    namespace = tenant_credential_namespace("acme", "salesforce")
    monkeypatch.setattr(
        "app.persistence.load_connector_binding",
        lambda *_args: {
            "tenant_id": "acme",
            "connector": "salesforce",
            "secret_name": "driftline-tenant-acme-salesforce",
            "credential_namespace": namespace,
            "status": "active",
        },
    )
    events: list[dict[str, object]] = []
    lease = resolve_tenant_credential(
        "acme",
        "salesforce",
        secret_reader=lambda *_args, **_kwargs: "refresh-token",
        access_writer=events.append,
    )
    assert lease.namespace_verified is True
    assert events[0]["namespace_verified"] is True
