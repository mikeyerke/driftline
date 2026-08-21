"""Least-privilege Jira handoff adapter.

The adapter is deliberately disabled unless an operator enables it and supplies
an Atlassian credential through the runtime environment. It creates at most
one issue for a Driftline action (marker-based idempotency), scopes writes to a
single configured project, and reverses the handoff by toggling Driftline-owned
labels rather than deleting or rewriting customer work.
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from .credential_broker import CredentialBrokerError, resolve_tenant_credential
from .tenant import (
    tenant_service_account_email,
    validate_connector_name,
    validate_tenant_id,
)


class ConnectorError(RuntimeError):
    """A configured connector could not complete its bounded operation."""


@dataclass(frozen=True)
class SalesforceConfig:
    """Read-only CRM context contract; writes are intentionally out of scope."""

    enabled: bool
    base_url: str = ""
    token: str = ""
    api_version: str = "v61.0"
    client_id: str = ""
    client_secret: str = ""
    login_url: str = "https://login.salesforce.com"
    redirect_uri: str = ""
    scope: str = "api refresh_token"

    @classmethod
    def from_env(cls) -> SalesforceConfig:
        enabled = (
            os.getenv("DRIFTLINE_SALESFORCE_ENABLED", "false").casefold() == "true"
        )
        return cls(
            enabled=enabled,
            base_url=os.getenv("DRIFTLINE_SALESFORCE_BASE_URL", "").rstrip("/"),
            token=_secret_or_env("DRIFTLINE_SALESFORCE_TOKEN") if enabled else "",
            api_version=os.getenv("DRIFTLINE_SALESFORCE_API_VERSION", "v61.0"),
            client_id=_secret_or_env("DRIFTLINE_SALESFORCE_CLIENT_ID") if enabled else "",
            client_secret=_secret_or_env("DRIFTLINE_SALESFORCE_CLIENT_SECRET") if enabled else "",
            login_url=os.getenv(
                "DRIFTLINE_SALESFORCE_LOGIN_URL", "https://login.salesforce.com"
            ).rstrip("/"),
            redirect_uri=os.getenv("DRIFTLINE_SALESFORCE_REDIRECT_URI", "").strip(),
            scope=os.getenv(
                "DRIFTLINE_SALESFORCE_SCOPE", "api refresh_token"
            ).strip(),
        )

    def validate(self) -> None:
        if not self.enabled:
            return
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or not (
            parsed.hostname
            and (
                parsed.hostname.casefold() == "salesforce.com"
                or parsed.hostname.casefold().endswith(".salesforce.com")
                or parsed.hostname.casefold() == "force.com"
                or parsed.hostname.casefold().endswith(".force.com")
            )
        ):
            raise ConnectorError("salesforce_base_url_must_be_salesforce_https")
        _require_https_service_url(self.base_url, "salesforce")
        if not self.token:
            raise ConnectorError("salesforce_read_token_missing")
        if not re.fullmatch(r"v\d+\.\d+", self.api_version):
            raise ConnectorError("salesforce_api_version_invalid")

    def validate_read_client(self) -> None:
        """Validate the tenant OAuth read lane without a global bearer token.

        The explicit OAuth routes obtain an access token per tenant at runtime;
        requiring ``DRIFTLINE_SALESFORCE_TOKEN`` here would incorrectly make a
        connected tenant depend on a deployment-wide credential. The instance
        URL is validated separately by ``SalesforceReadOnlyClient``.
        """
        if not self.enabled:
            raise ConnectorError("salesforce_not_enabled")
        if not re.fullmatch(r"v\d+\.\d+", self.api_version):
            raise ConnectorError("salesforce_api_version_invalid")

    def validate_oauth(self) -> None:
        if not self.enabled:
            raise ConnectorError("salesforce_not_enabled")
        parsed = urlparse(self.login_url)
        if parsed.scheme != "https" or parsed.netloc not in {
            "login.salesforce.com",
            "test.salesforce.com",
        }:
            raise ConnectorError("salesforce_login_url_invalid")
        if not self.client_id or not self.client_secret:
            raise ConnectorError("salesforce_oauth_client_missing")
        if not self.redirect_uri.startswith("https://"):
            raise ConnectorError("salesforce_redirect_uri_invalid")
        if "api" not in self.scope.split():
            raise ConnectorError("salesforce_api_scope_missing")


def salesforce_readiness() -> dict[str, object]:
    """Expose CRM readiness without making a network call or leaking a token."""
    config = SalesforceConfig.from_env()
    if not config.enabled:
        return {
            "status": "not_configured",
            "mode": "prepared_only",
            "external_write": False,
            "scope": "read_only_context",
            "allowed_objects": ["Product2", "PricebookEntry", "Opportunity"],
        }
    oauth_ready = False
    try:
        config.validate_oauth()
        oauth_ready = True
    except ConnectorError:
        pass
    # OAuth configuration is intentionally valid before the first tenant has
    # completed authorization.  The tenant refresh token is stored only after
    # the callback, so a missing read token/base URL must not hide a usable
    # authorization lane from operators.
    if oauth_ready and not config.token:
        return {
            "status": "oauth_ready",
            "mode": "awaiting_authorization",
            "external_write": False,
            "scope": "read_only_context",
            "allowed_objects": ["Product2", "PricebookEntry", "Opportunity"],
        }
    try:
        config.validate()
    except ConnectorError as exc:
        return {
            "status": "invalid_config",
            "mode": "prepared_only",
            "external_write": False,
            "scope": "read_only_context",
            "reason": str(exc),
        }
    if not config.token and not oauth_ready:
        return {
            "status": "oauth_not_configured",
            "mode": "prepared_only",
            "external_write": False,
            "scope": "read_only_context",
            "allowed_objects": ["Product2", "PricebookEntry", "Opportunity"],
            "reason": "Salesforce OAuth client and redirect URI are required",
        }
    return {
        "status": "configured_read_only" if config.token else "oauth_ready",
        "mode": "prepared_only",
        "external_write": False,
        "scope": "read_only_context",
        "api_version": config.api_version,
        "allowed_objects": ["Product2", "PricebookEntry", "Opportunity"],
        "oauth": oauth_ready,
    }


def salesforce_authorization_url(
    config: SalesforceConfig,
    state: str,
    *,
    code_challenge: str | None = None,
) -> str:
    """Build the authorization URL without exposing any secret.

    Salesforce requires PKCE for this external client.  The challenge is
    public by design; the verifier remains in short-lived server-side OAuth
    state and is supplied only during the token exchange.
    """
    config.validate_oauth()
    params = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "scope": config.scope,
        "state": state,
        "prompt": "login consent",
    }
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    return (
        f"{config.login_url}/services/oauth2/authorize?"
        + urlencode(params)
    )


def _salesforce_token_request(
    config: SalesforceConfig,
    payload: dict[str, str],
    *,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    config.validate_oauth()
    body = urlencode(payload).encode()
    request = Request(
        f"{config.login_url}/services/oauth2/token",
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Driftline-Salesforce-Connector/1.0",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=8) as response:
            raw = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ConnectorError("salesforce_oauth_request_failed") from exc
    try:
        result = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise ConnectorError("salesforce_oauth_response_not_json") from exc
    if not result.get("access_token"):
        raise ConnectorError("salesforce_oauth_token_missing")
    return result


def exchange_salesforce_code(
    config: SalesforceConfig,
    code: str,
    *,
    code_verifier: str | None = None,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Exchange a one-time authorization code for tokens."""
    if not code or len(code) > 4096:
        raise ConnectorError("salesforce_oauth_code_invalid")
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "redirect_uri": config.redirect_uri,
    }
    if code_verifier:
        payload["code_verifier"] = code_verifier
    return _salesforce_token_request(
        config,
        payload,
        opener=opener,
    )


def refresh_salesforce_token(
    config: SalesforceConfig,
    refresh_token: str,
    *,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    if not refresh_token:
        raise ConnectorError("salesforce_refresh_token_missing")
    return _salesforce_token_request(
        config,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        },
        opener=opener,
    )


class SalesforceReadOnlyClient:
    """Allowlisted, aggregate-only Salesforce REST client.

    No write method exists by design. Responses intentionally return counts and
    field names rather than CRM records so logs and operator dashboards cannot
    accidentally become a customer-data export.
    """

    _QUERIES: ClassVar[dict[str, str]] = {
        "Product2": "SELECT Id,Name,ProductCode,IsActive,Family FROM Product2 LIMIT 25",
        "PricebookEntry": "SELECT Id,Name,UnitPrice,IsActive,CurrencyIsoCode,Product2Id FROM PricebookEntry LIMIT 25",
        "Opportunity": "SELECT Id,StageName,Amount,CloseDate,IsClosed FROM Opportunity LIMIT 25",
    }

    def __init__(
        self,
        config: SalesforceConfig,
        *,
        access_token: str,
        instance_url: str,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        config.validate_read_client()
        if not access_token:
            raise ConnectorError("salesforce_access_token_missing")
        parsed = urlparse(instance_url.rstrip("/"))
        if parsed.scheme != "https" or not (
            parsed.netloc.endswith(".salesforce.com")
            or parsed.netloc.endswith(".force.com")
        ):
            raise ConnectorError("salesforce_instance_url_invalid")
        self.config = config
        self.access_token = access_token
        self.instance_url = instance_url.rstrip("/")
        self._opener = opener

    def query_summary(self, object_name: str) -> dict[str, Any]:
        query = self._QUERIES.get(object_name)
        if query is None:
            raise ConnectorError("salesforce_object_not_allowlisted")
        url = (
            f"{self.instance_url}/services/data/{self.config.api_version}/query?"
            + urlencode({"q": query})
        )
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": "Driftline-Salesforce-Connector/1.0",
            },
            method="GET",
        )
        try:
            with self._opener(request, timeout=8) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ConnectorError("salesforce_query_failed") from exc
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ConnectorError("salesforce_query_response_not_json") from exc
        if not isinstance(payload, dict) or "totalSize" not in payload:
            raise ConnectorError("salesforce_query_response_invalid")
        return {
            "object": object_name,
            "total": int(payload.get("totalSize", 0)),
            "fields": sorted(
                {
                    key
                    for row in payload.get("records", [])[:25]
                    if isinstance(row, dict)
                    for key in row
                    if key != "attributes"
                }
            ),
        }

    def health_summary(self) -> dict[str, Any]:
        results = [self.query_summary(name) for name in self._QUERIES]
        return {
            "status": "connected_read_only",
            "objects": results,
            "external_write": False,
        }


def _secret_or_env(env_name: str) -> str:
    """Read a credential from an env value or a Secret Manager version.

    Secret references are optional and are resolved only when a connector is
    explicitly enabled.  The value is never included in a returned status or
    error message.
    """
    # Secret Manager values are operator-supplied text; trim transport
    # newlines so a copied token can never become an invalid HTTP header.
    value = os.getenv(env_name, "").strip()
    if value:
        return value
    reference = os.getenv(f"{env_name}_SECRET", "").strip()
    if not reference:
        return ""
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if reference.startswith("projects/"):
        name = reference
    elif project:
        name = f"projects/{project}/secrets/{reference}/versions/latest"
    else:
        raise ConnectorError(f"{env_name.lower()}_secret_project_missing")
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("utf-8").strip()
    except Exception as exc:
        raise ConnectorError(f"{env_name.lower()}_secret_read_failed") from exc


def _tenant_setting(
    tenant_id: str | None,
    connector: str,
    key: str,
    env_name: str,
    default: str = "",
) -> str:
    """Resolve non-secret connector targets from an operator-owned profile.

    DRIFTLINE_TENANT_CONNECTOR_CONFIG is optional JSON shaped as
    {tenant: {connector: {key: value}}}. It carries only bounded target
    metadata, while credentials and request-supplied targets are rejected.
    A durable Firestore profile is preferred for signed tenants. Deployment-
    wide environment values remain only as an explicit compatibility fallback
    for fields that have not yet been provisioned for that tenant.
    """
    fallback = os.getenv(env_name, default)
    if not tenant_id:
        return fallback
    try:
        from .persistence import load_connector_profile

        profile = load_connector_profile(tenant_id, connector)
    except Exception as exc:
        # A signed production connector must not silently cross the tenant
        # boundary when its durable profile cannot be read.
        if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore":
            raise ConnectorError("tenant_connector_profile_lookup_failed") from exc
        profile = None
    if profile and profile.get("status", "active") == "active":
        settings = profile.get("settings") or {}
        if isinstance(settings, dict) and key in settings:
            value = settings.get(key)
            return str(value).strip() if value is not None else fallback
    if (
        os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
        and os.getenv(
            "DRIFTLINE_ALLOW_DEPLOYMENT_CONNECTOR_TARGET_FALLBACK", "false"
        ).casefold()
        != "true"
    ):
        raise ConnectorError("tenant_connector_profile_missing")
    raw = os.getenv("DRIFTLINE_TENANT_CONNECTOR_CONFIG", "").strip()
    if not raw:
        return fallback
    try:
        profiles = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConnectorError("tenant_connector_config_invalid") from exc
    if not isinstance(profiles, dict):
        raise ConnectorError("tenant_connector_config_invalid")
    try:
        safe_tenant = validate_tenant_id(tenant_id)
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise ConnectorError("tenant_connector_config_invalid") from exc
    profile = profiles.get(safe_tenant, {})
    if not isinstance(profile, dict):
        return fallback
    scoped = profile.get(safe_connector, {})
    if not isinstance(scoped, dict):
        return fallback
    value = scoped.get(key)
    return str(value).strip() if value is not None else fallback


def _tenant_secret_or_env(
    tenant_id: str, connector: str, env_name: str, *, operation: str = "read_context"
) -> str:
    """Resolve one tenant-bound secret through the credential broker.

    The broker is the only runtime path that may read a tenant connector
    secret.  Legacy deployment-wide fallback remains an explicit compatibility
    mode for local development, never the hosted SaaS default.
    """
    safe_tenant = validate_tenant_id(tenant_id)
    safe_connector = validate_connector_name(connector)

    def read_scoped_secret(secret_name: str, *, version: str = "latest") -> str:
        credentials = tenant_secret_credentials(safe_tenant)
        try:
            return read_secret(
                secret_name, version=version, credentials=credentials
            )
        except TypeError:
            try:
                return read_secret(secret_name, version=version)
            except TypeError:
                return read_secret(secret_name)

    try:
        lease = resolve_tenant_credential(
            safe_tenant,
            safe_connector,
            operation=operation,
            secret_reader=read_scoped_secret,
        )
        return lease.value
    except CredentialBrokerError as exc:
        if os.getenv(
            "DRIFTLINE_ALLOW_LEGACY_GLOBAL_CONNECTOR_SECRETS", "false"
        ).casefold() == "true":
            return _secret_or_env(env_name)
        # Keep provider adapters' stable error vocabulary while hiding the
        # broker's internal metadata and Secret Manager details.
        if str(exc) in {"credential_binding_unavailable", "tenant_not_active"}:
            raise ConnectorError(f"{safe_connector}_tenant_binding_missing") from exc
        raise ConnectorError(
            f"{safe_connector}_tenant_credential_unavailable"
        ) from exc


def _workflow_tenant_id(state: Any) -> str:
    action = state.action_record or {}
    approval = state.approval or {}
    identity = approval.get("approval_identity") or {}
    tenant_id = action.get("tenant_id") or identity.get("tenant_id")
    if not tenant_id:
        raise ConnectorError("connector_tenant_identity_missing")
    return validate_tenant_id(str(tenant_id))


def _validate_secret_version(version: str) -> str:
    normalized = str(version).strip()
    if normalized != "latest" and not re.fullmatch(r"[1-9][0-9]*", normalized):
        raise ConnectorError("secret_version_invalid")
    return normalized


def tenant_secret_credentials(tenant_id: str):
    """Return credentials for the tenant's isolated Secret Manager identity.

    Hosted SaaS enables impersonation so the shared Cloud Run identity can
    never directly read another tenant's secret. Local development keeps the
    default credentials path unless explicitly enabled.
    """
    mode = os.getenv("DRIFTLINE_TENANT_SECRET_IDENTITY_MODE", "direct").casefold()
    if mode != "impersonated":
        return None
    safe_tenant = validate_tenant_id(tenant_id)
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    try:
        from google.auth import default, impersonated_credentials

        source_credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        target = tenant_service_account_email(safe_tenant, project)
        return impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=target,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            lifetime=600,
        )
    except Exception as exc:
        raise ConnectorError("tenant_secret_identity_unavailable") from exc


def read_secret(
    secret_name: str, *, version: str = "latest", credentials: object | None = None
) -> str:
    """Read one explicitly named isolated Secret Manager secret."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    safe_version = _validate_secret_version(version)
    if not project or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,99}", secret_name):
        raise ConnectorError("secret_reference_invalid")
    try:
        from google.cloud import secretmanager

        kwargs = {"credentials": credentials} if credentials is not None else {}
        client = secretmanager.SecretManagerServiceClient(**kwargs)
        response = client.access_secret_version(
            name=f"projects/{project}/secrets/{secret_name}/versions/{safe_version}"
        )
        return response.payload.data.decode("utf-8")
    except Exception as exc:
        raise ConnectorError("secret_read_failed") from exc


def secret_version_for(secret_name: str, *, credentials: object | None = None) -> str:
    """Return the concrete enabled version behind ``latest`` when available.

    Secret Manager responses include the resolved version name, but local
    contract tests and emulators may omit it.  Falling back to ``latest`` is
    safe for those compatibility paths; hosted activation records a concrete
    version whenever the provider returns one.
    """
    _, version = read_secret_with_version(secret_name, credentials=credentials)
    return version or "latest"


def read_secret_with_version(
    secret_name: str, *, credentials: object | None = None
) -> tuple[str, str]:
    """Read an isolated secret and return ``(value, resolved_version)``."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,99}", secret_name):
        raise ConnectorError("secret_reference_invalid")
    try:
        from google.cloud import secretmanager

        kwargs = {"credentials": credentials} if credentials is not None else {}
        client = secretmanager.SecretManagerServiceClient(**kwargs)
        response = client.access_secret_version(
            name=f"projects/{project}/secrets/{secret_name}/versions/latest"
        )
        resolved_name = str(getattr(response, "name", "") or "")
        version = resolved_name.rsplit("/", 1)[-1]
        if not re.fullmatch(r"[1-9][0-9]*", version):
            version = ""
        return response.payload.data.decode("utf-8"), version
    except Exception as exc:
        raise ConnectorError("secret_read_failed") from exc


def write_secret_version(
    secret_name: str, value: str, *, credentials: object | None = None
) -> str | None:
    """Add a version to a pre-provisioned isolated secret.

    Secret creation is intentionally not attempted at request time. An
    operator provisions the empty tenant secret once with infrastructure IAM;
    the runtime only needs ``secretVersionAdder`` on that exact secret.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,99}", secret_name):
        raise ConnectorError("secret_reference_invalid")
    try:
        from google.cloud import secretmanager

        kwargs = {"credentials": credentials} if credentials is not None else {}
        client = secretmanager.SecretManagerServiceClient(**kwargs)
        response = client.add_secret_version(
            parent=f"projects/{project}/secrets/{secret_name}",
            payload={"data": value.encode("utf-8")},
        )
        name = str(getattr(response, "name", "") or "")
        version = name.rsplit("/", 1)[-1]
        return version if re.fullmatch(r"[1-9][0-9]*", version) else None
    except Exception as exc:
        raise ConnectorError("secret_write_failed") from exc


def _require_https_service_url(value: str, marker: str) -> str:
    url = value.rstrip("/") + "/"
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ConnectorError(f"{marker}_base_url_must_be_https")
    return url


def _require_allowlisted_service_url(
    value: str, marker: str, allowed_hosts: tuple[str, ...]
) -> str:
    url = _require_https_service_url(value, marker)
    host = (urlparse(url).hostname or "").casefold().rstrip(".")
    if not any(host == suffix or host.endswith(f".{suffix}") for suffix in allowed_hosts):
        raise ConnectorError(f"{marker}_base_url_host_not_allowlisted")
    return url


@dataclass(frozen=True)
class JiraConfig:
    enabled: bool
    base_url: str = ""
    email: str = ""
    token: str = ""
    project_key: str = ""
    issue_type: str = "Task"

    @classmethod
    def from_env(
        cls, tenant_id: str | None = None, *, operation: str = "read_context"
    ) -> JiraConfig:
        enabled = os.getenv("DRIFTLINE_JIRA_ENABLED", "false").casefold() == "true"
        return cls(
            enabled=enabled,
            base_url=_tenant_setting(
                tenant_id, "jira", "base_url", "DRIFTLINE_JIRA_BASE_URL"
            ).rstrip("/")
            + "/",
            email=_tenant_setting(tenant_id, "jira", "email", "DRIFTLINE_JIRA_EMAIL"),
            token=(
                _tenant_secret_or_env(tenant_id, "jira", "DRIFTLINE_JIRA_TOKEN", operation=operation)
                if enabled and tenant_id
                else _secret_or_env("DRIFTLINE_JIRA_TOKEN") if enabled else ""
            ),
            project_key=_tenant_setting(
                tenant_id, "jira", "project_key", "DRIFTLINE_JIRA_PROJECT_KEY"
            ),
            issue_type=_tenant_setting(
                tenant_id, "jira", "issue_type", "DRIFTLINE_JIRA_ISSUE_TYPE", "Task"
            ),
        )

    def validate(self) -> None:
        if not self.enabled:
            return
        parsed = urlparse(self.base_url)
        is_site_url = bool(
            parsed.hostname
            and (
                parsed.hostname.casefold() == "atlassian.net"
                or parsed.hostname.casefold().endswith(".atlassian.net")
            )
        )
        is_scoped_gateway = (
            parsed.hostname == "api.atlassian.com"
            and parsed.path.startswith("/ex/jira/")
        )
        if parsed.scheme != "https" or not (is_site_url or is_scoped_gateway):
            raise ConnectorError("jira_base_url_must_be_atlassian_https")
        _require_https_service_url(self.base_url, "jira")
        if not self.email or not self.token or not self.project_key:
            raise ConnectorError("jira_credentials_or_project_missing")


def _adf(text: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text[:32000]}],
            }
        ],
    }


class JiraConnector:
    """Small Jira v3 client with injectable transport for contract tests."""

    def __init__(
        self,
        config: JiraConfig,
        *,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        config.validate()
        self.config = config
        self._opener = opener
        credentials = f"{config.email}:{config.token}".encode()
        self._authorization = "Basic " + base64.b64encode(credentials).decode()

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = urljoin(self.config.base_url, path.lstrip("/"))
        if query:
            url = f"{url}?{urlencode(query)}"
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            url,
            data=body,
            headers={
                "Accept": "application/json",
                "Authorization": self._authorization,
                "Content-Type": "application/json",
                "User-Agent": "Driftline-Jira-Connector/1.0",
            },
            method=method,
        )
        try:
            with self._opener(request, timeout=8) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ConnectorError(f"jira_request_failed:{method}:{path}") from exc
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ConnectorError("jira_response_not_json") from exc

    def create_or_reuse_issue(
        self,
        *,
        workflow_id: str,
        action_id: str,
        source_name: str,
        evidence_hash: str,
        artifact: str,
        owner: str,
        proposed: str,
    ) -> dict[str, Any]:
        marker = f"Driftline action {action_id}"
        search = self._request(
            "POST",
            # Jira Cloud removed the legacy /search operation; /search/jql is
            # the current v3 endpoint and keeps the marker lookup bounded.
            "/rest/api/3/search/jql",
            {
                "jql": f'project = "{self.config.project_key}" AND text ~ "{marker}"',
                "maxResults": 1,
                "fields": ["key", "summary", "labels"],
            },
        )
        existing = (search.get("issues") or [None])[0]
        if existing:
            labels = {
                str(label).strip()
                for label in (existing.get("fields") or {}).get("labels", [])
            }
            if "driftline-reversed" in labels:
                # A prior human-approved action may have been undone. Reusing
                # that marker is still idempotent, but the new approval must
                # make the external state active again or Driftline would
                # report a successful write that Jira did not reflect.
                self._request(
                    "PUT",
                    f"/rest/api/3/issue/{quote(str(existing.get('key')), safe='')}",
                    {
                        "update": {
                            "labels": [
                                {"remove": "driftline-reversed"},
                                {"add": "driftline-active"},
                            ]
                        }
                    },
                )
                return {
                    "status": "reactivated",
                    "issue_key": existing.get("key"),
                    "issue_url": existing.get("self"),
                    "idempotent": True,
                }
            return {
                "status": "reused",
                "issue_key": existing.get("key"),
                "issue_url": existing.get("self"),
                "idempotent": True,
            }

        description = (
            f"{marker}\n"
            f"Workflow: {workflow_id}\n"
            f"Source: {source_name}\n"
            f"Evidence hash: {evidence_hash}\n"
            f"Owner: {owner}\n\n"
            f"Proposed output:\n{proposed}\n\n"
            "This issue was created by an approval-gated Driftline connector. "
            "It does not change customer-facing systems automatically."
        )
        created = self._request(
            "POST",
            "/rest/api/3/issue",
            {
                "fields": {
                    "project": {"key": self.config.project_key},
                    "summary": f"[Driftline] {artifact} · {source_name}",
                    "issuetype": {"name": self.config.issue_type},
                    "description": _adf(description),
                    "labels": ["driftline-active", "driftline-approval-gated"],
                }
            },
        )
        return {
            "status": "created",
            "issue_key": created.get("key"),
            "issue_id": created.get("id"),
            "issue_url": created.get("self"),
            "idempotent": False,
        }

    def reverse_issue(self, issue_key: str, action_id: str) -> dict[str, Any]:
        self._request(
            "PUT",
            f"/rest/api/3/issue/{quote(issue_key, safe='')}",
            {
                "update": {
                    "labels": [
                        {"remove": "driftline-active"},
                        {"add": "driftline-reversed"},
                    ]
                }
            },
        )
        self._request(
            "POST",
            f"/rest/api/3/issue/{quote(issue_key, safe='')}/comment",
            {"body": _adf(f"Driftline action {action_id} was reversed by a named human reviewer.")},
        )
        return {"status": "reversed", "issue_key": issue_key}

    def read_context_summary(self) -> dict[str, Any]:
        """Return bounded, aggregate Jira context without issue text.

        This is intentionally a separate read lane from the approval-gated
        handoff.  The query is fixed to the configured project and only asks
        Jira for status/priority metadata; no user-supplied JQL or issue IDs
        are accepted.
        """
        result = self._request(
            "POST",
            "/rest/api/3/search/jql",
            {
                "jql": f'project = "{self.config.project_key}" AND statusCategory != Done',
                "maxResults": 50,
                "fields": ["status", "priority", "updated"],
            },
        )
        issues = result.get("issues") or []
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        for issue in issues:
            fields = issue.get("fields") or {}
            status = str((fields.get("status") or {}).get("name") or "unknown")
            priority = str((fields.get("priority") or {}).get("name") or "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
        return {
            "status": "ok",
            "scope": f"project:{self.config.project_key}",
            "open_issue_count": int(result.get("total", len(issues)) or 0),
            "sampled_issue_count": len(issues),
            "by_status": by_status,
            "by_priority": by_priority,
            "redaction": "aggregate_metadata_only",
        }


def execute_jira_handoff(state: Any) -> dict[str, Any]:
    """Create one Jira task for the first approved packet, if explicitly enabled."""

    config = JiraConfig.from_env()
    if not config.enabled:
        return {"jira_status": "not_configured", "external_write": False}
    config = JiraConfig.from_env(_workflow_tenant_id(state), operation="create_issue")
    packet = next(
        (item for item in state.artifact_packets if item.get("status") == "packet_ready"),
        None,
    )
    if packet is None:
        return {"jira_status": "not_eligible", "external_write": False}
    connector = JiraConnector(config)
    evidence = state.evidence
    result = connector.create_or_reuse_issue(
        workflow_id=state.workflow_id,
        action_id=str((state.action_record or {}).get("action_id", "unknown")),
        source_name=evidence.source_name if evidence else "Unknown",
        evidence_hash=evidence.evidence_hash if evidence else "none",
        artifact=str(packet["artifact"]),
        owner=str(packet["owner"]),
        proposed=str(packet["content"]),
    )
    return {
        "jira_status": result["status"],
        "jira_issue_key": result.get("issue_key"),
        "jira_issue_url": result.get("issue_url"),
        "jira_idempotent": result.get("idempotent", False),
        "external_write": True,
    }


def reverse_jira_handoff(state: Any) -> dict[str, Any]:
    """Remove the active marker and append a reversal comment, never delete work."""

    action = state.action_record or {}
    issue_key = action.get("jira_issue_key")
    config = JiraConfig.from_env()
    if not issue_key or not config.enabled:
        return {"jira_status": "not_configured", "external_write": False}
    config = JiraConfig.from_env(_workflow_tenant_id(state), operation="reverse_issue")
    connector = JiraConnector(config)
    result = connector.reverse_issue(
        str(issue_key), str(action.get("action_id", "unknown"))
    )
    return {
        "jira_status": result["status"],
        "jira_issue_key": issue_key,
        "external_write": True,
    }


@dataclass(frozen=True)
class ConfluenceConfig:
    enabled: bool
    base_url: str = ""
    email: str = ""
    token: str = ""
    space_key: str = ""
    parent_page_id: str = ""

    @classmethod
    def from_env(
        cls, tenant_id: str | None = None, *, operation: str = "read_context"
    ) -> ConfluenceConfig:
        enabled = os.getenv("DRIFTLINE_CONFLUENCE_ENABLED", "false").casefold() == "true"
        return cls(
            enabled=enabled,
            base_url=_tenant_setting(
                tenant_id,
                "confluence",
                "base_url",
                "DRIFTLINE_CONFLUENCE_BASE_URL",
            ).rstrip("/")
            + "/",
            email=_tenant_setting(
                tenant_id, "confluence", "email", "DRIFTLINE_CONFLUENCE_EMAIL"
            ),
            token=(
                _tenant_secret_or_env(
                    tenant_id, "confluence", "DRIFTLINE_CONFLUENCE_TOKEN", operation=operation
                )
                if enabled and tenant_id
                else _secret_or_env("DRIFTLINE_CONFLUENCE_TOKEN") if enabled else ""
            ),
            space_key=_tenant_setting(
                tenant_id,
                "confluence",
                "space_key",
                "DRIFTLINE_CONFLUENCE_SPACE_KEY",
            ),
            parent_page_id=_tenant_setting(
                tenant_id,
                "confluence",
                "parent_page_id",
                "DRIFTLINE_CONFLUENCE_PARENT_PAGE_ID",
            ),
        )

    def validate(self) -> None:
        if not self.enabled:
            return
        parsed = urlparse(self.base_url)
        is_site_url = bool(
            parsed.hostname
            and (
                parsed.hostname.casefold() == "atlassian.net"
                or parsed.hostname.casefold().endswith(".atlassian.net")
            )
        )
        is_scoped_gateway = (
            parsed.hostname == "api.atlassian.com"
            and parsed.path.startswith("/ex/confluence/")
        )
        if not (is_site_url or is_scoped_gateway):
            raise ConnectorError("confluence_base_url_must_be_atlassian")
        _require_https_service_url(self.base_url, "confluence")
        if not self.email or not self.token or not self.space_key:
            raise ConnectorError("confluence_credentials_or_space_missing")


class ConfluenceConnector:
    """Scoped Confluence page handoff with marker-based idempotency."""

    def __init__(self, config: ConfluenceConfig, *, opener: Callable[..., Any] = urlopen):
        config.validate()
        self.config = config
        self._opener = opener
        credentials = f"{config.email}:{config.token}".encode()
        self._authorization = "Basic " + base64.b64encode(credentials).decode()

    def _api_path(self, path: str) -> str:
        """Prefix Confluence Cloud REST paths when using Atlassian's API gateway."""
        normalized = path.lstrip("/")
        if self.config.base_url.startswith("https://api.atlassian.com/ex/confluence/"):
            return f"wiki/{normalized}"
        return normalized

    @property
    def _uses_v2_gateway(self) -> bool:
        return self.config.base_url.startswith("https://api.atlassian.com/ex/confluence/")

    @staticmethod
    def _page_url(result: dict[str, Any]) -> str | None:
        links = result.get("_links") or {}
        webui = links.get("webui")
        if not webui:
            return None
        if webui.startswith("http"):
            return webui
        base = links.get("base", "").rstrip("/")
        return f"{base}/{webui.lstrip('/')}" if base else webui

    def _space_id(self) -> str:
        spaces = self._request(
            "GET",
            "/api/v2/spaces",
            query={"keys": self.config.space_key, "limit": "1"},
        )
        space = (spaces.get("results") or [None])[0]
        if not space or not space.get("id"):
            raise ConnectorError("confluence_space_not_found")
        return str(space["id"])

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = urljoin(self.config.base_url, self._api_path(path))
        if query:
            url = f"{url}?{urlencode(query)}"
        request = Request(
            url,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Accept": "application/json",
                "Authorization": self._authorization,
                "Content-Type": "application/json",
                "User-Agent": "Driftline-Confluence-Connector/1.0",
            },
            method=method,
        )
        try:
            with self._opener(request, timeout=8) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ConnectorError(f"confluence_request_failed:{method}:{path}") from exc
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ConnectorError("confluence_response_not_json") from exc

    def create_or_reuse_page(
        self,
        *,
        action_id: str,
        workflow_id: str,
        source_name: str,
        evidence_hash: str,
        artifact: str,
        owner: str,
        proposed: str,
    ) -> dict[str, Any]:
        marker = f"Driftline action {action_id}"
        title = f"[Driftline] {artifact} - {source_name}"
        if self._uses_v2_gateway:
            space_id = self._space_id()
            result = self._request(
                "GET",
                "/api/v2/pages",
                query={"space-id": space_id, "title": title, "limit": "1"},
            )
        else:
            result = self._request(
                "GET",
                "/rest/api/content",
                query={"spaceKey": self.config.space_key, "title": title, "limit": "1"},
            )
        existing = (result.get("results") or [None])[0]
        if existing:
            page_id = str(existing.get("id"))
            if self._page_was_reversed(page_id):
                self._reactivate_page(page_id, action_id)
                return {
                    "status": "reactivated",
                    "page_id": existing.get("id"),
                    "page_url": self._page_url(existing),
                    "idempotent": True,
                }
            return {
                "status": "reused",
                "page_id": existing.get("id"),
                "page_url": self._page_url(existing),
                "idempotent": True,
            }
        body = (
            f"<h1>{artifact}</h1><p>{marker}</p>"
            f"<p>Workflow: {workflow_id}<br/>Source: {source_name}<br/>"
            f"Evidence hash: {evidence_hash}<br/>Owner: {owner}</p>"
            f"<h2>Proposed update</h2><p>{html.escape(proposed)}</p>"
        )
        if self._uses_v2_gateway:
            payload = {
                "spaceId": space_id,
                "status": "current",
                "title": title,
                "body": {"representation": "storage", "value": body},
            }
            if self.config.parent_page_id:
                payload["parentId"] = self.config.parent_page_id
            created = self._request("POST", "/api/v2/pages", payload)
        else:
            payload = {
                "type": "page",
                "title": title,
                "space": {"key": self.config.space_key},
                "body": {"storage": {"value": body, "representation": "storage"}},
                "metadata": {"labels": {"results": [{"name": "driftline-active"}]}},
            }
            if self.config.parent_page_id:
                payload["ancestors"] = [{"id": self.config.parent_page_id}]
            created = self._request("POST", "/rest/api/content", payload)
        return {
            "status": "created",
            "page_id": created.get("id"),
            "page_url": self._page_url(created),
            "idempotent": False,
        }

    def _page_was_reversed(self, page_id: str) -> bool:
        """Detect only Driftline's own reversal marker before reusing a page."""
        if self._uses_v2_gateway:
            current = self._request(
                "GET",
                f"/api/v2/pages/{quote(page_id, safe='')}",
                query={"body-format": "storage"},
            )
            value = str(((current.get("body") or {}).get("storage") or {}).get("value", ""))
            return "was reversed by a named human reviewer" in value
        current = self._request(
            "GET",
            f"/rest/api/content/{quote(page_id, safe='')}",
            query={"expand": "metadata.labels"},
        )
        labels = {
            str(item.get("name"))
            for item in (((current.get("metadata") or {}).get("labels") or {}).get("results") or [])
            if isinstance(item, dict)
        }
        return "driftline-reversed" in labels

    def _reactivate_page(self, page_id: str, action_id: str) -> None:
        """Append a reactivation audit marker without overwriting page history."""
        if self._uses_v2_gateway:
            current = self._request(
                "GET",
                f"/api/v2/pages/{quote(page_id, safe='')}",
                query={"body-format": "storage"},
            )
            version = current.get("version", {}).get("number")
            if not isinstance(version, int):
                raise ConnectorError("confluence_page_version_missing")
            storage = (current.get("body") or {}).get("storage") or {}
            value = storage.get("value", "")
            value += (
                f"<p>Driftline action {html.escape(action_id)} was reactivated by "
                "a named human reviewer.</p>"
            )
            self._request(
                "PUT",
                f"/api/v2/pages/{quote(page_id, safe='')}",
                {
                    "id": page_id,
                    "status": current.get("status", "current"),
                    "title": current.get("title", "Driftline page"),
                    "body": {"representation": "storage", "value": value},
                    "version": {"number": version + 1, "message": "Driftline reactivation"},
                },
            )
            return
        self._request(
            "DELETE",
            f"/rest/api/content/{quote(page_id, safe='')}/label/global/driftline-reversed",
        )
        self._request(
            "POST",
            f"/rest/api/content/{quote(page_id, safe='')}/label",
            {"prefix": "global", "name": "driftline-active"},
        )

    def reverse_page(self, page_id: str, action_id: str) -> dict[str, Any]:
        if self._uses_v2_gateway:
            current = self._request(
                "GET",
                f"/api/v2/pages/{quote(page_id, safe='')}",
                query={"body-format": "storage"},
            )
            version = current.get("version", {}).get("number")
            if not isinstance(version, int):
                raise ConnectorError("confluence_page_version_missing")
            storage = (current.get("body") or {}).get("storage") or {}
            value = storage.get("value", "")
            value += (
                f"<p>Driftline action {html.escape(action_id)} was reversed by "
                "a named human reviewer.</p>"
            )
            self._request(
                "PUT",
                f"/api/v2/pages/{quote(page_id, safe='')}",
                {
                    "id": page_id,
                    "status": current.get("status", "current"),
                    "title": current.get("title", "Driftline page"),
                    "body": {"representation": "storage", "value": value},
                    "version": {"number": version + 1, "message": "Driftline reversal"},
                },
            )
        else:
            self._request(
                "POST",
                f"/rest/api/content/{quote(page_id, safe='')}/label",
                {"prefix": "global", "name": "driftline-reversed"},
            )
        return {"status": "reversed", "page_id": page_id, "action_id": action_id}

    def read_context_summary(self) -> dict[str, Any]:
        """Return bounded space/page counts without page bodies or titles."""
        space_id = self._space_id()
        if self._uses_v2_gateway:
            result = self._request(
                "GET",
                "/api/v2/pages",
                query={"space-id": space_id, "limit": "50", "sort": "-modified-date"},
            )
        else:
            result = self._request(
                "GET",
                "/rest/api/content",
                query={"spaceKey": self.config.space_key, "limit": "50", "expand": "version"},
            )
        pages = result.get("results") or []
        return {
            "status": "ok",
            "scope": f"space:{self.config.space_key}",
            "page_count": int(result.get("totalSize", len(pages)) or 0),
            "sampled_page_count": len(pages),
            "has_more": bool(result.get("_links", {}).get("next") or result.get("next")),
            "redaction": "aggregate_metadata_only",
        }


def execute_confluence_handoff(state: Any) -> dict[str, Any]:
    config = ConfluenceConfig.from_env()
    if not config.enabled:
        return {
            "confluence_status": "not_configured",
            "confluence_prepared_only": True,
            "external_write": False,
        }
    config = ConfluenceConfig.from_env(_workflow_tenant_id(state), operation="create_page")
    packet = next(
        (item for item in state.artifact_packets if item.get("status") == "packet_ready"),
        None,
    )
    if packet is None:
        return {"confluence_status": "not_eligible", "external_write": False}
    evidence = state.evidence
    result = ConfluenceConnector(config).create_or_reuse_page(
        action_id=str((state.action_record or {}).get("action_id", "unknown")),
        workflow_id=state.workflow_id,
        source_name=evidence.source_name if evidence else "Unknown",
        evidence_hash=evidence.evidence_hash if evidence else "none",
        artifact=str(packet["artifact"]),
        owner=str(packet["owner"]),
        proposed=str(packet["content"]),
    )
    return {
        "confluence_status": result["status"],
        "confluence_page_id": result.get("page_id"),
        "confluence_page_url": result.get("page_url"),
        "confluence_idempotent": result.get("idempotent", False),
        "external_write": True,
    }


def reverse_confluence_handoff(state: Any) -> dict[str, Any]:
    action = state.action_record or {}
    page_id = action.get("confluence_page_id")
    config = ConfluenceConfig.from_env()
    if not page_id or not config.enabled:
        return {
            "confluence_status": "not_configured",
            "confluence_prepared_only": True,
            "external_write": False,
        }
    config = ConfluenceConfig.from_env(_workflow_tenant_id(state), operation="reverse_page")
    result = ConfluenceConnector(config).reverse_page(
        str(page_id), str(action.get("action_id", "unknown"))
    )
    return {"confluence_status": result["status"], "confluence_page_id": page_id, "external_write": True}


@dataclass(frozen=True)
class SlackConfig:
    enabled: bool
    token: str = ""
    channel_id: str = ""
    base_url: str = "https://slack.com/api/"

    @classmethod
    def from_env(
        cls, tenant_id: str | None = None, *, operation: str = "read_context"
    ) -> SlackConfig:
        enabled = os.getenv("DRIFTLINE_SLACK_ENABLED", "false").casefold() == "true"
        return cls(
            enabled=enabled,
            token=(
                _tenant_secret_or_env(tenant_id, "slack", "DRIFTLINE_SLACK_TOKEN", operation=operation)
                if enabled and tenant_id
                else _secret_or_env("DRIFTLINE_SLACK_TOKEN") if enabled else ""
            ),
            channel_id=_tenant_setting(
                tenant_id, "slack", "channel_id", "DRIFTLINE_SLACK_CHANNEL_ID"
            ),
            base_url=_tenant_setting(
                tenant_id,
                "slack",
                "base_url",
                "DRIFTLINE_SLACK_BASE_URL",
                "https://slack.com/api/",
            ).rstrip("/")
            + "/",
        )

    def validate(self) -> None:
        if not self.enabled:
            return
        _require_allowlisted_service_url(self.base_url, "slack", ("slack.com",))
        if not self.token or not self.channel_id:
            raise ConnectorError("slack_token_or_channel_missing")


class SlackConnector:
    """Scoped Slack bot handoff; no arbitrary channel or webhook input."""

    def __init__(self, config: SlackConfig, *, opener: Callable[..., Any] = urlopen):
        config.validate()
        self.config = config
        self._opener = opener

    def _request(self, method: str, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            urljoin(self.config.base_url, endpoint),
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "Driftline-Slack-Connector/1.0",
            },
            method=method,
        )
        try:
            with self._opener(request, timeout=8) as response:
                raw = response.read().decode("utf-8")
            result = json.loads(raw) if raw else {}
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ConnectorError(f"slack_request_failed:{endpoint}") from exc
        if not result.get("ok", False):
            raise ConnectorError(f"slack_api_error:{result.get('error', 'unknown')}")
        return result

    def create_or_reuse_message(
        self, *, action_id: str, workflow_id: str, artifact: str, owner: str, proposed: str
    ) -> dict[str, Any]:
        marker = f"Driftline action {action_id}"
        history = self._request(
            "POST", "conversations.history", {"channel": self.config.channel_id, "limit": 100}
        )
        existing = next(
            (message for message in history.get("messages", []) if marker in message.get("text", "")),
            None,
        )
        if existing:
            reversed_marker = f"{marker} was reversed by a named human reviewer."
            if any(reversed_marker in message.get("text", "") for message in history.get("messages", [])):
                result = self._request(
                    "POST",
                    "chat.postMessage",
                    {
                        "channel": self.config.channel_id,
                        "text": f"{marker} was reactivated by a named human reviewer.",
                        "client_msg_id": f"{action_id}:reactivate",
                    },
                )
                return {
                    "status": "reactivated",
                    "message_ts": result.get("ts"),
                    "idempotent": True,
                }
            return {"status": "reused", "message_ts": existing.get("ts"), "idempotent": True}
        result = self._request(
            "POST",
            "chat.postMessage",
            {
                "channel": self.config.channel_id,
                "text": f"{marker}\nWorkflow: {workflow_id}\nOwner: {owner}\n*{artifact}*\n{proposed}",
                "client_msg_id": action_id,
            },
        )
        return {"status": "created", "message_ts": result.get("ts"), "idempotent": False}

    def reverse_message(self, action_id: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "chat.postMessage",
            {
                "channel": self.config.channel_id,
                "text": f"Driftline action {action_id} was reversed by a named human reviewer.",
                "client_msg_id": f"{action_id}:reverse",
            },
        )
        return {"status": "reversed", "message_ts": result.get("ts")}

    def read_context_summary(self) -> dict[str, Any]:
        """Return recent message volume for the fixed channel, never message text."""
        history = self._request(
            "POST", "conversations.history", {"channel": self.config.channel_id, "limit": 100}
        )
        messages = history.get("messages") or []
        return {
            "status": "ok",
            "scope": f"channel:{self.config.channel_id}",
            "recent_message_count": len(messages),
            "has_more": bool(history.get("has_more")),
            "latest_message_ts": messages[0].get("ts") if messages else None,
            "redaction": "aggregate_metadata_only",
        }


def execute_slack_handoff(state: Any) -> dict[str, Any]:
    config = SlackConfig.from_env()
    if not config.enabled:
        return {"slack_status": "not_configured", "slack_prepared_only": True, "external_write": False}
    config = SlackConfig.from_env(_workflow_tenant_id(state), operation="post_message")
    packet = next(
        (item for item in state.artifact_packets if item.get("status") == "packet_ready"),
        None,
    )
    if packet is None:
        return {"slack_status": "not_eligible", "external_write": False}
    result = SlackConnector(config).create_or_reuse_message(
        action_id=str((state.action_record or {}).get("action_id", "unknown")),
        workflow_id=state.workflow_id,
        artifact=str(packet["artifact"]),
        owner=str(packet["owner"]),
        proposed=str(packet["content"]),
    )
    return {
        "slack_status": result["status"],
        "slack_message_ts": result.get("message_ts"),
        "slack_idempotent": result.get("idempotent", False),
        "external_write": True,
    }


def reverse_slack_handoff(state: Any) -> dict[str, Any]:
    config = SlackConfig.from_env()
    action_id = str((state.action_record or {}).get("action_id", "unknown"))
    if not config.enabled:
        return {"slack_status": "not_configured", "slack_prepared_only": True, "external_write": False}
    config = SlackConfig.from_env(_workflow_tenant_id(state), operation="reverse_message")
    result = SlackConnector(config).reverse_message(action_id)
    return {"slack_status": result["status"], "slack_message_ts": result.get("message_ts"), "external_write": True}


@dataclass(frozen=True)
class GitHubConfig:
    enabled: bool
    token: str = ""
    owner: str = ""
    repo: str = ""
    api_url: str = "https://api.github.com/"

    @classmethod
    def from_env(
        cls, tenant_id: str | None = None, *, operation: str = "read_context"
    ) -> GitHubConfig:
        enabled = os.getenv("DRIFTLINE_GITHUB_ENABLED", "false").casefold() == "true"
        return cls(
            enabled=enabled,
            token=(
                _tenant_secret_or_env(tenant_id, "github", "DRIFTLINE_GITHUB_TOKEN", operation=operation)
                if enabled and tenant_id
                else _secret_or_env("DRIFTLINE_GITHUB_TOKEN") if enabled else ""
            ),
            owner=_tenant_setting(tenant_id, "github", "owner", "DRIFTLINE_GITHUB_OWNER"),
            repo=_tenant_setting(tenant_id, "github", "repo", "DRIFTLINE_GITHUB_REPO"),
            api_url=_tenant_setting(
                tenant_id,
                "github",
                "api_url",
                "DRIFTLINE_GITHUB_API_URL",
                "https://api.github.com/",
            ),
        )

    def validate(self) -> None:
        if not self.enabled:
            return
        _require_allowlisted_service_url(self.api_url, "github", ("github.com",))
        if not self.token or not re.fullmatch(r"[A-Za-z0-9_.-]+", self.owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", self.repo):
            raise ConnectorError("github_token_or_repository_missing")


class GitHubConnector:
    """Repository-scoped GitHub issue handoff with marker idempotency."""

    def __init__(self, config: GitHubConfig, *, opener: Callable[..., Any] = urlopen):
        config.validate()
        self.config = config
        self._opener = opener

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        request = Request(
            urljoin(self.config.api_url, path.lstrip("/")),
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.config.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "Driftline-GitHub-Connector/1.0",
            },
            method=method,
        )
        try:
            with self._opener(request, timeout=8) as response:
                raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ConnectorError(f"github_request_failed:{method}:{path}") from exc

    @staticmethod
    def _preserved_labels(issue: dict[str, Any], replacement: str) -> list[str]:
        """Keep customer labels while replacing only Driftline-owned state."""
        owned = {"driftline-active", "driftline-approval-gated", "driftline-reversed"}
        labels = [
            str(label.get("name"))
            for label in issue.get("labels") or []
            if isinstance(label, dict) and label.get("name")
        ]
        preserved = [label for label in labels if label not in owned]
        return [*preserved, replacement]

    def create_or_reuse_issue(
        self, *, action_id: str, workflow_id: str, artifact: str, owner: str, proposed: str, evidence_hash: str
    ) -> dict[str, Any]:
        marker = f"Driftline action {action_id}"
        base = f"/repos/{quote(self.config.owner)}/{quote(self.config.repo)}"
        issues = self._request("GET", f"{base}/issues?state=all&per_page=100")
        existing = next(
            (issue for issue in issues if marker in f"{issue.get('title', '')}\n{issue.get('body', '')}"),
            None,
        )
        if existing:
            if str(existing.get("state", "open")).casefold() == "closed":
                # A closed issue may have been resolved or closed by a human.
                # Never silently reopen or relabel it as active; the operator
                # must explicitly reopen it or choose a new downstream target.
                return {
                    "status": "blocked_closed",
                    "issue_number": existing.get("number"),
                    "issue_url": existing.get("html_url"),
                    "idempotent": False,
                }
            labels = {
                str(label.get("name"))
                for label in existing.get("labels") or []
                if isinstance(label, dict)
            }
            if "driftline-reversed" in labels:
                self._request(
                    "PUT",
                    f"{base}/issues/{existing.get('number')}/labels",
                    {
                        "labels": self._preserved_labels(
                            existing, "driftline-active"
                        )
                        + ["driftline-approval-gated"]
                    },
                )
                return {
                    "status": "reactivated",
                    "issue_number": existing.get("number"),
                    "issue_url": existing.get("html_url"),
                    "idempotent": True,
                }
            return {"status": "reused", "issue_number": existing.get("number"), "issue_url": existing.get("html_url"), "idempotent": True}
        created = self._request(
            "POST",
            f"{base}/issues",
            {
                "title": f"[Driftline] {artifact}",
                "body": f"{marker}\nWorkflow: {workflow_id}\nOwner: {owner}\nEvidence hash: {evidence_hash}\n\n{proposed}",
                "labels": ["driftline-active", "driftline-approval-gated"],
            },
        )
        return {"status": "created", "issue_number": created.get("number"), "issue_url": created.get("html_url"), "idempotent": False}

    def reverse_issue(self, issue_number: int, action_id: str) -> dict[str, Any]:
        base = f"/repos/{quote(self.config.owner)}/{quote(self.config.repo)}"
        issue = self._request("GET", f"{base}/issues/{issue_number}")
        self._request(
            "PUT",
            f"{base}/issues/{issue_number}/labels",
            {"labels": self._preserved_labels(issue, "driftline-reversed")},
        )
        self._request("POST", f"{base}/issues/{issue_number}/comments", {"body": f"Driftline action {action_id} was reversed by a named human reviewer."})
        return {"status": "reversed", "issue_number": issue_number}

    def read_context_summary(self) -> dict[str, Any]:
        """Return open issue/PR counts for the fixed repository only."""
        base = f"/repos/{quote(self.config.owner)}/{quote(self.config.repo)}"
        issues = self._request("GET", f"{base}/issues?state=open&per_page=100")
        if not isinstance(issues, list):
            raise ConnectorError("github_context_response_invalid")
        pull_requests = sum(1 for issue in issues if issue.get("pull_request"))
        driftline_owned = sum(
            1
            for issue in issues
            if any(str(label.get("name")) == "driftline-active" for label in issue.get("labels") or [])
        )
        return {
            "status": "ok",
            "scope": f"repository:{self.config.owner}/{self.config.repo}",
            "open_issue_count": len(issues) - pull_requests,
            "open_pull_request_count": pull_requests,
            "driftline_active_count": driftline_owned,
            "redaction": "aggregate_metadata_only",
        }


def execute_github_handoff(state: Any) -> dict[str, Any]:
    config = GitHubConfig.from_env()
    if not config.enabled:
        return {"github_status": "not_configured", "github_prepared_only": True, "external_write": False}
    config = GitHubConfig.from_env(_workflow_tenant_id(state), operation="create_issue")
    packet = next(
        (item for item in state.artifact_packets if item.get("status") == "packet_ready"),
        None,
    )
    if packet is None:
        return {"github_status": "not_eligible", "external_write": False}
    result = GitHubConnector(config).create_or_reuse_issue(
        action_id=str((state.action_record or {}).get("action_id", "unknown")),
        workflow_id=state.workflow_id,
        artifact=str(packet["artifact"]),
        owner=str(packet["owner"]),
        proposed=str(packet["content"]),
        evidence_hash=str(packet.get("evidence_hash", "none")),
    )
    return {
        "github_status": result["status"],
        "github_issue_number": result.get("issue_number"),
        "github_issue_url": result.get("issue_url"),
        "github_idempotent": result.get("idempotent", False),
        "external_write": result["status"] != "blocked_closed",
    }


def reverse_github_handoff(state: Any) -> dict[str, Any]:
    action = state.action_record or {}
    issue_number = action.get("github_issue_number")
    config = GitHubConfig.from_env()
    if not config.enabled or issue_number is None:
        return {"github_status": "not_configured", "github_prepared_only": True, "external_write": False}
    config = GitHubConfig.from_env(_workflow_tenant_id(state), operation="reverse_issue")
    result = GitHubConnector(config).reverse_issue(
        int(issue_number), str(action.get("action_id", "unknown"))
    )
    return {"github_status": result["status"], "github_issue_number": issue_number, "external_write": True}
