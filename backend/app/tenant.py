"""Small, explicit tenant and role boundary for operator-grade routes.

The public demo remains packet-only.  Signed/OIDC requests carry a tenant
principal so every future connector can bind credentials and audit records to
one customer boundary.  The mapping is intentionally configuration-driven:
``DRIFTLINE_TENANT_MEMBERS`` accepts comma-separated
``email=tenant_id:role`` entries, for example
``mike@example.com=acme:owner``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

_TENANT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_ROLES = {"viewer", "operator", "owner"}
CONNECTOR_NAMES = frozenset({"jira", "confluence", "slack", "github"})


@dataclass(frozen=True)
class TenantPrincipal:
    tenant_id: str
    subject: str = ""
    email: str = ""
    role: str = "viewer"
    identity: str = "signed_operator"

    def can(self, required: str = "operator") -> bool:
        order = {"viewer": 0, "operator": 1, "owner": 2}
        return order.get(self.role, -1) >= order.get(required, 1)


def validate_tenant_id(value: str) -> str:
    tenant_id = value.strip().casefold()
    if not _TENANT_ID.fullmatch(tenant_id):
        raise ValueError("tenant_id_invalid")
    return tenant_id


def validate_connector_name(value: str) -> str:
    """Validate the small, product-owned connector allowlist."""
    connector = value.strip().casefold()
    if connector not in CONNECTOR_NAMES:
        raise ValueError("connector_not_allowlisted")
    return connector


def tenant_connector_secret_name(tenant_id: str, connector: str) -> str:
    """Return the deterministic Secret Manager name for one tenant connector."""
    safe_tenant = validate_tenant_id(tenant_id)
    safe_connector = validate_connector_name(connector)
    return f"driftline-tenant-{safe_tenant}-{safe_connector}"[:100]


def _configured_members() -> dict[str, tuple[str, str]]:
    members: dict[str, tuple[str, str]] = {}
    for raw in os.getenv("DRIFTLINE_TENANT_MEMBERS", "").split(","):
        entry = raw.strip()
        if not entry or "=" not in entry:
            continue
        email, binding = entry.split("=", 1)
        if ":" not in binding:
            continue
        tenant_id, role = binding.rsplit(":", 1)
        try:
            tenant_id = validate_tenant_id(tenant_id)
        except ValueError:
            continue
        role = role.strip().casefold()
        if role not in _ROLES:
            continue
        members[email.strip().casefold()] = (tenant_id, role)
    return members


def principal_for_claims(
    *,
    subject: str,
    email: str,
    requested_tenant_id: str | None = None,
    identity: str = "google_oidc_operator",
) -> TenantPrincipal:
    normalized_email = email.strip().casefold()
    configured = _configured_members()
    persisted = None
    try:
        # Lazy import avoids coupling the pure tenant parser to Firestore
        # during local synthetic runs while allowing durable memberships
        # to survive environment/configuration rollouts.
        from .persistence import load_tenant_membership

        persisted_tenant = validate_tenant_id(
            requested_tenant_id
            or os.getenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
        )
        persisted = load_tenant_membership(persisted_tenant, normalized_email)
    except Exception:  # noqa: BLE001 - auth falls back to explicit bootstrap config.
        persisted = None
    if persisted:
        if str(persisted.get("status", "active")).casefold() != "active":
            raise PermissionError("tenant_membership_inactive")
        tenant_id = validate_tenant_id(str(persisted["tenant_id"]))
        role = str(persisted.get("role", "viewer")).casefold()
    else:
        binding = configured.get(normalized_email)
        if not binding:
            # OIDC identities must be explicitly mapped to a tenant. Falling
            # back to the default tenant here would let an authenticated but
            # unprovisioned user claim an arbitrary tenant/owner role.
            raise PermissionError("tenant_membership_required")
        tenant_id, role = binding
        if role not in _ROLES:
            role = "viewer"
    if requested_tenant_id:
        requested = validate_tenant_id(requested_tenant_id)
        if requested != tenant_id:
            raise PermissionError("tenant_not_allowlisted")
    return TenantPrincipal(
        tenant_id=tenant_id,
        subject=subject,
        email=normalized_email,
        role=role,
        identity=identity,
    )


def principal_for_hmac(requested_tenant_id: str | None = None) -> TenantPrincipal:
    tenant_id = validate_tenant_id(
        requested_tenant_id
        or os.getenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
    )
    configured_tenants: set[str] = set()
    for raw in os.getenv("DRIFTLINE_HMAC_TENANTS", "").split(","):
        if not raw.strip():
            continue
        try:
            configured_tenants.add(validate_tenant_id(raw))
        except ValueError:
            continue
    if not configured_tenants:
        configured_tenants.add(
            validate_tenant_id(
                os.getenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
            )
        )
    if tenant_id not in configured_tenants:
        raise PermissionError("tenant_not_allowlisted")
    return TenantPrincipal(
        tenant_id=tenant_id,
        role="owner",
        identity="signed_operator",
    )


def public_demo_principal() -> TenantPrincipal:
    return TenantPrincipal(
        tenant_id="demo-tenant",
        role="viewer",
        identity="named_demo_actor",
    )
