"""Tenant-scoped credential broker.

This module is the single seam through which connector adapters resolve a
provider credential.  Callers provide a tenant, an allowlisted connector, and
an operation; the broker owns the binding lookup, deterministic Secret
Manager reference check, pinned-version read, short lease metadata, and
metadata-only access audit.  Credential values never cross this interface's
metadata responses and are never written to the audit ledger.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .tenant import (
    tenant_connector_secret_name,
    tenant_credential_namespace,
    tenant_service_account_email,
    validate_connector_name,
    validate_tenant_id,
)


class CredentialBrokerError(RuntimeError):
    """A tenant credential could not be safely leased."""


CONNECTOR_OPERATIONS: dict[str, frozenset[str]] = {
    "jira": frozenset({"runtime", "read_context", "create_issue", "reverse_issue"}),
    "confluence": frozenset(
        {"runtime", "read_context", "create_page", "reverse_page"}
    ),
    "slack": frozenset({"runtime", "read_context", "post_message", "reverse_message"}),
    "github": frozenset({"runtime", "read_context", "create_issue", "reverse_issue"}),
    "salesforce": frozenset({"runtime", "read_context"}),
}

READ_ONLY_OPERATIONS = frozenset({"runtime", "read_context"})


@dataclass(frozen=True)
class CredentialLease:
    """Short-lived in-process credential lease; never serialize ``value``."""

    lease_id: str
    tenant_id: str
    connector: str
    credential_id: str
    operation: str
    secret_name: str
    secret_version: str
    value: str
    issued_at: str
    expires_at: str
    namespace_verified: bool = False

    def metadata(self) -> dict[str, object]:
        """Return a safe audit/API view without the credential value."""
        return {
            "lease_id": self.lease_id,
            "tenant_id": self.tenant_id,
            "connector": self.connector,
            "credential_id": self.credential_id,
            "operation": self.operation,
            "secret_version": self.secret_version,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "namespace_verified": self.namespace_verified,
        }


def allowed_operations(connector: str) -> list[str]:
    """Return the product-owned operation scope for one connector."""
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise CredentialBrokerError("connector_not_allowlisted") from exc
    return sorted(CONNECTOR_OPERATIONS[safe_connector])


def normalize_allowed_operations(
    connector: str,
    requested: list[str] | tuple[str, ...] | set[str] | None = None,
    *,
    default: str = "all",
) -> list[str]:
    """Validate a tenant binding's least-privilege operation scope.

    ``default=read_only`` is used by new enrollment sessions so a connector
    cannot silently gain downstream writes. Existing binding verification
    keeps ``default=all`` for backwards-compatible migrations; owners can
    narrow or explicitly expand that scope in a later verification.
    """
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise CredentialBrokerError("connector_not_allowlisted") from exc
    if requested is None:
        operations = (
            READ_ONLY_OPERATIONS
            if default == "read_only"
            else CONNECTOR_OPERATIONS[safe_connector]
        )
    else:
        if not isinstance(requested, (list, tuple, set)):
            raise CredentialBrokerError("credential_scope_invalid")
        operations = {
            str(value).strip().casefold()
            for value in requested
            if str(value).strip()
        }
        if not operations:
            raise CredentialBrokerError("credential_scope_empty")
    if not operations.issubset(CONNECTOR_OPERATIONS[safe_connector]):
        raise CredentialBrokerError("credential_scope_not_allowlisted")
    return sorted(operations)


def _lease_seconds() -> int:
    try:
        configured = int(os.getenv("DRIFTLINE_CREDENTIAL_LEASE_SECONDS", "300"))
    except ValueError:
        configured = 300
    return max(30, min(configured, 900))


def _safe_secret_version(value: object) -> str:
    version = str(value or "latest").strip() or "latest"
    if version != "latest" and not re.fullmatch(r"[1-9][0-9]*", version):
        raise CredentialBrokerError("secret_version_invalid")
    return version


def _record_access(payload: dict[str, object], writer: Callable[[dict[str, object]], object] | None) -> None:
    if writer is None:
        from .persistence import persist_credential_access_event

        writer = persist_credential_access_event
    try:
        writer(payload)
    except Exception as exc:
        raise CredentialBrokerError("credential_access_audit_unavailable") from exc


def resolve_tenant_credential(
    tenant_id: str,
    connector: str,
    *,
    operation: str = "runtime",
    secret_reader: Callable[..., str],
    access_writer: Callable[[dict[str, object]], object] | None = None,
) -> CredentialLease:
    """Resolve one active tenant binding into a bounded in-process lease.

    The caller never supplies a secret name.  The broker derives the expected
    name from the tenant/connector pair and rejects cross-tenant references,
    revoked bindings, unapproved operations, missing durable tenants, and
    invalid versions before reading Secret Manager.
    """
    try:
        safe_tenant = validate_tenant_id(tenant_id)
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise CredentialBrokerError("tenant_or_connector_invalid") from exc
    safe_operation = operation.strip().casefold()
    if safe_operation not in CONNECTOR_OPERATIONS[safe_connector]:
        raise CredentialBrokerError("operation_not_allowlisted")

    try:
        from .persistence import load_connector_binding, load_tenant

        if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore":
            tenant = load_tenant(safe_tenant)
            if not tenant or str(tenant.get("status", "")).casefold() != "active":
                raise CredentialBrokerError("tenant_not_active")
        binding = load_connector_binding(safe_tenant, safe_connector)
    except CredentialBrokerError:
        raise
    except Exception as exc:
        raise CredentialBrokerError("credential_binding_lookup_failed") from exc

    if not binding or str(binding.get("status", "")).casefold() != "active":
        raise CredentialBrokerError("credential_binding_unavailable")
    if str(binding.get("tenant_id", safe_tenant)) != safe_tenant:
        raise CredentialBrokerError("credential_tenant_mismatch")
    if str(binding.get("connector", safe_connector)) != safe_connector:
        raise CredentialBrokerError("credential_connector_mismatch")
    expected_secret = tenant_connector_secret_name(safe_tenant, safe_connector)
    if str(binding.get("secret_name", "")) != expected_secret:
        raise CredentialBrokerError("secret_name_mismatch")

    # New bindings carry a fully-qualified namespace. Accept legacy records
    # during migration, but if the metadata exists it must agree with the
    # authenticated tenant, connector, project, and service identity before a
    # provider value is read.
    namespace = binding.get("credential_namespace")
    if namespace is not None:
        if not isinstance(namespace, dict):
            raise CredentialBrokerError("credential_namespace_invalid")
        try:
            expected_namespace = tenant_credential_namespace(
                safe_tenant, safe_connector
            )
        except ValueError as exc:
            raise CredentialBrokerError("credential_namespace_invalid") from exc
        for key in (
            "schema_version",
            "tenant_id",
            "connector",
            "secret_resource",
            "service_account",
            "isolation",
        ):
            if str(namespace.get(key, "")) != str(expected_namespace[key]):
                raise CredentialBrokerError("credential_namespace_mismatch")
    elif (
        os.getenv("DRIFTLINE_TENANT_SECRET_IDENTITY_MODE", "direct").casefold()
        == "impersonated"
        and os.getenv(
            "DRIFTLINE_REQUIRE_TENANT_CREDENTIAL_NAMESPACE", "false"
        ).casefold()
        == "true"
    ):
        # Operators can turn this on after the one-time migration. Keeping the
        # switch explicit lets a rolling deployment read pre-migration records
        # without weakening the new namespace checks for migrated tenants.
        try:
            expected_service = tenant_service_account_email(safe_tenant)
        except ValueError as exc:
            raise CredentialBrokerError("credential_namespace_invalid") from exc
        if str(binding.get("service_account", "")) != expected_service:
            raise CredentialBrokerError("credential_namespace_required")

    configured_operations = binding.get("allowed_operations")
    if configured_operations is None:
        configured_operations = list(CONNECTOR_OPERATIONS[safe_connector])
    if not isinstance(configured_operations, (list, tuple, set)):
        raise CredentialBrokerError("credential_scope_invalid")
    normalized_operations = {str(value).strip().casefold() for value in configured_operations}
    if safe_operation not in normalized_operations:
        raise CredentialBrokerError("operation_not_allowed")

    secret_version = _safe_secret_version(binding.get("secret_version"))
    try:
        try:
            value = secret_reader(expected_secret, version=secret_version).strip()
        except TypeError:
            # Small local adapters from older integrations accepted only the
            # secret name.  Preserve that compatibility path only for
            # ``latest``; a pinned version must never be silently discarded.
            if secret_version != "latest":
                raise
            value = secret_reader(expected_secret).strip()
    except Exception as exc:
        raise CredentialBrokerError("credential_read_failed") from exc
    if not value:
        raise CredentialBrokerError("credential_empty")

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(seconds=_lease_seconds())
    lease = CredentialLease(
        lease_id=f"lease-{uuid4().hex}",
        tenant_id=safe_tenant,
        connector=safe_connector,
        credential_id=str(
            binding.get("credential_id") or f"cred-{safe_tenant}-{safe_connector}"
        ),
        operation=safe_operation,
        secret_name=expected_secret,
        secret_version=secret_version,
        value=value,
        issued_at=issued_at.isoformat(),
        expires_at=expires_at.isoformat(),
        namespace_verified=isinstance(namespace, dict),
    )
    _record_access(
        {
            **lease.metadata(),
            "outcome": "resolved",
        },
        access_writer,
    )
    return lease
