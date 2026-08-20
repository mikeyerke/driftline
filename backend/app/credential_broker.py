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

    def metadata(self) -> dict[str, str]:
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
        }


def allowed_operations(connector: str) -> list[str]:
    """Return the product-owned operation scope for one connector."""
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise CredentialBrokerError("connector_not_allowlisted") from exc
    return sorted(CONNECTOR_OPERATIONS[safe_connector])


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
    expected_secret = tenant_connector_secret_name(safe_tenant, safe_connector)
    if str(binding.get("secret_name", "")) != expected_secret:
        raise CredentialBrokerError("secret_name_mismatch")

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
        credential_id=str(binding.get("credential_id") or f"{safe_tenant}:{safe_connector}"),
        operation=safe_operation,
        secret_name=expected_secret,
        secret_version=secret_version,
        value=value,
        issued_at=issued_at.isoformat(),
        expires_at=expires_at.isoformat(),
    )
    _record_access(
        {
            **lease.metadata(),
            "outcome": "resolved",
        },
        access_writer,
    )
    return lease
