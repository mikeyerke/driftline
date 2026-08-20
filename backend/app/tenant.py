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
    binding = configured.get(normalized_email)
    if binding:
        tenant_id, role = binding
    else:
        tenant_id = validate_tenant_id(
            requested_tenant_id
            or os.getenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
        )
        role = os.getenv("DRIFTLINE_DEFAULT_TENANT_ROLE", "owner").casefold()
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
