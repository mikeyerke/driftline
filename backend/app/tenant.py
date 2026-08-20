"""Small, explicit tenant and role boundary for operator-grade routes.

The public demo remains packet-only.  Signed/OIDC requests carry a tenant
principal so every future connector can bind credentials and audit records to
one customer boundary.  The mapping is intentionally configuration-driven:
``DRIFTLINE_TENANT_MEMBERS`` accepts comma-separated
``email=tenant_id:role`` entries, for example
``mike@example.com=acme:owner``.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass

_TENANT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_ROLES = {"viewer", "operator", "owner"}
CONNECTOR_NAMES = frozenset({"jira", "confluence", "slack", "github", "salesforce"})
TENANT_CREDENTIAL_SCHEMA_VERSION = 1

# Non-secret destination metadata is deliberately narrower than the provider
# APIs. Credentials, arbitrary query/path fields, and user-supplied targets do
# not belong in a tenant profile. Connector adapters still validate URL and
# provider-specific constraints before making a request.
CONNECTOR_PROFILE_KEYS: dict[str, frozenset[str]] = {
    "jira": frozenset({"base_url", "email", "project_key", "issue_type"}),
    "confluence": frozenset(
        {"base_url", "email", "space_key", "parent_page_id"}
    ),
    "slack": frozenset({"base_url", "channel_id"}),
    "github": frozenset({"api_url", "owner", "repo"}),
    # Salesforce's instance URL is learned during OAuth and is non-secret
    # connection metadata. The refresh token remains in the tenant secret.
    "salesforce": frozenset({"instance_url"}),
}


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


def validate_connector_profile(
    connector: str, settings: dict[str, object]
) -> dict[str, str]:
    """Return bounded, non-secret settings for one allowlisted connector."""
    safe_connector = validate_connector_name(connector)
    if not isinstance(settings, dict) or not settings:
        raise ValueError("connector_profile_settings_required")
    allowed = CONNECTOR_PROFILE_KEYS[safe_connector]
    safe: dict[str, str] = {}
    for key, value in settings.items():
        if key not in allowed:
            raise ValueError("connector_profile_key_not_allowlisted")
        if not isinstance(value, str):
            raise TypeError("connector_profile_value_invalid")
        normalized = value.strip()
        if not normalized or len(normalized) > 500:
            raise ValueError("connector_profile_value_invalid")
        safe[key] = normalized
    return safe


def tenant_connector_secret_name(tenant_id: str, connector: str) -> str:
    """Return the deterministic Secret Manager name for one tenant connector."""
    safe_tenant = validate_tenant_id(tenant_id)
    safe_connector = validate_connector_name(connector)
    return f"driftline-tenant-{safe_tenant}-{safe_connector}"[:100]


def tenant_secret_resource_name(
    tenant_id: str, connector: str, project_id: str | None = None
) -> str:
    """Return the fully-qualified Secret Manager resource for one tenant.

    Connector callers never accept a resource name from a request.  They derive
    it from the authenticated tenant and fixed connector allowlist, which makes
    project and tenant swaps detectable before Secret Manager is touched.
    """
    project = (project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")).strip()
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project):
        raise ValueError("google_project_id_invalid")
    return (
        f"projects/{project}/secrets/"
        f"{tenant_connector_secret_name(tenant_id, connector)}"
    )


def tenant_credential_namespace(
    tenant_id: str, connector: str, project_id: str | None = None
) -> dict[str, str | int]:
    """Describe the stable control/data-plane namespace for one credential.

    This metadata is safe to persist and inspect: it contains no provider
    value.  The namespace is the contract shared by Firestore, Secret Manager,
    and the per-tenant service identity.
    """
    safe_tenant = validate_tenant_id(tenant_id)
    safe_connector = validate_connector_name(connector)
    project = (project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")).strip()
    return {
        "schema_version": TENANT_CREDENTIAL_SCHEMA_VERSION,
        "tenant_id": safe_tenant,
        "connector": safe_connector,
        "secret_resource": tenant_secret_resource_name(
            safe_tenant, safe_connector, project
        ),
        "service_account": tenant_service_account_email(safe_tenant, project),
        "isolation": "tenant_service_identity",
    }


def tenant_service_account_id(tenant_id: str) -> str:
    """Return a collision-resistant, deterministic per-tenant SA id."""
    safe_tenant = validate_tenant_id(tenant_id)
    digest = hashlib.sha256(safe_tenant.encode("utf-8")).hexdigest()[:7]
    readable = re.sub(r"[^a-z0-9-]", "-", safe_tenant).strip("-") or "tenant"
    return f"driftline-{readable[:12].rstrip('-')}-{digest}"[:30]


def tenant_service_account_email(tenant_id: str, project_id: str | None = None) -> str:
    """Return the deterministic per-tenant service identity email."""
    project = (project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")).strip()
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project):
        raise ValueError("google_project_id_invalid")
    return f"{tenant_service_account_id(tenant_id)}@{project}.iam.gserviceaccount.com"


def tenant_operator_signing_secret_name(tenant_id: str, prefix: str = "driftline-tenant-operator-") -> str:
    """Return the deterministic break-glass signer secret for one tenant.

    The prefix is infrastructure-owned and never accepted from an API request.
    Keeping the tenant suffix deterministic lets an operator provision and
    rotate the secret out of band while the runtime refuses arbitrary secret
    references.
    """
    safe_tenant = validate_tenant_id(tenant_id)
    safe_prefix = prefix.strip()
    if not safe_prefix or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", safe_prefix):
        raise ValueError("tenant_signing_secret_prefix_invalid")
    return f"{safe_prefix}{safe_tenant}"[:100]


def _tenant_is_disabled(tenant_id: str) -> bool:
    """Fail closed for tenants soft-deprovisioned in the control plane."""
    try:
        from .persistence import load_tenant

        tenant = load_tenant(tenant_id)
    except Exception:  # noqa: BLE001 - auth must fail closed.
        # Hosted Firestore is authoritative. If the status check cannot be
        # completed, fail closed rather than trusting a stale local snapshot.
        return (
            os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold()
            == "firestore"
        )
    if (
        os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
        and not tenant
    ):
        # A membership without its tenant control-plane record is not a valid
        # hosted principal. Treat a partial/deleted bootstrap as disabled
        # rather than authorizing against stale membership metadata.
        return True
    return str((tenant or {}).get("status", "active")).casefold() in {
        "disabled",
        "deprovisioned",
    }


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
    discovered: list[dict[str, object]] = []
    durable_persistence = (
        os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    )
    try:
        # Lazy import avoids coupling the pure tenant parser to Firestore
        # during local synthetic runs while allowing durable memberships
        # to survive environment/configuration rollouts.
        from .persistence import (
            list_tenant_memberships_for_email,
            load_tenant_membership,
        )

        if requested_tenant_id:
            persisted_tenant = validate_tenant_id(requested_tenant_id)
            persisted = load_tenant_membership(persisted_tenant, normalized_email)
        else:
            # A multi-tenant identity should not inherit the deployment's demo
            # tenant. Discover only this email's durable memberships and allow
            # implicit selection when there is exactly one active tenant.
            discovered = list_tenant_memberships_for_email(normalized_email)
            active = [
                item
                for item in discovered
                if str(item.get("status", "active")).casefold() == "active"
            ]
            if len(active) == 1:
                persisted = active[0]
            elif len(active) > 1:
                raise PermissionError("tenant_selection_required")
    except PermissionError:
        raise
    except Exception as exc:
        if durable_persistence:
            raise PermissionError("tenant_membership_unavailable") from exc
        persisted = None
    if persisted:
        if str(persisted.get("status", "active")).casefold() != "active":
            raise PermissionError("tenant_membership_inactive")
        tenant_id = validate_tenant_id(str(persisted["tenant_id"]))
        role = str(persisted.get("role", "viewer")).casefold()
    else:
        if durable_persistence:
            raise PermissionError("tenant_membership_required")
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
    if _tenant_is_disabled(tenant_id):
        raise PermissionError("tenant_disabled")
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
    durable_directory = (
        os.getenv("DRIFTLINE_ALLOW_DURABLE_HMAC_TENANTS", "false").casefold()
        == "true"
    )
    configured_tenants: set[str] = set()
    for raw in os.getenv("DRIFTLINE_HMAC_TENANTS", "").split(","):
        if not raw.strip():
            continue
        try:
            configured_tenants.add(validate_tenant_id(raw))
        except ValueError:
            continue
    if not configured_tenants and not durable_directory:
        configured_tenants.add(
            validate_tenant_id(
                os.getenv("DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo")
            )
        )

    # Hosted SaaS deployments can make the durable tenant directory the
    # source of truth instead of redeploying for every new customer. The
    # tenant must already exist and be active; the tenant-specific signer is
    # still verified by the API before this principal is returned. Fail closed
    # if the directory cannot be read so a transient Firestore outage never
    # widens the HMAC allowlist.
    if durable_directory:
        try:
            from .persistence import load_tenant

            persisted = load_tenant(tenant_id)
        except Exception as exc:
            raise PermissionError("tenant_directory_unavailable") from exc
        if str((persisted or {}).get("status", "")).casefold() == "active":
            configured_tenants.add(tenant_id)

    if tenant_id not in configured_tenants:
        raise PermissionError("tenant_not_allowlisted")
    if _tenant_is_disabled(tenant_id):
        raise PermissionError("tenant_disabled")
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
