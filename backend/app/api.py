from __future__ import annotations

import asyncio
import base64
import copy
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
from collections import deque
from collections.abc import Callable
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from threading import Lock
from time import monotonic
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:  # Cloud Tasks is optional for local synthetic development.
    from google.api_core.exceptions import AlreadyExists as TaskAlreadyExists
    from google.cloud import tasks_v2
except ImportError:  # pragma: no cover - exercised only in a minimal local env.
    tasks_v2 = None
    TaskAlreadyExists = type("TaskAlreadyExists", (Exception,), {})

from .adk_runtime import run_agent_task
from .artifacts import persist_action_artifact, persist_operational_output
from .connectors import (
    ConfluenceConfig,
    ConfluenceConnector,
    ConnectorError,
    GitHubConfig,
    GitHubConnector,
    JiraConfig,
    JiraConnector,
    SalesforceConfig,
    SalesforceReadOnlyClient,
    SlackConfig,
    SlackConnector,
    exchange_salesforce_code,
    execute_confluence_handoff,
    execute_github_handoff,
    execute_jira_handoff,
    execute_slack_handoff,
    read_secret,
    refresh_salesforce_token,
    reverse_confluence_handoff,
    reverse_github_handoff,
    reverse_jira_handoff,
    reverse_slack_handoff,
    salesforce_authorization_url,
    salesforce_readiness,
    secret_version_for,
    tenant_secret_credentials,
    write_secret_version,
)
from .credential_broker import (
    CredentialBrokerError,
    allowed_operations,
    normalize_allowed_operations,
    resolve_tenant_credential,
)
from .decision_copilot import validate_approval_choice
from .materiality import build_change_card
from .memory import build_memory_summary
from .models import ActionItemStatus, JobState, WorkflowState, utc_now
from .multimodal import (
    MultimodalUnavailable,
    analyze_visual_evidence,
    get_visual_evidence,
    visual_asset_bytes,
)
from .persistence import (
    claim_job,
    compare_and_set_workflow,
    consume_salesforce_oauth_state,
    delete_salesforce_connection,
    list_connector_bindings,
    list_connector_profiles,
    list_credential_access_events,
    list_job_failures,
    list_jobs,
    list_outcome_measurements,
    list_tenant_audit_events,
    list_tenant_memberships,
    list_tenant_memberships_for_email,
    list_workflows,
    load_connector_binding,
    load_connector_profile,
    load_credential_enrollment,
    load_job,
    load_salesforce_connection,
    load_tenant,
    load_tenant_policy,
    load_tenant_usage,
    load_workflow,
    persist_connector_binding,
    persist_connector_profile,
    persist_credential_enrollment,
    persist_job,
    persist_job_failure,
    persist_outcome_measurement,
    persist_salesforce_connection,
    persist_salesforce_oauth_state,
    persist_tenant,
    persist_tenant_audit_event,
    persist_tenant_membership,
    persist_tenant_policy,
    persist_workflow,
    provision_tenant_metadata,
    record_tenant_usage,
    reserve_tenant_rate_limit,
    update_jobs_for_workflow,
)


def _read_tenant_secret(tenant_id: str, secret_name: str, *, version: str = "latest") -> str:
    """Read through the tenant identity with compatibility for local fakes."""
    credentials = tenant_secret_credentials(tenant_id)
    try:
        return read_secret(secret_name, version=version, credentials=credentials)
    except TypeError:
        # Older local test doubles accepted only the secret name. This branch
        # never runs with the production Secret Manager client.
        try:
            return read_secret(secret_name, version=version)
        except TypeError:
            return read_secret(secret_name)


def _tenant_secret_version(tenant_id: str, secret_name: str) -> str:
    credentials = tenant_secret_credentials(tenant_id)
    try:
        return secret_version_for(secret_name, credentials=credentials)
    except TypeError:
        return secret_version_for(secret_name)


def _write_tenant_secret(tenant_id: str, secret_name: str, value: str) -> str | None:
    credentials = tenant_secret_credentials(tenant_id)
    try:
        return write_secret_version(secret_name, value, credentials=credentials)
    except TypeError:
        return write_secret_version(secret_name, value)
from .simulator import simulate_scenarios
from .source import (
    inspect_allowlisted_source,
    list_allowlisted_sources,
    list_source_history,
    register_operator_source,
    scheduler_source_entries,
    source_definition,
    source_definitions,
    source_registry_health,
)
from .tenant import (
    CONNECTOR_NAMES,
    principal_for_claims,
    principal_for_hmac,
    public_demo_principal,
    tenant_connector_secret_name,
    tenant_credential_namespace,
    tenant_operator_signing_secret_name,
    validate_connector_name,
    validate_connector_profile,
    validate_tenant_id,
)
from .workflow import PolicyViolation, packet_markdown, workflow_store

logger = logging.getLogger("driftline.api")
app = FastAPI(title="Driftline API", version="0.2.0")
_request_auth: ContextVar[tuple[str | None, str | None]] = ContextVar(
    "driftline_request_auth", default=(None, None)
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    )
    if request.url.path.startswith("/api/"):
        # API responses can contain tenant-scoped metadata or one-time OAuth
        # handoff state. Never let a browser, proxy, or shared intermediary
        # retain those responses beyond the request.
        response.headers["Cache-Control"] = "no-store"
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self' https://accounts.google.com/gsi/client; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self' https://accounts.google.com/gsi/; frame-src https://accounts.google.com/gsi/; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    )
    # Cloud Run terminates TLS before forwarding to Uvicorn, so the app often
    # sees an internal HTTP scheme even for the public HTTPS URL. The service
    # has no HTTP-only public route; emit HSTS unconditionally so the browser
    # never downgrades the deployed console.
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )
    return response


@app.middleware("http")
async def secure_get_auth(request: Request, call_next):
    """Keep bearer/HMAC credentials out of URLs and access logs.

    Endpoint models retain their explicit token fields for local/bootstrap
    compatibility, but hosted requests resolve credentials from headers via a
    request-scoped context. Never rewrite the query string with a bearer token:
    ASGI access logging can record that URL before the endpoint runs.
    """
    if request.method == "GET" and os.getenv(
        "DRIFTLINE_REJECT_QUERY_AUTH", "false"
    ).casefold() == "true":
        pairs = parse_qsl(
            request.scope.get("query_string", b"").decode(), keep_blank_values=True
        )
        sensitive_keys = {"approval_token", "identity_token"}
        if {key for key, _value in pairs} & sensitive_keys:
            # Uvicorn's access logger reads the mutable ASGI scope. Remove
            # credential parameters before returning the rejection so a
            # hostile query token cannot be retained in the request line.
            request.scope["query_string"] = urlencode(
                [
                    (key, value)
                    for key, value in pairs
                    if key not in sensitive_keys
                ]
            ).encode()
            return JSONResponse(
                {"detail": "Query authentication is disabled; use request headers."},
                status_code=400,
            )
    auth_token = _request_auth.set(
        (request.headers.get("x-driftline-approval"), request.headers.get("authorization"))
    )
    try:
        return await call_next(request)
    finally:
        _request_auth.reset(auth_token)


class ApprovalRequest(BaseModel):
    approver: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    decision: str = Field(default="grandfather_existing_customers", max_length=64)
    artifact_decisions: dict[str, str] | None = None
    copilot_option_id: str | None = Field(default=None, min_length=3, max_length=64)
    copilot_artifact_override: bool = False
    copilot_override_reason: str | None = Field(default=None, min_length=3, max_length=240)
    approval_mode: Literal["demo", "signed"] = "demo"
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class UndoRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_mode: Literal["demo", "signed"] = "demo"
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class DismissRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=3, max_length=240)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_mode: Literal["demo", "signed"] = "demo"
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class ConnectorContextRequest(BaseModel):
    """Signed operator request for aggregate-only internal context."""

    operator: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class ConnectorBindingRequest(BaseModel):
    """Owner request to register/verify a tenant connector secret binding."""

    operator: str = Field(min_length=1, max_length=120)
    allowed_operations: list[str] | None = Field(default=None, max_length=10)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class ConnectorCredentialEnrollmentRequest(BaseModel):
    """Owner request for a short-lived, secret-free connector enrollment."""

    operator: str = Field(min_length=1, max_length=120)
    allowed_operations: list[str] | None = Field(default=None, max_length=10)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class ConnectorBindingRotationRequest(BaseModel):
    """Owner request to begin a tenant connector credential rotation."""

    operator: str = Field(min_length=1, max_length=120)
    reason: str = Field(default="credential_rotation", min_length=3, max_length=240)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class ConnectorProfileRequest(BaseModel):
    """Owner-managed non-secret connector destination profile."""

    operator: str = Field(min_length=1, max_length=120)
    settings: dict[str, str] = Field(default_factory=dict)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class TenantMemberRequest(BaseModel):
    """Owner-managed durable membership metadata; never accepts credentials."""

    operator: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    role: Literal["viewer", "operator", "owner"] = "viewer"
    status: Literal["active", "disabled"] = "active"
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class TenantDeprovisionRequest(BaseModel):
    """Owner-confirmed soft deprovisioning request; never deletes secrets."""

    operator: str = Field(min_length=1, max_length=120)
    tenant_id: str = Field(min_length=3, max_length=63)
    confirmation: str = Field(min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class TenantPolicyRequest(BaseModel):
    """Owner-managed bounded tenant allowance and retention; never billing."""

    operator: str = Field(min_length=1, max_length=120)
    agent_calls_per_window: int = Field(default=10, ge=1, le=1000)
    workflow_mutations_per_window: int = Field(default=30, ge=1, le=1000)
    connector_calls_per_window: int = Field(default=60, ge=1, le=1000)
    retention_days: int = Field(default=30, ge=1, le=3650)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class PlatformTenantProvisionRequest(BaseModel):
    """Platform-admin tenant bootstrap metadata; never accepts credentials."""

    operator: str = Field(min_length=1, max_length=120)
    tenant_id: str = Field(min_length=3, max_length=63)
    owner_email: str = Field(min_length=3, max_length=320)
    identity_token: str | None = Field(default=None, max_length=4096)


class ActionItemRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_mode: Literal["demo", "signed"] = "demo"
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class ActionFailureRequest(ActionItemRequest):
    reason: str = Field(min_length=1, max_length=240)


class AgentRunRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    user_id: str = Field(default="demo-operator", min_length=1, max_length=128)
    source_id: str = Field(default="public/pricing", min_length=1, max_length=80)
    # The public judge path intentionally omits these fields and stays
    # tenantless. A real operator can supply the same signed identity fields
    # used by the connector/action lanes so ADK execution carries a durable
    # tenant boundary all the way into source inspection and Firestore state.
    operator: str | None = Field(default=None, min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class JobStartRequest(BaseModel):
    query: str = Field(
        default=(
            "Inspect the allowlisted public/pricing change, verify the evidence, "
            "map the affected artifacts, and stop at the human approval gate."
        ),
        min_length=1,
        max_length=2000,
    )
    user_id: str = Field(default="demo-operator", min_length=1, max_length=128)
    # ``tenant_demo`` is an authenticated pilot lane: it replays one of the
    # pinned fixtures through the real ADK coordinator while retaining the
    # tenant boundary and connector approval gates. It is deliberately
    # distinct from both the anonymous judge replay and live monitoring.
    run_mode: Literal["demo", "monitor", "tenant_demo"] = "demo"
    source_id: str = Field(default="public/pricing", min_length=1, max_length=80)
    operator: str = Field(default="demo-operator", min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class JobRetryRequest(BaseModel):
    """Tenant-authenticated retry request; never accepts a new query or source."""

    operator: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class MultimodalAnalysisRequest(BaseModel):
    asset_id: str = Field(default="promise-card", min_length=1, max_length=80)
    mode: Literal["live", "demo"] = "live"


class SourceOnboardingRequest(BaseModel):
    source_id: str = Field(min_length=8, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    change_type: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=12, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    cadence: str = Field(default="24h", max_length=4)
    freshness_sla_hours: int = Field(default=48, ge=1, le=168)
    parser: Literal["html", "text", "rss"] = "html"
    registered_by: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class OutcomeMeasurementRequest(BaseModel):
    """Aggregate pilot evidence; raw customer text and identifiers are excluded."""

    operator: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    source_type: Literal[
        "customer_interview", "pilot_log", "win_loss", "billing_record"
    ]
    cohort_label: str = Field(min_length=1, max_length=80)
    changes_observed: int = Field(ge=1, le=10000)
    baseline_minutes: float = Field(ge=0, le=1_000_000)
    driftline_minutes: float = Field(ge=0, le=1_000_000)
    revenue_lift_usd: float | None = Field(
        default=None, ge=-1_000_000_000, le=1_000_000_000
    )
    retention_lift_pct: float | None = Field(default=None, ge=-100, le=100)
    willingness_to_pay_usd: float | None = Field(default=None, ge=0, le=1_000_000)
    evidence_ref: str = Field(min_length=1, max_length=300)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class SalesforceConnectRequest(BaseModel):
    operator: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    approval_token: str | None = Field(default=None, max_length=256)
    identity_token: str | None = Field(default=None, max_length=4096)


class SalesforceHealthRequest(SalesforceConnectRequest):
    pass


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


AGENT_MAX_CALLS = _positive_int("DRIFTLINE_AGENT_MAX_CALLS", 10)
AGENT_WINDOW_SECONDS = _positive_int("DRIFTLINE_AGENT_WINDOW_SECONDS", 3600)
_agent_call_times: deque[float] = deque()
_tenant_agent_call_times: dict[str, deque[float]] = {}
_agent_call_lock = Lock()

DEMO_MAX_MUTATIONS = _positive_int("DRIFTLINE_DEMO_MAX_MUTATIONS", 30)
DEMO_WINDOW_SECONDS = _positive_int("DRIFTLINE_DEMO_WINDOW_SECONDS", 3600)
_demo_mutation_times: deque[float] = deque()
_tenant_demo_mutation_times: dict[str, deque[float]] = {}
_demo_mutation_lock = Lock()
CONNECTOR_MAX_CALLS = _positive_int("DRIFTLINE_CONNECTOR_MAX_CALLS", 60)
CONNECTOR_WINDOW_SECONDS = _positive_int(
    "DRIFTLINE_CONNECTOR_WINDOW_SECONDS", 3600
)
_connector_call_times: deque[float] = deque()
_tenant_connector_call_times: dict[str, deque[float]] = {}
_connector_call_lock = Lock()
MULTIMODAL_MAX_CALLS = _positive_int("DRIFTLINE_MULTIMODAL_MAX_CALLS", 10)
MULTIMODAL_WINDOW_SECONDS = _positive_int(
    "DRIFTLINE_MULTIMODAL_WINDOW_SECONDS", 3600
)
_multimodal_call_times: deque[float] = deque()
_multimodal_call_lock = Lock()
MAX_JOB_ATTEMPTS = _positive_int("DRIFTLINE_MAX_JOB_ATTEMPTS", 3)

_salesforce_oauth_states: dict[str, dict[str, object]] = {}
_salesforce_oauth_lock = Lock()

_jobs: dict[str, JobState] = {}
_jobs_lock = Lock()
_workflow_transition_lock = Lock()
_background_tasks: set[asyncio.Task[None]] = set()


def _merge_durable_records(
    memory_records: list[Any],
    loader: Callable[[int], list[Any]],
    *,
    limit: int,
    key: Callable[[Any], str],
) -> list[Any]:
    """Merge the current instance with durable history for operator metrics.

    Cloud Run instances are intentionally disposable. Reading only the local
    cache whenever it contains one record makes value proof, memory, and ops
    summaries under-report after a fresh instance starts. Firestore remains
    the source of truth in hosted mode; the local copy wins for an in-flight
    transition that has not finished its durable write. A bounded local
    fallback keeps local development and a transient Firestore outage useful.
    """
    if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() != "firestore":
        return memory_records
    try:
        durable_records = loader(limit)
    except Exception:  # noqa: BLE001 - metrics must not take the console down.
        logger.warning("Durable record merge unavailable; using local records")
        return memory_records
    merged = {key(record): record for record in durable_records if key(record)}
    for record in memory_records:
        identifier = key(record)
        if identifier:
            merged[identifier] = record
    return list(merged.values())


def _visible_tenant_record(record: Any, identity: dict[str, str] | None) -> bool:
    """Apply the public-vs-tenant record visibility contract.

    Anonymous requests are limited to tenantless demo records. Once a caller
    is authenticated, tenantless records must not be mixed into that tenant's
    operational counts: they are deployment-wide fixtures, not customer
    evidence. A signed request therefore requires an exact tenant match.
    """
    tenant_id = getattr(record, "tenant_id", None)
    if identity is None:
        return tenant_id is None
    return tenant_id is not None and tenant_id == identity.get("tenant_id")


def _count_record_modes(records: list[Any], attribute: str) -> dict[str, int]:
    """Count a bounded record mode field without leaking record contents."""
    counts: dict[str, int] = {}
    for record in records:
        mode = str(getattr(record, attribute, None) or "unknown")
        counts[mode] = counts.get(mode, 0) + 1
    return counts


def _record_tenant_usage(tenant_id: str | None, metric: str) -> None:
    """Best-effort aggregate metering after a quota slot is reserved."""
    if not tenant_id:
        return
    try:
        record_tenant_usage(tenant_id, metric)
    except Exception:  # noqa: BLE001 - metering must not authorize extra work.
        logger.warning("Tenant usage ledger update failed for %s/%s", tenant_id, metric)


def _tenant_quota_limit(tenant_id: str | None, metric: str, fallback: int) -> int:
    """Resolve one tenant's bounded allowance without widening on failure."""
    if not tenant_id:
        return fallback
    policy_key = {
        "agent_calls": "agent_calls_per_window",
        "workflow_mutations": "workflow_mutations_per_window",
        "connector_calls": "connector_calls_per_window",
    }.get(metric)
    if policy_key is None:
        return fallback
    try:
        policy = load_tenant_policy(tenant_id, defaults={policy_key: fallback})
        return max(1, min(int(policy.get(policy_key, fallback)), 1000))
    except Exception:  # noqa: BLE001 - quota lookup must fail closed hosted.
        if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore":
            return 0
        return fallback


def _reserve_durable_tenant_slot(
    tenant_id: str | None, metric: str, limit: int, window_seconds: int
) -> bool | None:
    """Reserve a signed tenant slot transactionally when Firestore is active.

    None means local development mode, where the process-local bucket remains
    authoritative. A Firestore error fails closed instead of silently allowing
    unmetered tenant work.
    """
    if not tenant_id:
        return None
    if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() != "firestore":
        return None
    try:
        return reserve_tenant_rate_limit(
            tenant_id, metric, limit, window_seconds
        )
    except Exception:
        logger.exception("Durable tenant quota reservation failed")
        return False


def _reserve_agent_call(tenant_id: str | None = None) -> bool:
    limit = _tenant_quota_limit(tenant_id, "agent_calls", AGENT_MAX_CALLS)
    if limit < 1:
        return False
    durable = _reserve_durable_tenant_slot(
        tenant_id, "agent_calls", limit, AGENT_WINDOW_SECONDS
    )
    if durable is not None:
        if durable:
            _record_tenant_usage(tenant_id, "agent_calls")
        return durable
    now = monotonic()
    cutoff = now - AGENT_WINDOW_SECONDS
    with _agent_call_lock:
        times = (
            _tenant_agent_call_times.setdefault(tenant_id, deque())
            if tenant_id
            else _agent_call_times
        )
        while times and times[0] <= cutoff:
            times.popleft()
        if len(times) >= limit:
            return False
        times.append(now)
        _record_tenant_usage(tenant_id, "agent_calls")
        return True


def _reserve_demo_mutation(tenant_id: str | None = None) -> bool:
    limit = _tenant_quota_limit(tenant_id, "workflow_mutations", DEMO_MAX_MUTATIONS)
    if limit < 1:
        return False
    durable = _reserve_durable_tenant_slot(
        tenant_id, "workflow_mutations", limit, DEMO_WINDOW_SECONDS
    )
    if durable is not None:
        if durable:
            _record_tenant_usage(tenant_id, "workflow_mutations")
        return durable
    now = monotonic()
    cutoff = now - DEMO_WINDOW_SECONDS
    with _demo_mutation_lock:
        times = (
            _tenant_demo_mutation_times.setdefault(tenant_id, deque())
            if tenant_id
            else _demo_mutation_times
        )
        while times and times[0] <= cutoff:
            times.popleft()
        if len(times) >= limit:
            return False
        times.append(now)
        _record_tenant_usage(tenant_id, "workflow_mutations")
        return True


def _reserve_connector_call(tenant_id: str | None = None) -> bool:
    """Reserve one bounded external connector read for the tenant."""
    limit = _tenant_quota_limit(
        tenant_id, "connector_calls", CONNECTOR_MAX_CALLS
    )
    if limit < 1:
        return False
    durable = _reserve_durable_tenant_slot(
        tenant_id, "connector_calls", limit, CONNECTOR_WINDOW_SECONDS
    )
    if durable is not None:
        if durable:
            _record_tenant_usage(tenant_id, "connector_calls")
        return durable
    now = monotonic()
    cutoff = now - CONNECTOR_WINDOW_SECONDS
    with _connector_call_lock:
        times = (
            _tenant_connector_call_times.setdefault(tenant_id, deque())
            if tenant_id
            else _connector_call_times
        )
        while times and times[0] <= cutoff:
            times.popleft()
        if len(times) >= limit:
            return False
        times.append(now)
        _record_tenant_usage(tenant_id, "connector_calls")
        return True


def _reserve_multimodal_call() -> int | None:
    """Reserve one public visual-analysis call and return retry seconds.

    Visual analysis is deliberately allowlisted, but it still crosses the
    Vertex/Gemini cost boundary. Keep a process-wide budget and tell clients
    when the fixed window will reopen instead of leaving them to retry-loop.
    Cloud Run is configured with one maximum instance, so this guard bounds
    the public deployment's normal request path without adding tenant data to
    the identity-free demo lane.
    """
    now = monotonic()
    cutoff = now - MULTIMODAL_WINDOW_SECONDS
    with _multimodal_call_lock:
        while _multimodal_call_times and _multimodal_call_times[0] <= cutoff:
            _multimodal_call_times.popleft()
        if len(_multimodal_call_times) >= MULTIMODAL_MAX_CALLS:
            return max(
                1,
                int(
                    _multimodal_call_times[0]
                    + MULTIMODAL_WINDOW_SECONDS
                    - now
                )
                + 1,
            )
        _multimodal_call_times.append(now)
        return None


def _tasks_enabled() -> bool:
    return os.getenv("DRIFTLINE_TASKS_ENABLED", "false").casefold() == "true"


def _resolve_workflow(workflow_id: str):
    try:
        return workflow_store.get(workflow_id)
    except KeyError:
        state = load_workflow(workflow_id)
        if state is not None:
            return workflow_store.restore(state)
        raise


def _enforce_workflow_tenant(
    state: WorkflowState, approval_identity: dict[str, str]
) -> None:
    """Prevent a signed operator from acting on another tenant's workflow."""
    scope = approval_identity.get("scope")
    # Keep accepting the legacy value for persisted/local identities, but use
    # the production-facing name for all new public decisions.
    if scope in {"public_packet_only", "sandbox_packet_only"}:
        if state.tenant_id is not None:
            raise HTTPException(
                status_code=403,
                detail="Tenant-scoped workflow requires signed approval",
            )
        return
    expected_tenant = approval_identity.get("tenant_id")
    if not expected_tenant or not state.tenant_id:
        raise HTTPException(status_code=403, detail="workflow_tenant_missing")
    if state.tenant_id != expected_tenant:
        raise HTTPException(status_code=403, detail="workflow_tenant_mismatch")


def _authorize_workflow_tenant(
    workflow_id: str, approval_identity: dict[str, str]
) -> None:
    try:
        state = _resolve_workflow(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _enforce_workflow_tenant(state, approval_identity)


def _authorize_read_tenant(
    state: WorkflowState | JobState,
    *,
    resource_id: str,
    operator: str | None,
    tenant_id: str | None,
    approval_token: str | None,
    identity_token: str | None,
) -> None:
    """Keep tenant-bound reads behind the same signed operator boundary.

    The public judge console deliberately reads tenantless synthetic fixtures.
    A real monitor job/workflow, however, can contain connector-derived
    metadata and must never become readable merely because its identifier is
    guessed.  Signed callers use the exact same HMAC/OIDC identity path as
    mutations and are checked against the resource tenant.
    """
    if state.tenant_id is None:
        return
    if not operator or not tenant_id:
        raise HTTPException(
            status_code=403, detail="Tenant-scoped resource requires signed approval"
        )
    identity = _verify_approval_mode(
        resource_id,
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    _enforce_workflow_tenant(state, identity)


def _resolve_job(job_id: str) -> JobState:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is not None:
        return job
    job = load_job(job_id)
    if job is not None:
        with _jobs_lock:
            _jobs[job_id] = job
        return job
    raise KeyError(f"Unknown job: {job_id}")


def _claim_job_for_run(job_id: str) -> bool:
    """Claim a queued job before invoking the agent runtime.

    The process lock closes the local race; ``claim_job`` adds the durable
    Firestore transaction for duplicate Cloud Tasks deliveries across Cloud
    Run instances.
    """
    claim_id = f"claim-{uuid4().hex}"
    with _jobs_lock:
        try:
            job = _jobs.get(job_id) or load_job(job_id)
        except Exception:
            logger.exception("Unable to load job %s for claiming", job_id)
            return False
        if job is None:
            return False
        if job.status != "queued":
            _jobs[job_id] = job
            return False
        if not claim_job(job_id, claim_id):
            durable = load_job(job_id)
            if durable is not None:
                _jobs[job_id] = durable
            return False
        job.status = "running"
        job.claim_id = claim_id
        job.run_attempts += 1
        job.touch()
        _jobs[job_id] = job
    persist_job(job)
    return True


def _set_job(job: JobState) -> None:
    job.touch()
    with _jobs_lock:
        _jobs[job.job_id] = job
    persist_job(job)


def _sync_jobs_for_workflow(workflow_id: str, status: str) -> None:
    with _jobs_lock:
        matching = [job for job in _jobs.values() if job.workflow_id == workflow_id]
    for job in matching:
        job.status = status
        _set_job(job)
    update_jobs_for_workflow(workflow_id, status)


def _safe_connector_call(
    operation: Callable[[WorkflowState], dict[str, object]],
    status_key: str,
    state: WorkflowState,
) -> dict[str, object]:
    try:
        return operation(state)
    except (ConnectorError, CredentialBrokerError) as exc:
        logger.warning("%s connector failed: %s", status_key, exc)
        return {f"{status_key}_status": "failed", "external_write": False}


def _enqueue_cloud_task(job: JobState) -> None:
    if tasks_v2 is None:
        raise RuntimeError("Cloud Tasks dependency is unavailable")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("DRIFTLINE_TASK_LOCATION", "us-central1")
    queue = os.getenv("DRIFTLINE_TASK_QUEUE", "driftline-jobs")
    target_url = os.getenv("DRIFTLINE_TASK_TARGET_URL")
    service_account = os.getenv("DRIFTLINE_TASK_SERVICE_ACCOUNT")
    if not project or not target_url or not service_account:
        raise RuntimeError("Cloud Tasks configuration is incomplete")

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)
    task = tasks_v2.Task(
        # A deterministic task name makes an enqueue retry idempotent.  Cloud
        # Tasks returns ALREADY_EXISTS for the same job instead of creating a
        # second delivery.
        name=client.task_path(project, location, queue, job.job_id),
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=f"{target_url.rstrip('/')}/api/jobs/{job.job_id}/run",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"job_id": job.job_id}).encode("utf-8"),
            oidc_token=tasks_v2.OidcToken(
                service_account_email=service_account,
                audience=target_url.rstrip("/"),
            ),
        ),
    )
    try:
        client.create_task(parent=parent, task=task)
    except TaskAlreadyExists:
        logger.info(
            "Cloud Task for %s already exists; treating enqueue as success", job.job_id
        )


def _verify_task_request(request: Request) -> None:
    if not _tasks_enabled():
        return
    authorization = request.headers.get("authorization", "")
    expected_audience = os.getenv("DRIFTLINE_TASK_TARGET_URL", "").rstrip("/")
    expected_email = os.getenv("DRIFTLINE_TASK_SERVICE_ACCOUNT", "")
    if not authorization.startswith("Bearer ") or not expected_audience:
        raise HTTPException(status_code=401, detail="Task identity is required")
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            authorization.removeprefix("Bearer ").strip(),
            GoogleRequest(),
            audience=expected_audience,
        )
    except Exception as exc:  # pragma: no cover - token verification is cloud-only.
        raise HTTPException(status_code=401, detail="Invalid task identity") from exc
    if expected_email and claims.get("email") != expected_email:
        raise HTTPException(status_code=403, detail="Unexpected task identity")


def _verify_scheduler_request(request: Request) -> None:
    """Verify the dedicated Cloud Scheduler identity before monitor ticks."""
    authorization = request.headers.get("authorization", "")
    expected_audience = os.getenv("DRIFTLINE_SCHEDULER_AUDIENCE", "").rstrip("/")
    expected_email = os.getenv("DRIFTLINE_SCHEDULER_SERVICE_ACCOUNT", "")
    if not authorization.startswith("Bearer ") or not expected_audience:
        raise HTTPException(status_code=401, detail="Scheduler identity is required")
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            authorization.removeprefix("Bearer ").strip(),
            GoogleRequest(),
            audience=expected_audience,
        )
    except Exception as exc:  # pragma: no cover - token verification is cloud-only.
        raise HTTPException(
            status_code=401, detail="Invalid scheduler identity"
        ) from exc
    if expected_email and claims.get("email") != expected_email:
        raise HTTPException(status_code=403, detail="Unexpected scheduler identity")


def _verify_approval_mode(
    workflow_id: str,
    actor: str,
    mode: str,
    token: str | None,
    identity_token: str | None = None,
    requested_tenant_id: str | None = None,
) -> dict[str, str]:
    """Bound public decisions to an explicit demo or signed approval mode.

    The public console intentionally runs in ``demo`` mode and creates
    packet-only outputs. A configured operator lane can use a Google OIDC
    identity for the allowlisted operator email, or an HMAC token generated
    from the dedicated approval secret as an isolated break-glass path;
    unsigned public names are rejected before the workflow policy engine runs.
    """
    header_approval, header_identity = _request_auth.get()
    token = token or header_approval
    identity_token = identity_token or header_identity
    configured = os.getenv("DRIFTLINE_APPROVAL_MODE", "demo").casefold()
    signed_enabled = (
        os.getenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "false").casefold() == "true"
    )
    # Keep the public judge console in demo mode while allowing a separately
    # signed operator lane to exercise configured connectors.  A deployment
    # configured as signed remains strict and never accepts demo approvals.
    if configured == "signed" and mode != "signed":
        raise HTTPException(status_code=403, detail="Approval mode is not enabled")
    if mode == "signed" and configured != "signed" and not signed_enabled:
        raise HTTPException(status_code=403, detail="Signed approval is not enabled")
    if mode == "demo" and configured != "demo":
        raise HTTPException(status_code=403, detail="Approval mode is not enabled")
    cleaned = actor.strip()
    if mode == "demo":
        principal = public_demo_principal()
        return {
            "mode": "demo",
            "identity": "named_demo_actor",
            "scope": "public_packet_only",
            "tenant_id": principal.tenant_id,
            "role": principal.role,
        }
    if identity_token:
        audience = os.getenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "").strip()
        if not audience:
            raise HTTPException(
                status_code=403, detail="Google operator identity is not enabled"
            )
        try:
            claims = _verify_google_identity_claims(identity_token, audience)
        except Exception as exc:  # pragma: no cover - Google-only runtime path.
            raise HTTPException(
                status_code=401, detail="Invalid Google operator identity"
            ) from exc
        email = str(claims.get("email", "")).casefold()
        allowed = {
            item.strip().casefold()
            for item in os.getenv("DRIFTLINE_OPERATOR_EMAILS", "").split(",")
            if item.strip()
        }
        if allowed and email not in allowed:
            raise HTTPException(
                status_code=403, detail="Google operator is not allowlisted"
            )
        try:
            principal = principal_for_claims(
                subject=str(claims.get("sub", "")),
                email=email,
                requested_tenant_id=requested_tenant_id,
            )
        except (ValueError, PermissionError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if not principal.can("operator"):
            raise HTTPException(
                status_code=403, detail="Tenant role cannot perform this operation"
            )
        return {
            "mode": "signed",
            "identity": "google_oidc_operator",
            "scope": "configured",
            "subject": str(claims.get("sub", "")),
            "email": email,
            "tenant_id": principal.tenant_id,
            "role": principal.role,
        }
    # Production tenant lanes should use short-lived Google OIDC identities,
    # not a replayable break-glass bearer value. Keep the HMAC path available
    # only when an operator explicitly opts into it (local/bootstrap or an
    # incident runbook), and fail closed when the deployment requires OIDC.
    if (
        os.getenv("DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY", "false").casefold()
        == "true"
    ):
        raise HTTPException(
            status_code=401,
            detail="Google operator identity is required for this deployment",
        )
    # A deployment-wide signer is retained only as an explicit compatibility
    # fallback. SaaS deployments can set a deterministic, infrastructure-owned
    # per-tenant secret prefix and require every break-glass request to use the
    # tenant's own signer. OIDC remains preferred for normal operator traffic.
    tenant_for_signing = requested_tenant_id or os.getenv(
        "DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo"
    )
    try:
        tenant_for_signing = validate_tenant_id(tenant_for_signing)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="tenant_id_invalid") from exc
    secret = ""
    tenant_signing_prefix = os.getenv(
        "DRIFTLINE_TENANT_SIGNING_SECRET_PREFIX", ""
    ).strip()
    require_tenant_signer = (
        os.getenv("DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS", "false").casefold()
        == "true"
    )
    if tenant_signing_prefix:
        try:
            secret = _read_tenant_secret(
                tenant_for_signing,
                tenant_operator_signing_secret_name(
                    tenant_for_signing, tenant_signing_prefix
                ),
            ).strip()
        except (ConnectorError, ValueError):
            if require_tenant_signer:
                raise HTTPException(
                    status_code=401, detail="Tenant signing secret is unavailable"
                ) from None
    if not secret and not require_tenant_signer:
        secret = os.getenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", "")
    if not secret or not token:
        raise HTTPException(status_code=401, detail="Signed approval is required")
    message = f"{workflow_id}:{cleaned}".encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid signed approval")
    try:
        principal = principal_for_hmac(requested_tenant_id)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "mode": "signed",
        "identity": "signed_operator",
        "scope": "configured",
        "tenant_id": principal.tenant_id,
        "role": principal.role,
    }


def _verify_platform_operator(identity_token: str | None) -> dict[str, str]:
    """Verify the separate platform-admin OIDC boundary for tenant bootstrap."""
    audience = os.getenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "").strip()
    if not identity_token or not audience:
        raise HTTPException(status_code=401, detail="Platform identity is required")
    try:
        claims = _verify_google_identity_claims(identity_token, audience)
    except Exception as exc:  # pragma: no cover - Google-only runtime path.
        raise HTTPException(status_code=401, detail="Invalid platform identity") from exc
    email = str(claims.get("email", "")).strip().casefold()
    allowed = {
        item.strip().casefold()
        for item in os.getenv("DRIFTLINE_PLATFORM_OPERATOR_EMAILS", "").split(",")
        if item.strip()
    }
    if not email or email not in allowed:
        raise HTTPException(status_code=403, detail="Platform operator is not allowlisted")
    return {
        "identity": "google_oidc_platform_operator",
        "subject": str(claims.get("sub", "")),
        "email": email,
    }


def _verify_google_identity_claims(
    identity_token: str | None, audience: str
) -> dict[str, object]:
    """Verify a Google OIDC identity once, including the tenant-safe claims.

    This helper is shared by the tenant selector and signed operator routes so
    both use the same audience, issuer, expiry, and verified-email checks. It
    intentionally returns claims only in memory; no token is persisted.
    """
    if not identity_token or not audience:
        raise ValueError("google_identity_required")
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import id_token

    claims = id_token.verify_oauth2_token(
        identity_token.removeprefix("Bearer ").strip(),
        GoogleRequest(),
        audience=audience,
    )
    issuer = str(claims.get("iss", ""))
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValueError("google_identity_issuer_invalid")
    email = str(claims.get("email", "")).strip().casefold()
    if not email or claims.get("email_verified") is False:
        raise ValueError("google_identity_email_unverified")
    if not str(claims.get("sub", "")).strip():
        raise ValueError("google_identity_subject_missing")
    return claims


_CONNECTOR_HANDOFFS: tuple[
    tuple[
        str,
        Callable[[WorkflowState], dict[str, object]],
        Callable[[WorkflowState], dict[str, object]],
    ],
    ...,
] = (
    ("jira", execute_jira_handoff, reverse_jira_handoff),
    ("confluence", execute_confluence_handoff, reverse_confluence_handoff),
    ("slack", execute_slack_handoff, reverse_slack_handoff),
    ("github", execute_github_handoff, reverse_github_handoff),
)


def _prepared_connector_info() -> dict[str, object]:
    """Return an honest packet-only result for the public demo lane.

    Connector configuration is intentionally not enough to authorize a write:
    only a signed operator approval can cross that boundary. This protects the
    public demo even if credentials are present in the isolated deployment.
    """
    result: dict[str, object] = {}
    for name, _, _ in _CONNECTOR_HANDOFFS:
        result[f"{name}_status"] = "prepared_only"
        result[f"{name}_prepared_only"] = True
        result[f"{name}_external_write"] = False
    return result


def _connector_handoff_info(
    state: WorkflowState,
    approval_identity: dict[str, str],
    *,
    reverse: bool = False,
) -> dict[str, object]:
    """Execute connector work only inside the signed, configured lane."""
    if approval_identity.get("scope") != "configured":
        return _prepared_connector_info()
    result: dict[str, object] = {}
    for name, execute, undo in _CONNECTOR_HANDOFFS:
        operation = undo if reverse else execute
        result.update(_safe_connector_call(operation, name, state))
    return result


def _connector_context_info(tenant_id: str) -> dict[str, object]:
    """Read fixed internal scopes and return aggregate metadata only.

    This lane is deliberately independent of approval-time writes. A bad or
    unavailable connector produces an explicit status rather than partial raw
    records, and no connector receives user-supplied paths, JQL, channel IDs,
    or repository names.
    """
    definitions: tuple[tuple[str, Callable[[], object], str], ...] = (
        ("jira", lambda: JiraConnector(JiraConfig.from_env(tenant_id)).read_context_summary(), "read_only_project"),
        ("confluence", lambda: ConfluenceConnector(ConfluenceConfig.from_env(tenant_id)).read_context_summary(), "read_only_space"),
        ("slack", lambda: SlackConnector(SlackConfig.from_env(tenant_id)).read_context_summary(), "read_only_channel"),
        ("github", lambda: GitHubConnector(GitHubConfig.from_env(tenant_id)).read_context_summary(), "read_only_repository"),
    )
    result: dict[str, object] = {}
    for name, operation, scope in definitions:
        enabled = os.getenv(f"DRIFTLINE_{name.upper()}_ENABLED", "false").casefold() == "true"
        if not enabled:
            result[name] = {
                "status": "not_configured",
                "mode": "prepared_only",
                "scope": scope,
                "external_read": False,
                "redaction": "aggregate_metadata_only",
            }
            continue
        try:
            summary = operation()
            result[name] = {**summary, "external_read": True}
        except ConnectorError as exc:
            logger.warning("%s context read failed: %s", name, exc)
            result[name] = {
                "status": "failed",
                "mode": "read_only_context",
                "scope": scope,
                "external_read": False,
                "reason": str(exc),
                "redaction": "aggregate_metadata_only",
            }
    return result


def _transition_workflow(
    workflow_id: str,
    expected_status: str,
    transition: Callable[[WorkflowState], WorkflowState],
) -> WorkflowState:
    """Run one policy transition and commit it with a durable CAS."""
    with _workflow_transition_lock:
        state = _resolve_workflow(workflow_id)
        previous = copy.deepcopy(state)
        result = transition(state)
        if not compare_and_set_workflow(result, expected_status):
            # Restore this process from durable truth after a cross-instance
            # race, rather than leaving a locally mutated but uncommitted run.
            durable = load_workflow(workflow_id)
            if durable is not None:
                workflow_store.restore(durable)
            else:
                workflow_store.restore(previous)
            raise PolicyViolation("Workflow changed concurrently; retry the decision")
        return result


def _recover_orphaned_workflow(job: JobState) -> WorkflowState | None:
    """Find a workflow created by a partial run of this source job.

    Source inspection writes its append-only observation and workflow before
    the model's optional follow-up/analysis turns. If a transient model error
    happens after that write, the next bounded retry can otherwise advance the
    source baseline and hide the real approval work. Match only a recent
    workflow for the same tenant and exact source, then let the caller attach
    it to the durable job.
    """
    candidates: list[WorkflowState] = []
    with _workflow_transition_lock:
        candidates.extend(workflow_store._runs.values())
    candidates.extend(list_workflows(limit=50))
    unique: dict[str, WorkflowState] = {
        state.workflow_id: state for state in candidates
    }
    matching = [
        state
        for state in unique.values()
        if state.tenant_id == job.tenant_id
        and state.evidence is not None
        and state.evidence.source_id == job.source_id
        and state.created_at >= job.created_at
    ]
    matching.sort(key=lambda state: state.created_at, reverse=True)
    return matching[0] if matching else None


async def _run_job(job_id: str) -> None:
    if not _claim_job_for_run(job_id):
        logger.info("Job %s was already claimed or completed", job_id)
        return
    job = _resolve_job(job_id)
    try:
        bound_query = (
            job.query
            if f'source_id "{job.source_id}"' in job.query
            else f'{job.query} Use the exact allowlisted source_id "{job.source_id}".'
        )
        if job.run_mode == "demo" and job.tenant_id is None:
            result = await run_agent_task(bound_query, job.user_id)
        elif job.tenant_id is None:
            result = await run_agent_task(bound_query, job.user_id, job.run_mode)
        else:
            result = await run_agent_task(
                bound_query,
                job.user_id,
                job.run_mode,
                tenant_id=job.tenant_id,
            )
        workflow_id = result.get("workflow_id")
        if not workflow_id:
            if result.get("change_detected") is False or result.get(
                "source_status"
            ) in {
                "baseline_established",
                "unchanged",
            }:
                job.status = "complete"
                job.model = result.get("model")
                job.execution_mode = result.get("execution_mode")
                job.tool_calls = result.get("tool_calls", [])
                job.event_count = int(result.get("event_count", 0))
                job.response = (
                    result.get("response") or "No material source change was found."
                )
                job.error = None
                _set_job(job)
                return
            raise RuntimeError("Agent completed without creating a workflow")
        state = _resolve_workflow(workflow_id)
        state.agent_trace = result.get("agent_trace")
        persist_workflow(state)
        job.status = (
            "needs_approval"
            if state.status.value == "needs_approval"
            else state.status.value
        )
        job.workflow_id = workflow_id
        job.model = result.get("model")
        job.execution_mode = result.get("execution_mode")
        job.tool_calls = result.get("tool_calls", [])
        job.event_count = int(result.get("event_count", 0))
        job.response = result.get("response", "")
        job.error = None
    except Exception as exc:
        recovered = _recover_orphaned_workflow(job)
        if recovered is not None:
            recovered.agent_trace = {
                **(recovered.agent_trace or {}),
                "execution_mode": "google_adk",
                "decision_copilot": {
                    "mode": "unavailable",
                    "reason": "Transient model failure; rerun the scan before approval.",
                },
            }
            persist_workflow(recovered)
            job.workflow_id = recovered.workflow_id
            job.status = (
                "needs_approval"
                if recovered.status.value == "needs_approval"
                else recovered.status.value
            )
            job.model = job.model or os.getenv("MODEL_NAME", "gemini-3.5-flash")
            job.execution_mode = job.execution_mode or "google_adk"
            job.response = (
                "Evidence captured; the workflow was preserved after a bounded "
                "agent retry. Human approval is still required."
            )
            job.error = None
            _set_job(job)
            logger.warning(
                "Recovered workflow %s for partially completed job %s after %s",
                recovered.workflow_id,
                job.job_id,
                type(exc).__name__,
            )
            return
        # The public judge console is an explicitly synthetic, identity-free
        # lane.  Keep it reviewable when a real Gemini turn is temporarily
        # quota-limited or unavailable, while leaving signed/monitor runs
        # fail-closed.  The fallback is labelled in the durable job and
        # workflow records; it never claims a Gemini execution occurred.
        if _complete_demo_fallback(job, exc):
            _set_job(job)
            return
        logger.exception("Async Driftline job failed")
        if job.run_attempts < MAX_JOB_ATTEMPTS:
            # Returning a retriable state lets Cloud Tasks redeliver the same
            # deterministic task. The durable claim is cleared only after the
            # failed attempt has been recorded, so a duplicate delivery cannot
            # run concurrently with the retry.
            job.status = "queued"
            job.claim_id = None
            job.error = (
                f"Transient agent failure; retry {job.run_attempts}/{MAX_JOB_ATTEMPTS}."
            )
        else:
            job.status = "failed"
            job.error = "The agent job failed after bounded retries."
            try:
                persist_job_failure(
                    {
                        "job_id": job.job_id,
                        "workflow_id": job.workflow_id,
                        "tenant_id": job.tenant_id,
                        "attempts": job.run_attempts,
                        "failed_at": utc_now(),
                    }
                )
            except Exception:
                logger.exception("Unable to persist terminal failure for %s", job.job_id)
    _set_job(job)


def _complete_demo_fallback(job: JobState, error: Exception) -> bool:
    """Create the bounded synthetic replay when the public demo's ADK turn fails.

    This is intentionally narrow: only tenantless ``demo`` jobs with a
    static allowlisted source can use it.  Signed tenant jobs and monitor
    runs must surface the real failure instead of hiding an unavailable
    Gemini/connector execution behind synthetic state.
    """
    if job.run_mode != "demo" or job.tenant_id is not None:
        return False
    match = re.search(r'allowlisted source_id "([^"]+)"', job.query)
    source_id = match.group(1) if match else "public/pricing"
    definition = source_definition(source_id)
    if not definition or definition.get("dynamic") == "true":
        return False
    state = workflow_store.start_demo(
        source_id=source_id,
        source_name=definition["name"],
        source_url=definition["url"],
        before_text=definition["before"],
        after_text=definition["after"],
        snapshot_label=f"Synthetic replay fixture · {source_id}",
        data_mode="synthetic_demo",
    )
    persist_workflow(state)
    job.status = "needs_approval"
    job.workflow_id = state.workflow_id
    job.model = "synthetic"
    job.execution_mode = "deterministic_demo_fallback"
    job.tool_calls = []
    job.event_count = 0
    job.response = (
        "Gemini was temporarily unavailable; this is a labelled synthetic "
        "replay so the approval and evidence workflow remains reviewable."
    )
    job.error = None
    logger.warning(
        "Demo ADK unavailable; served labelled synthetic replay (%s)",
        type(error).__name__,
    )
    return True


def _schedule_local_job(job: JobState) -> None:
    task = asyncio.create_task(_run_job(job.job_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _start_job(
    *,
    query: str,
    user_id: str,
    run_mode: str,
    background_tasks: BackgroundTasks,
    tenant_id: str | None = None,
    source_id: str = "public/pricing",
    retry_of: str | None = None,
) -> JobState:
    job = JobState(
        job_id=f"job-{uuid4().hex[:12]}",
        query=query,
        user_id=user_id,
        tenant_id=tenant_id,
        run_mode=run_mode,
        source_id=source_id,
        retry_of=retry_of,
    )
    _set_job(job)
    try:
        if _tasks_enabled():
            _enqueue_cloud_task(job)
        else:
            background_tasks.add_task(_run_job, job.job_id)
    except Exception:
        logger.exception("Unable to enqueue async Driftline job")
        job.status = "failed"
        job.error = (
            "Async execution is not configured. Check the Cloud Tasks deployment."
        )
        _set_job(job)
    return job


def _inflight_monitor_job_exists(
    source_id: str,
    tenant_id: str | None,
) -> bool:
    """Return whether this source already has an active monitor job.

    Scheduler delivery is at-least-once. Checking both the instance cache and
    the durable job ledger prevents a duplicate tick (or a second Cloud Run
    instance) from launching another model call for the same source.
    """
    try:
        with _jobs_lock:
            candidates = list(_jobs.values())
        candidates.extend(list_jobs(limit=50))
    except Exception:
        # A ledger outage must not make the scheduler fan out unbounded work.
        logger.exception("Unable to inspect in-flight monitor jobs")
        return True
    return any(
        job.run_mode == "monitor"
        and job.source_id == source_id
        and job.tenant_id == tenant_id
        and job.status in {"queued", "running"}
        for job in candidates
    )


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "driftline-agent",
        "persistence": os.getenv("DRIFTLINE_PERSISTENCE", "memory"),
        "async_jobs": _tasks_enabled(),
    }


@app.get("/api/auth/config")
def get_auth_config() -> dict[str, object]:
    """Expose only the public Google Identity Services configuration.

    A web OAuth client id is not a credential. Returning it lets the hosted
    console offer an actual operator sign-in without shipping a secret or
    weakening the anonymous packet-safe judge lane. The API still validates
    the resulting short-lived Google ID token and durable tenant membership on
    every signed request.
    """
    audience = os.getenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "").strip()
    return {
        "enabled": bool(audience),
        "client_id": audience or None,
        "mode": "google_oidc" if audience else "unavailable",
        "anonymous_lane": "packet_only",
        "credential_values_exposed": False,
    }


def _salesforce_secret_name(tenant_id: str) -> str:
    """Return the same tenant connector secret name used by every adapter."""
    return tenant_connector_secret_name(tenant_id, "salesforce")


def _save_salesforce_state(state: str, payload: dict[str, object]) -> None:
    expires_at = float(payload.get("expires_at", 0))
    with _salesforce_oauth_lock:
        _salesforce_oauth_states[state] = payload
        # Keep the local fallback bounded and remove expired state eagerly.
        for key, item in list(_salesforce_oauth_states.items()):
            if float(item.get("expires_at", 0)) < expires_at - 900:
                _salesforce_oauth_states.pop(key, None)
    persist_salesforce_oauth_state(state, payload)


def _consume_salesforce_state(state: str) -> dict[str, object] | None:
    with _salesforce_oauth_lock:
        payload = _salesforce_oauth_states.pop(state, None)
    durable = consume_salesforce_oauth_state(state)
    # Firestore is authoritative in the hosted deployment. Never resurrect a
    # consumed/deleted OAuth state from another instance's local memory.
    result = (
        durable
        if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
        else durable or payload
    )
    if not result or float(result.get("expires_at", 0)) < datetime.now(UTC).timestamp():
        return None
    return result


@app.post("/api/connectors/salesforce/start")
def start_salesforce_connection(request: SalesforceConnectRequest) -> dict[str, object]:
    """Start a tenant-scoped Salesforce OAuth authorization-code flow."""
    identity = _verify_approval_mode(
        "salesforce-connect",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    config = SalesforceConfig.from_env()
    try:
        config.validate_oauth()
        tenant_id = identity["tenant_id"]
        state = secrets.token_urlsafe(32)
        # Salesforce enforces PKCE on this External Client App. Keep the
        # verifier in the expiring server-side state record; only the S256
        # challenge is sent through the browser.
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode("ascii")).digest()
            )
            .rstrip(b"=")
            .decode("ascii")
        )
        _save_salesforce_state(
            state,
            {
                "tenant_id": tenant_id,
                "operator": request.operator.strip(),
                "subject": identity.get("subject", ""),
                "email": identity.get("email", ""),
                "expires_at": datetime.now(UTC).timestamp() + 600,
                "code_verifier": code_verifier,
            },
        )
        return {
            "status": "authorization_required",
            "tenant_id": tenant_id,
            "authorize_url": salesforce_authorization_url(
                config, state, code_challenge=code_challenge
            ),
            "expires_in_seconds": 600,
            "scopes": config.scope.split(),
            "disclosure": "The callback stores only a tenant-scoped refresh-token reference in Secret Manager; no Salesforce records are copied.",
        }
    except (ConnectorError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/connectors/salesforce/oauth/callback")
def salesforce_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> Response:
    """Consume a one-time callback and persist only safe connection metadata."""
    if error:
        return PlainTextResponse(
            "Salesforce authorization was declined.", status_code=400
        )
    if not code or not state:
        return PlainTextResponse("Salesforce callback is incomplete.", status_code=400)
    callback_state = _consume_salesforce_state(state)
    if callback_state is None:
        return PlainTextResponse(
            "Salesforce authorization expired or was already used.", status_code=400
        )
    config = SalesforceConfig.from_env()
    try:
        result = exchange_salesforce_code(
            config,
            code,
            code_verifier=str(callback_state.get("code_verifier", "")),
        )
        refresh_token = str(result.get("refresh_token", ""))
        if not refresh_token:
            raise ConnectorError("salesforce_refresh_token_missing")
        tenant_id = validate_tenant_id(str(callback_state["tenant_id"]))
        tenant = load_tenant(tenant_id)
        if str((tenant or {}).get("status", "")).casefold() != "active":
            raise ConnectorError("salesforce_tenant_inactive")
        secret_name = _salesforce_secret_name(tenant_id)
        secret_version = _write_tenant_secret(tenant_id, secret_name, refresh_token) or "latest"
        binding = persist_connector_binding(
            {
                "tenant_id": tenant_id,
                "connector": "salesforce",
                "secret_name": secret_name,
                "status": "active",
                "scope": "tenant_bound_oauth_refresh_token",
                "credential_id": f"cred-{tenant_id}-salesforce",
                "secret_backend": "google_secret_manager",
                "secret_reference_scope": "exact_tenant_connector_secret",
                # Salesforce is deliberately read-only. Do not inherit the
                # compatibility ``runtime`` scope used by older connectors;
                # the OAuth callback must mint only the concrete operation
                # the read probe can request.
                "allowed_operations": normalize_allowed_operations(
                    "salesforce", default="read_only"
                ),
                "lease_seconds": 300,
                "secret_version": secret_version,
                "verified_at": utc_now(),
                "configured_by": callback_state.get("email", "") or "salesforce_oauth",
                "updated_at": utc_now(),
            }
        )
        persist_salesforce_connection(
            {
                "tenant_id": tenant_id,
                "instance_url": str(result.get("instance_url", "")).rstrip("/"),
                "secret_name": secret_name,
                "scopes": config.scope.split(),
                "status": "connected_read_only",
                "connected_at": utc_now(),
                "operator_email": callback_state.get("email", ""),
            }
        )
        persist_tenant_audit_event(
            {
                "tenant_id": tenant_id,
                "event_type": "salesforce_connected_read_only",
                "connector": "salesforce",
                "status": "active",
                "secret_name": binding["secret_name"],
                "actor": callback_state.get("email", "") or "salesforce_oauth",
            }
        )
        return PlainTextResponse(
            "Salesforce connected to Driftline in read-only mode. You can close this tab."
        )
    except (ConnectorError, ValueError) as exc:
        logger.warning("Salesforce OAuth callback failed: %s", str(exc))
        return PlainTextResponse(
            "Driftline could not finish Salesforce setup. Provision the tenant Secret Manager secret and retry.",
            status_code=503,
        )


@app.post("/api/connectors/salesforce/health")
def salesforce_health(request: SalesforceHealthRequest) -> dict[str, object]:
    """Run aggregate-only read probes for the authenticated tenant."""
    identity = _verify_approval_mode(
        "salesforce-health",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if not _reserve_connector_call(identity["tenant_id"]):
        raise HTTPException(
            status_code=429,
            detail="Connector read quota reached; retry later.",
        )
    tenant_id = identity["tenant_id"]
    connection = load_salesforce_connection(tenant_id)
    binding = load_connector_binding(tenant_id, "salesforce")
    expected_secret = _salesforce_secret_name(tenant_id)
    if (
        not connection
        or connection.get("status") != "connected_read_only"
        or not binding
        or binding.get("status") != "active"
        or binding.get("secret_name") != expected_secret
    ):
        raise HTTPException(
            status_code=409, detail="Salesforce is not connected for this tenant"
        )
    config = SalesforceConfig.from_env()
    try:
        refresh_token = resolve_tenant_credential(
            tenant_id,
            "salesforce",
            operation="read_context",
            secret_reader=read_secret,
        ).value
        token = refresh_salesforce_token(config, refresh_token)
        client = SalesforceReadOnlyClient(
            config,
            access_token=str(token["access_token"]),
            instance_url=str(connection["instance_url"]),
        )
        result = client.health_summary()
        return {"tenant_id": tenant_id, **result}
    except (ConnectorError, CredentialBrokerError) as exc:
        logger.warning("Salesforce health probe failed: %s", str(exc))
        raise HTTPException(
            status_code=503, detail="Salesforce read probe failed"
        ) from exc


@app.delete("/api/connectors/salesforce")
def disconnect_salesforce(request: SalesforceConnectRequest) -> dict[str, object]:
    """Revoke Driftline's connection metadata; token deletion stays recoverable."""
    identity = _verify_approval_mode(
        "salesforce-disconnect",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    binding = load_connector_binding(tenant_id, "salesforce")
    if binding:
        persist_connector_binding(
            {
                **binding,
                "tenant_id": tenant_id,
                "connector": "salesforce",
                "status": "revoked",
                "revoked_at": utc_now(),
                "revoked_by": identity.get("email") or identity.get("identity"),
            }
        )
    delete_salesforce_connection(tenant_id)
    persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": "salesforce_disconnected",
            "connector": "salesforce",
            "status": "revoked",
            "secret_name": (binding or {}).get("secret_name", _salesforce_secret_name(tenant_id)),
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": "disconnected",
        "tenant_id": tenant_id,
        "follow_up": "Revoke the Driftline app in Salesforce and delete the tenant secret during offboarding.",
    }


@app.get("/api/sources")
def get_sources(
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Expose public fixtures or the caller's signed tenant registry."""
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for tenant sources"
            )
        identity = _verify_approval_mode(
            "sources:list",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    bound_tenant = identity.get("tenant_id") if identity else None
    return {"sources": list_allowlisted_sources(bound_tenant)}


@app.post("/api/operator/sources")
def onboard_operator_source(request: SourceOnboardingRequest) -> dict[str, object]:
    """Add one exact public source through an authenticated operator lane."""
    approval_identity = _verify_approval_mode(
        f"source-onboarding:{request.source_id}",
        request.registered_by,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    try:
        definition = register_operator_source(
            source_id=request.source_id,
            name=request.name,
            category=request.category,
            change_type=request.change_type,
            url=request.url,
            owner=request.owner,
            cadence=request.cadence,
            freshness_sla_hours=request.freshness_sla_hours,
            parser=request.parser,
            registered_by=request.registered_by,
            tenant_id=approval_identity["tenant_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # Production onboarding should prove that the exact URL is readable and
    # establish its first append-only baseline in the same operator action.
    # Keep local/synthetic test mode metadata-only, and never turn a fetch
    # failure into a false change: inspect_allowlisted_source returns an
    # explicit source_fetch_failed result for the scheduler to retry.
    baseline: dict[str, object] | None = None
    if os.getenv("DRIFTLINE_SOURCE_MODE", "synthetic").casefold() == "public":
        baseline = inspect_allowlisted_source(
            request.source_id,
            tenant_id=approval_identity["tenant_id"],
            force_replay=False,
        )
    return {
        "status": "registered",
        "source": {
            key: value
            for key, value in definition.items()
            if key not in {"registered_by", "registered_at"}
        },
        "approval_identity": approval_identity,
        "baseline": baseline,
        "next_step": (
            "Scheduler monitoring is active; the first baseline was established."
            if baseline and baseline.get("status") == "baseline_established"
            else "Scheduler will retry this source until a bounded baseline is established."
            if baseline and baseline.get("status") == "source_fetch_failed"
            else "Enable public source mode, then run a signed monitor tick to establish the baseline."
        ),
    }


@app.get("/api/monitor/registry")
def get_monitor_registry(
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return source freshness and allowlist health without fetching sources."""
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for monitor registry"
            )
        identity = _verify_approval_mode(
            "monitor-registry",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    sources = source_registry_health(
        tenant_id=identity.get("tenant_id") if identity else None
    )
    return {
        "append_only": True,
        "generated_at": utc_now(),
        "sources": sources,
        "summary": {
            "total": len(sources),
            "healthy": sum(item["status"] == "healthy" for item in sources),
            "stale": sum(item["status"] == "stale" for item in sources),
            "needs_baseline": sum(
                item["status"] == "needs_baseline" for item in sources
            ),
            "synthetic_only": sum(
                item["status"] == "synthetic_only" for item in sources
            ),
            "source_failed": sum(
                item["status"] == "source_failed" for item in sources
            ),
        },
    }


@app.get("/api/ops/summary")
def get_ops_summary(
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Expose bounded operator health without cross-tenant record counts."""
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for tenant metrics"
            )
        identity = _verify_approval_mode(
            "ops:summary",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    with _jobs_lock:
        job_records = list(_jobs.values())
    jobs = [
        job
        for job in _merge_durable_records(
            job_records, list_jobs, limit=20, key=lambda item: item.job_id
        )
        if _visible_tenant_record(job, identity)
    ]
    workflow_records = list(workflow_store._runs.values())
    workflows = [
        state
        for state in _merge_durable_records(
            workflow_records,
            list_workflows,
            limit=20,
            key=lambda item: item.workflow_id,
        )
        if _visible_tenant_record(state, identity)
    ]
    source_health = source_registry_health(
        tenant_id=identity.get("tenant_id") if identity else None
    )
    job_failures = (
        list_job_failures(identity["tenant_id"], limit=20)
        if identity is not None
        else []
    )
    connector_names = ("jira", "confluence", "slack", "github")
    return {
        "generated_at": utc_now(),
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "local"),
        "persistence": os.getenv("DRIFTLINE_PERSISTENCE", "memory"),
        "async_jobs": _tasks_enabled(),
        "model": os.getenv("MODEL_NAME", "gemini-3.5-flash"),
        "guardrails": {
            "agent_max_calls": AGENT_MAX_CALLS,
            "agent_window_seconds": AGENT_WINDOW_SECONDS,
            "demo_max_mutations": DEMO_MAX_MUTATIONS,
            "connector_max_calls": CONNECTOR_MAX_CALLS,
            "connector_window_seconds": CONNECTOR_WINDOW_SECONDS,
            "multimodal_max_calls": MULTIMODAL_MAX_CALLS,
            "multimodal_window_seconds": MULTIMODAL_WINDOW_SECONDS,
            "monitor_max_sources": _positive_int("DRIFTLINE_MONITOR_MAX_SOURCES", 5),
            "tenant_quota_enforcement": (
                "firestore_transaction"
                if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold()
                == "firestore"
                else "process_local"
            ),
            # Public summaries deliberately omit tenant policy; signed
            # operators receive only their own bounded control-plane values.
            "tenant_policy": (
                load_tenant_policy(identity["tenant_id"])
                if identity is not None
                else None
            ),
        },
        "approval_security": {
            "public_demo_packet_only": True,
            "configured_mode": os.getenv("DRIFTLINE_APPROVAL_MODE", "demo"),
            "signed_approvals_enabled": os.getenv(
                "DRIFTLINE_SIGNED_APPROVALS_ENABLED", "false"
            ).casefold()
            == "true",
            "google_oidc_operator_enabled": bool(
                os.getenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "").strip()
            ),
            "external_writes_require_signed": True,
            "credential_model": {
                "tenant_bound": True,
                "legacy_global_fallback": os.getenv(
                    "DRIFTLINE_ALLOW_LEGACY_GLOBAL_CONNECTOR_SECRETS", "false"
                ).casefold()
                == "true",
                "binding_route": "/api/connectors/{connector}/binding",
                "metadata_collection": "driftline_connector_bindings",
                "canonical_binding_path": "driftline_tenants/{tenant}/credentials/{connector}",
                "namespace_schema_version": 1,
                "namespace_migration": "scripts/migrate_tenant_credential_bindings.py",
                "strict_namespace_required": os.getenv(
                    "DRIFTLINE_REQUIRE_TENANT_CREDENTIAL_NAMESPACE", "false"
                ).casefold()
                == "true",
                "broker_inventory_route": "/api/connectors/credentials",
                "broker_access_route": "/api/connectors/credentials/access",
                "broker_access_collection": "driftline_credential_access_events",
                "resolution": "short_lived_tenant_scoped_lease",
                "lease_seconds": 300,
                "operation_scopes": {
                    connector: allowed_operations(connector)
                    for connector in sorted(
                        ("jira", "confluence", "slack", "github", "salesforce")
                    )
                },
                "profile_route": "/api/connectors/{connector}/profile",
                "profile_collection": "driftline_tenant_connector_profiles",
                "deployment_target_fallback": os.getenv(
                    "DRIFTLINE_ALLOW_DEPLOYMENT_CONNECTOR_TARGET_FALLBACK",
                    "false",
                ).casefold()
                == "true",
                "tenant_collection": "driftline_tenants",
                "membership_collection": "driftline_tenant_memberships",
            },
            "tenant_auth": {
                # Hosted Firestore membership records are authoritative.  A
                # static environment mapping is only a local/bootstrap
                # compatibility path and must not be required for new tenants.
                "configured": (
                    os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold()
                    == "firestore"
                    or bool(os.getenv("DRIFTLINE_TENANT_MEMBERS", "").strip())
                ),
                "membership_source": (
                    "firestore"
                    if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold()
                    == "firestore"
                    else "environment_bootstrap"
                ),
                "static_operator_allowlist": bool(
                    os.getenv("DRIFTLINE_OPERATOR_EMAILS", "").strip()
                ),
                "durable_memberships": True,
                "default_tenant": os.getenv(
                    "DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo"
                ),
                "role_model": ["viewer", "operator", "owner"],
            },
        },
        "jobs": {
            "total": len(jobs),
            "dead_lettered": len(job_failures),
            "by_status": {
                status: sum(job.status == status for job in jobs)
                for status in {job.status for job in jobs}
            },
        },
        "workflows": {
            "total": len(workflows),
            "by_status": {
                status: sum(state.status.value == status for state in workflows)
                for status in {state.status.value for state in workflows}
            },
        },
        "connectors": {
            name: os.getenv(f"DRIFTLINE_{name.upper()}_ENABLED", "false").casefold()
            == "true"
            for name in connector_names
        },
        "crm": {"salesforce": salesforce_readiness()},
        "source_health": source_health,
    }


@app.post("/api/connectors/context/summary")
def get_connector_context_summary(request: ConnectorContextRequest) -> dict[str, object]:
    """Read bounded internal context for an authenticated operator.

    The public demo cannot call this route: it requires the same signed/OIDC
    boundary used for configured connector writes. Results are aggregate-only
    and intentionally not copied into public workflow state or model prompts.
    """
    identity = _verify_approval_mode(
        "connector-context-summary",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if not _reserve_connector_call(identity["tenant_id"]):
        raise HTTPException(
            status_code=429,
            detail="Connector read quota reached; retry later.",
        )
    summaries = _connector_context_info(identity["tenant_id"])
    return {
        "status": "ok",
        "tenant_id": identity["tenant_id"],
        "role": identity["role"],
        "generated_at": utc_now(),
        "context_contract": {
            "purpose": "ground downstream impact planning with bounded internal workload context",
            "redaction": "aggregate_metadata_only",
            "persisted": False,
            "retention": "request-scoped; no source bodies or message text retained",
            "user_input_scope": "none; connector targets come only from the caller's durable tenant profile",
        },
        "connectors": summaries,
    }


@app.post("/api/connectors/{connector}/binding")
def register_connector_binding(
    connector: str, request: ConnectorBindingRequest
) -> dict[str, object]:
    """Register one deterministic tenant Secret Manager binding.

    The runtime never accepts a secret value or arbitrary secret name. An
    infrastructure operator pre-provisions the deterministic secret, then this
    signed owner route verifies that it is readable and activates the binding.
    """
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    identity = _verify_approval_mode(
        f"connector-binding:{safe_connector}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    try:
        scoped_operations = normalize_allowed_operations(
            safe_connector, request.allowed_operations
        )
    except CredentialBrokerError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    secret_name = tenant_connector_secret_name(tenant_id, safe_connector)
    existing_binding = load_connector_binding(tenant_id, safe_connector) or {}
    status = "active"
    secret_version = "latest"
    try:
        if not _read_tenant_secret(tenant_id, secret_name).strip():
            status = "pending_secret"
        else:
            # Pin the binding to the exact Secret Manager version resolved at
            # verification time. If a local emulator/test double cannot
            # expose a concrete version, ``latest`` remains an explicit
            # compatibility marker and the next owner verification can pin it.
            try:
                secret_version = _tenant_secret_version(tenant_id, secret_name)
            except ConnectorError:
                secret_version = "latest"
    except ConnectorError:
        status = "pending_secret"
    persist_tenant(
        {
            "tenant_id": tenant_id,
            "status": "active",
            "provisioning": "owner_connector_binding",
            "configured_by": identity.get("email") or identity.get("identity"),
            "updated_at": utc_now(),
        }
    )
    if identity.get("email"):
        persist_tenant_membership(
            {
                "tenant_id": tenant_id,
                "email": identity["email"],
                "role": identity.get("role", "owner"),
                "status": "active",
                "source": "verified_operator_binding",
            }
        )
    binding = persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "secret_name": secret_name,
            "status": status,
            "scope": "tenant_bound_connector_credential",
            "credential_id": existing_binding.get("credential_id")
            or f"cred-{tenant_id}-{safe_connector}",
            "secret_backend": "google_secret_manager",
            "secret_reference_scope": "exact_tenant_connector_secret",
            "allowed_operations": scoped_operations,
            "lease_seconds": 300,
            "secret_version": secret_version,
            "verified_at": utc_now() if status == "active" else None,
            "configured_by": identity.get("email") or identity.get("identity"),
            "updated_at": utc_now(),
        }
    )
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": (
                "connector_binding_activated"
                if status == "active"
                else "connector_binding_pending"
            ),
            "connector": safe_connector,
            "status": status,
            "secret_name": secret_name,
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": status,
        "tenant_id": tenant_id,
        "connector": safe_connector,
        "secret_name": secret_name,
        "credential_namespace": binding.get(
            "credential_namespace",
            tenant_credential_namespace(tenant_id, safe_connector)
            if os.getenv("GOOGLE_CLOUD_PROJECT")
            else None,
        ),
        "secret_version": binding.get("secret_version", "latest"),
        "verified_at": binding.get("verified_at"),
        "scope": binding["scope"],
        "credential_value_accepted": False,
        "audit_event_id": audit_event["event_id"],
        "next_step": (
            "Binding is active; connector calls will use this tenant secret."
            if status == "active"
            else "Provision the deterministic secret, then repeat this signed owner request."
        ),
    }


@app.post("/api/connectors/{connector}/credential-enrollment")
def start_connector_credential_enrollment(
    connector: str, request: ConnectorCredentialEnrollmentRequest
) -> dict[str, object]:
    """Start a short-lived tenant credential enrollment handoff.

    The response is intentionally a provisioning contract, not a credential
    upload form. The owner provisions the exact deterministic Secret Manager
    secret out of band, then completes this enrollment to verify and activate
    the binding. New sessions default to read-only operations so downstream
    writes require an explicit owner scope grant.
    """
    try:
        safe_connector = validate_connector_name(connector)
        scoped_operations = normalize_allowed_operations(
            safe_connector, request.allowed_operations, default="read_only"
        )
    except (ValueError, CredentialBrokerError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    identity = _verify_approval_mode(
        f"credential-enrollment:{safe_connector}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    existing = load_connector_binding(tenant_id, safe_connector)
    if existing and str(existing.get("status", "")).casefold() == "active":
        raise HTTPException(
            status_code=409,
            detail="connector_binding_active_use_rotation",
        )
    created_at = datetime.now(UTC)
    expires_at = created_at.timestamp() + 900
    enrollment_id = f"enroll-{uuid4().hex}"
    secret_name = tenant_connector_secret_name(tenant_id, safe_connector)
    enrollment = persist_credential_enrollment(
        {
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "enrollment_id": enrollment_id,
            "status": "awaiting_secret",
            "secret_name": secret_name,
            "credential_namespace": (
                tenant_credential_namespace(tenant_id, safe_connector)
                if os.getenv("GOOGLE_CLOUD_PROJECT")
                else None
            ),
            "allowed_operations": scoped_operations,
            "requested_by": identity.get("email") or identity.get("identity"),
            "created_at": created_at.isoformat(),
            "expires_at": datetime.fromtimestamp(expires_at, UTC).isoformat(),
            "updated_at": created_at.isoformat(),
        }
    )
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": "credential_enrollment_started",
            "connector": safe_connector,
            "enrollment_id": enrollment_id,
            "status": "awaiting_secret",
            "allowed_operations": scoped_operations,
            "secret_name": secret_name,
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": enrollment["status"],
        "tenant_id": tenant_id,
        "connector": safe_connector,
        "enrollment_id": enrollment_id,
        "secret_name": secret_name,
        "credential_namespace": enrollment.get("credential_namespace"),
        "allowed_operations": scoped_operations,
        "expires_at": enrollment["expires_at"],
        "expires_in_seconds": 900,
        "credential_value_exposed": False,
        "audit_event_id": audit_event["event_id"],
        "next_step": (
            "Provision a version in this exact tenant secret out of band, then "
            "call the enrollment completion route. The request never accepts a token value."
        ),
    }


@app.post("/api/connectors/{connector}/credential-enrollment/{enrollment_id}/complete")
def complete_connector_credential_enrollment(
    connector: str,
    enrollment_id: str,
    request: ConnectorBindingRequest,
) -> dict[str, object]:
    """Verify an out-of-band secret and atomically activate its tenant binding."""
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    identity = _verify_approval_mode(
        f"credential-enrollment-complete:{safe_connector}:{enrollment_id}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    enrollment = load_credential_enrollment(tenant_id, safe_connector, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=404, detail="credential_enrollment_not_found")
    if str(enrollment.get("status", "")).casefold() == "completed":
        return {
            "status": "active",
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "enrollment_id": enrollment_id,
            "secret_name": enrollment.get("secret_name"),
            "secret_version": enrollment.get("secret_version", "latest"),
            "allowed_operations": enrollment.get("allowed_operations", []),
            "credential_value_exposed": False,
            "already_completed": True,
        }
    try:
        expiry = datetime.fromisoformat(str(enrollment.get("expires_at", "")))
    except ValueError:
        expiry = datetime.min.replace(tzinfo=UTC)
    if expiry <= datetime.now(UTC):
        expired = persist_credential_enrollment(
            {
                **enrollment,
                "status": "expired",
                "updated_at": utc_now(),
            }
        )
        raise HTTPException(
            status_code=410,
            detail={
                "error": "credential_enrollment_expired",
                "enrollment_id": expired["enrollment_id"],
            },
        )
    secret_name = tenant_connector_secret_name(tenant_id, safe_connector)
    try:
        if not _read_tenant_secret(tenant_id, secret_name).strip():
            raise ConnectorError("credential_empty")
        try:
            secret_version = _tenant_secret_version(tenant_id, secret_name)
        except ConnectorError:
            secret_version = "latest"
    except ConnectorError:
        return {
            "status": "awaiting_secret",
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "enrollment_id": enrollment_id,
            "secret_name": secret_name,
            "allowed_operations": enrollment.get("allowed_operations", []),
            "credential_value_exposed": False,
            "next_step": "Add a version to the exact tenant secret, then retry completion.",
        }
    try:
        scoped_operations = normalize_allowed_operations(
            safe_connector,
            list(enrollment.get("allowed_operations") or []),
            default="read_only",
        )
    except CredentialBrokerError as exc:
        raise HTTPException(status_code=409, detail="credential_scope_invalid") from exc
    now = utc_now()
    binding = persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "secret_name": secret_name,
            "status": "active",
            "scope": "tenant_bound_connector_credential",
            "credential_id": f"cred-{tenant_id}-{safe_connector}",
            "secret_backend": "google_secret_manager",
            "secret_reference_scope": "exact_tenant_connector_secret",
            "allowed_operations": scoped_operations,
            "lease_seconds": 300,
            "secret_version": secret_version,
            "enrollment_id": enrollment_id,
            "verified_at": now,
            "configured_by": identity.get("email") or identity.get("identity"),
            "updated_at": now,
        }
    )
    completed = persist_credential_enrollment(
        {
            **enrollment,
            "status": "completed",
            "secret_version": secret_version,
            "completed_at": now,
            "completed_by": identity.get("email") or identity.get("identity"),
            "updated_at": now,
        }
    )
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": "credential_enrollment_completed",
            "connector": safe_connector,
            "enrollment_id": enrollment_id,
            "status": "active",
            "secret_name": secret_name,
            "secret_version": secret_version,
            "allowed_operations": scoped_operations,
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": binding["status"],
        "tenant_id": tenant_id,
        "connector": safe_connector,
        "enrollment_id": completed["enrollment_id"],
        "secret_name": binding["secret_name"],
        "secret_version": binding.get("secret_version", "latest"),
        "allowed_operations": scoped_operations,
        "credential_namespace": binding.get("credential_namespace"),
        "credential_value_exposed": False,
        "audit_event_id": audit_event["event_id"],
    }


@app.post("/api/connectors/{connector}/binding/revoke")
def revoke_connector_binding(
    connector: str, request: ConnectorBindingRequest
) -> dict[str, object]:
    """Revoke one tenant binding without deleting or returning its secret."""
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    identity = _verify_approval_mode(
        f"connector-binding-revoke:{safe_connector}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    binding = load_connector_binding(tenant_id, safe_connector)
    if binding is None:
        raise HTTPException(status_code=404, detail="connector_binding_not_found")
    revoked = persist_connector_binding(
        {
            **binding,
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "status": "revoked",
            "revoked_at": utc_now(),
            "revoked_by": identity.get("email") or identity.get("identity"),
        }
    )
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": "connector_binding_revoked",
            "connector": safe_connector,
            "status": "revoked",
            "secret_name": revoked["secret_name"],
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": "revoked",
        "tenant_id": tenant_id,
        "connector": safe_connector,
        "secret_name": revoked["secret_name"],
        "credential_namespace": revoked.get("credential_namespace"),
        "credential_value_exposed": False,
        "audit_event_id": audit_event["event_id"],
        "follow_up": (
            "Revoke the provider token and disable or rotate the Secret Manager "
            "version during offboarding; re-run the signed owner binding route "
            "only after a replacement secret is ready."
        ),
    }


@app.post("/api/connectors/{connector}/binding/rotate")
def rotate_connector_binding(
    connector: str, request: ConnectorBindingRotationRequest
) -> dict[str, object]:
    """Begin an owner-controlled credential rotation without accepting a secret.

    Rotation is a two-step control-plane operation: this endpoint moves the
    binding to ``rotation_pending`` so connector calls fail closed, then an
    infrastructure operator adds a new version to the deterministic Secret
    Manager secret and repeats the normal binding verification route.  The
    runtime never receives or returns a credential value.
    """
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    identity = _verify_approval_mode(
        f"connector-binding-rotate:{safe_connector}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    binding = load_connector_binding(tenant_id, safe_connector)
    if binding is None:
        raise HTTPException(status_code=404, detail="connector_binding_not_found")
    current_status = str(binding.get("status", "")).casefold()
    if current_status not in {"active", "rotation_pending"}:
        raise HTTPException(
            status_code=409,
            detail="connector_binding_not_rotatable",
        )
    if current_status == "rotation_pending" and binding.get("rotation_id"):
        return {
            "status": "rotation_pending",
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "rotation_id": binding["rotation_id"],
            "secret_name": binding["secret_name"],
            "credential_namespace": binding.get("credential_namespace"),
            "credential_value_exposed": False,
            "already_pending": True,
            "next_step": (
                "Add a replacement version to this deterministic Secret Manager secret, "
                "then repeat the signed owner binding request to verify and reactivate it."
            ),
        }
    now = utc_now()
    rotation_id = f"rotation-{uuid4().hex}"
    pending = persist_connector_binding(
        {
            **binding,
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "status": "rotation_pending",
            "rotation_id": rotation_id,
            "rotation_reason": request.reason.strip(),
            "rotation_started_at": now,
            "rotation_started_by": identity.get("email") or identity.get("identity"),
            "updated_at": now,
        }
    )
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": "connector_binding_rotation_requested",
            "connector": safe_connector,
            "status": "rotation_pending",
            "rotation_id": rotation_id,
            "reason": request.reason.strip(),
            "secret_name": pending["secret_name"],
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": "rotation_pending",
        "tenant_id": tenant_id,
        "connector": safe_connector,
        "rotation_id": rotation_id,
        "secret_name": pending["secret_name"],
        "credential_namespace": pending.get("credential_namespace"),
        "credential_value_exposed": False,
        "audit_event_id": audit_event["event_id"],
        "next_step": (
            "Add a replacement version to this deterministic Secret Manager secret, "
            "then repeat the signed owner binding request to verify and reactivate it."
        ),
    }


@app.post("/api/connectors/{connector}/profile")
def register_connector_profile(
    connector: str, request: ConnectorProfileRequest
) -> dict[str, object]:
    """Persist one tenant's bounded, non-secret connector destination."""
    try:
        safe_connector = validate_connector_name(connector)
        settings = validate_connector_profile(safe_connector, request.settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    identity = _verify_approval_mode(
        f"connector-profile:{safe_connector}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    profile = persist_connector_profile(
        {
            "tenant_id": tenant_id,
            "connector": safe_connector,
            "settings": settings,
            "updated_at": utc_now(),
        }
    )
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": "connector_profile_updated",
            "connector": safe_connector,
            "setting_keys": sorted(settings),
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": "active",
        "tenant_id": tenant_id,
        "connector": safe_connector,
        "settings": profile["settings"],
        "credential_values_accepted": False,
        "audit_event_id": audit_event["event_id"],
    }


@app.get("/api/connectors/{connector}/profile")
def get_connector_profile(
    connector: str,
    operator: str,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return the caller's non-secret profile, never a credential value."""
    try:
        safe_connector = validate_connector_name(connector)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    identity = _verify_approval_mode(
        f"connector-profile-read:{safe_connector}",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    profile = load_connector_profile(identity["tenant_id"], safe_connector)
    return {
        "tenant_id": identity["tenant_id"],
        "connector": safe_connector,
        "status": (profile or {}).get("status", "not_configured"),
        "settings": (profile or {}).get("settings", {}),
        "credential_values_exposed": False,
    }


@app.get("/api/tenants")
def get_tenant_metadata(
    operator: str,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return metadata for the caller's tenant, never credentials or secrets."""
    identity = _verify_approval_mode(
        "tenant-metadata",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    tenant = load_tenant(identity["tenant_id"]) or {
        "tenant_id": identity["tenant_id"],
        "status": "bootstrap_pending",
    }

    bindings = list_connector_bindings(identity["tenant_id"])
    profiles = list_connector_profiles(identity["tenant_id"])
    memberships = list_tenant_memberships(identity["tenant_id"])
    return {
        "tenant": {
            key: value
            for key, value in tenant.items()
            if key not in {"token", "secret_value", "access_token", "refresh_token"}
        },
        "role": identity["role"],
        "connector_binding_count": len(bindings),
        "connector_profile_count": len(profiles),
        "membership_count": len(memberships),
        "credential_values_exposed": False,
    }


@app.get("/api/tenants/available")
def get_available_tenants(identity_token: str | None = None) -> dict[str, object]:
    """List the caller's active tenant memberships for a tenant switcher.

    This is the only identity-only tenant discovery route. It does not accept a
    tenant selector, HMAC token, or operator-supplied email, and it returns
    membership metadata only. A user with one active membership can omit a
    tenant selector on subsequent signed requests; a user with several must
    explicitly choose one so an identity can never silently fall into the
    deployment's demo tenant.
    """
    audience = os.getenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "").strip()
    try:
        claims = _verify_google_identity_claims(identity_token, audience)
        email = str(claims.get("email", "")).strip().casefold()
        memberships = list_tenant_memberships_for_email(email)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid tenant identity") from exc

    available: list[dict[str, object]] = []
    for member in memberships:
        if str(member.get("status", "active")).casefold() != "active":
            continue
        tenant_id = str(member.get("tenant_id", "")).strip().casefold()
        try:
            tenant_id = validate_tenant_id(tenant_id)
        except ValueError:
            continue
        tenant = load_tenant(tenant_id)
        if os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore" and not tenant:
            continue
        if tenant and str(tenant.get("status", "active")).casefold() != "active":
            continue
        available.append(
            {
                "tenant_id": tenant_id,
                "role": str(member.get("role", "viewer")).casefold(),
                "membership_id": member.get("membership_id"),
                "status": "active",
            }
        )
    available.sort(key=lambda item: str(item["tenant_id"]))
    return {
        "status": "ok" if available else "no_active_memberships",
        "email": email,
        "tenants": available,
        "selection_required": len(available) > 1,
        "credential_values_exposed": False,
    }


@app.post("/api/platform/tenants")
def provision_platform_tenant(
    request: PlatformTenantProvisionRequest,
) -> dict[str, object]:
    """Create or reactivate tenant metadata through a platform OIDC identity.

    This route is intentionally a control-plane bootstrap only. It creates no
    Secret Manager value and accepts no provider credential; infrastructure
    provisions the deterministic containers separately before bindings can be
    activated.
    """
    platform = _verify_platform_operator(request.identity_token)
    try:
        tenant_id = validate_tenant_id(request.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    owner_email = request.owner_email.strip().casefold()
    if "@" not in owner_email or len(owner_email) > 320:
        raise HTTPException(status_code=422, detail="owner_email_invalid")
    now = utc_now()
    bootstrap_audit = {
        "event_id": f"tenant-audit-{uuid4().hex}",
        "tenant_id": tenant_id,
        "event_type": "tenant_provisioned",
        "status": "active",
        "owner_email": owner_email,
        "actor": platform["email"],
        "identity": platform["identity"],
        "created_at": now,
    }
    created = provision_tenant_metadata(
        {
            "tenant_id": tenant_id,
            "status": "active",
            "provisioning": "platform_oidc",
            "configured_by": platform["email"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "tenant_id": tenant_id,
            "email": owner_email,
            "role": "owner",
            "status": "active",
            "source": "platform_oidc_bootstrap",
            "configured_by": platform["email"],
            "updated_at": now,
        },
        audit_payload=bootstrap_audit,
    )
    if not created:
        # A previous platform bootstrap may have created the tenant document
        # but failed before writing its owner membership (for example during a
        # rolling Firestore migration). Repair that bounded, metadata-only
        # state instead of leaving the tenant permanently undiscoverable.
        existing_tenant = load_tenant(tenant_id) or {}
        existing_memberships = list_tenant_memberships(tenant_id)
        if (
            str(existing_tenant.get("status", "")).casefold() == "active"
            and not existing_memberships
        ):
            repaired = persist_tenant_membership(
                {
                    "tenant_id": tenant_id,
                    "email": owner_email,
                    "role": "owner",
                    "status": "active",
                    "source": "platform_oidc_membership_repair",
                    "configured_by": platform["email"],
                    "updated_at": now,
                }
            )
            repair_audit = persist_tenant_audit_event(
                {
                    **bootstrap_audit,
                    "event_id": f"tenant-audit-{uuid4().hex}",
                    "event_type": "tenant_membership_repaired",
                    "status": "active",
                    "repair": "missing_owner_membership",
                }
            )
            return {
                "status": "active",
                "tenant_id": tenant_id,
                "owner_email": owner_email,
                "membership_id": repaired["membership_id"],
                "secret_references": {
                    connector: tenant_connector_secret_name(tenant_id, connector)
                    for connector in ("jira", "confluence", "slack", "github", "salesforce")
                },
                "operator_signing_secret": tenant_operator_signing_secret_name(tenant_id),
                "credential_values_exposed": False,
                "audit_event_id": repair_audit["event_id"],
                "repaired_membership": True,
                "next_step": (
                    "Provision the deterministic Secret Manager containers out of band, "
                    "then add provider values and activate each owner binding."
                ),
            }
        raise HTTPException(status_code=409, detail="tenant_already_exists")
    membership_id = base64.urlsafe_b64encode(
        f"{tenant_id}:{owner_email}".encode()
    ).decode("ascii").rstrip("=")
    return {
        "status": "active",
        "tenant_id": tenant_id,
        "owner_email": owner_email,
        "membership_id": membership_id,
        "secret_references": {
            connector: tenant_connector_secret_name(tenant_id, connector)
            for connector in ("jira", "confluence", "slack", "github", "salesforce")
        },
        "operator_signing_secret": tenant_operator_signing_secret_name(tenant_id),
        "credential_values_exposed": False,
        "audit_event_id": bootstrap_audit["event_id"],
        "next_step": (
            "Provision the deterministic Secret Manager containers out of band, "
            "then add provider values and activate each owner binding."
        ),
    }


@app.get("/api/tenants/audit")
def get_tenant_audit(
    operator: str,
    tenant_id: str | None = None,
    limit: int = 50,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return append-only tenant control-plane events without credentials."""
    identity = _verify_approval_mode(
        "tenant-audit",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    events = list_tenant_audit_events(identity["tenant_id"], limit=limit)
    return {
        "append_only": True,
        "tenant_id": identity["tenant_id"],
        "events": [
            {
                key: value
                for key, value in event.items()
                if key not in {"token", "secret_value", "access_token", "refresh_token"}
            }
            for event in events
        ],
        "credential_values_exposed": False,
    }


@app.get("/api/tenants/usage")
def get_tenant_usage(
    operator: str,
    tenant_id: str | None = None,
    period: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return aggregate tenant usage; this is metering, not billing."""
    identity = _verify_approval_mode(
        "tenant-usage",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    usage = load_tenant_usage(identity["tenant_id"], period=period)
    return {
        "tenant_id": identity["tenant_id"],
        "period": usage.get("period"),
        "usage": {
            key: usage.get(key, 0)
            for key in (
                "agent_calls",
                "workflow_mutations",
                "connector_calls",
                "monitor_jobs",
            )
        },
        "metering": {
            "durable": True,
            "scope": "tenant_period",
            "billing_enabled": False,
            "retention": "control_plane_metadata; no content TTL",
        },
        "credential_values_exposed": False,
    }


@app.get("/api/tenants/policy")
def get_tenant_policy(
    operator: str,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return the caller's effective bounded quota and retention policy."""
    identity = _verify_approval_mode(
        "tenant-policy-read",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    policy = load_tenant_policy(identity["tenant_id"])
    return {
        "tenant_id": identity["tenant_id"],
        "policy": policy,
        "windows_seconds": {
            "agent_calls": AGENT_WINDOW_SECONDS,
            "workflow_mutations": DEMO_WINDOW_SECONDS,
            "connector_calls": CONNECTOR_WINDOW_SECONDS,
        },
        "billing_enabled": False,
        "metering_only": True,
        "credential_values_exposed": False,
    }


@app.post("/api/tenants/policy")
def update_tenant_policy(request: TenantPolicyRequest) -> dict[str, object]:
    """Update one tenant's bounded quota and retention policy without redeploying."""
    identity = _verify_approval_mode(
        "tenant-policy-update",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    requested_policy = {
        field: getattr(request, field)
        for field in (
            "agent_calls_per_window",
            "workflow_mutations_per_window",
            "connector_calls_per_window",
            "retention_days",
        )
        if field in request.model_fields_set
    }
    policy = persist_tenant_policy(identity["tenant_id"], requested_policy)
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": identity["tenant_id"],
            "event_type": "tenant_policy_updated",
            "policy_keys": sorted(policy),
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": "active",
        "tenant_id": identity["tenant_id"],
        "policy": policy,
        "billing_enabled": False,
        "metering_only": True,
        "audit_event_id": audit_event["event_id"],
        "credential_values_exposed": False,
    }


@app.post("/api/tenants/deprovision")
def deprovision_tenant(request: TenantDeprovisionRequest) -> dict[str, object]:
    """Soft-disable one tenant and revoke its connector bindings."""
    identity = _verify_approval_mode(
        "tenant-deprovision",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    tenant_id = identity["tenant_id"]
    if request.confirmation.strip().casefold() != tenant_id:
        raise HTTPException(status_code=422, detail="tenant_confirmation_mismatch")
    now = utc_now()
    bindings = list_connector_bindings(tenant_id)
    for binding in bindings:
        persist_connector_binding(
            {
                **binding,
                "tenant_id": tenant_id,
                "status": "revoked",
                "revoked_at": now,
                "revoked_by": identity.get("email") or identity.get("identity"),
            }
        )
    memberships = list_tenant_memberships(tenant_id)
    for member in memberships:
        persist_tenant_membership(
            {
                **member,
                "tenant_id": tenant_id,
                "status": "disabled",
                "updated_at": now,
            }
        )
    persist_tenant(
        {
            "tenant_id": tenant_id,
            "status": "disabled",
            "deprovisioned_at": now,
            "deprovisioned_by": identity.get("email") or identity.get("identity"),
        }
    )
    audit_event = persist_tenant_audit_event(
        {
            "tenant_id": tenant_id,
            "event_type": "tenant_deprovisioned",
            "status": "disabled",
            "revoked_binding_count": len(bindings),
            "disabled_membership_count": len(memberships),
            "actor": identity.get("email") or identity.get("identity"),
        }
    )
    return {
        "status": "disabled",
        "tenant_id": tenant_id,
        "revoked_binding_count": len(bindings),
        "disabled_membership_count": len(memberships),
        "audit_event_id": audit_event["event_id"],
        "credential_values_exposed": False,
        "follow_up": (
            "Revoke provider tokens and delete or disable the tenant's Secret "
            "Manager versions through infrastructure offboarding."
        ),
    }


@app.get("/api/tenants/members")
def get_tenant_members(
    operator: str,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """List role metadata for one tenant; owners only may inspect membership."""
    identity = _verify_approval_mode(
        "tenant-members",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    members = list_tenant_memberships(identity["tenant_id"])
    return {
        "tenant_id": identity["tenant_id"],
        "members": [
            {
                key: value
                for key, value in member.items()
                if key not in {"token", "secret_value", "access_token", "refresh_token"}
            }
            for member in members
        ],
        "credential_values_exposed": False,
    }


@app.post("/api/tenants/members")
def provision_tenant_member(request: TenantMemberRequest) -> dict[str, object]:
    """Provision or update one tenant role without accepting a secret/token."""
    identity = _verify_approval_mode(
        "tenant-member-provision",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Tenant owner role is required")
    email = request.email.strip().casefold()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=422, detail="member_email_invalid")
    tenant_id = identity["tenant_id"]
    persist_tenant(
        {
            "tenant_id": tenant_id,
            "status": "active",
            "provisioning": "owner_membership",
            "configured_by": identity.get("email") or identity.get("identity"),
            "updated_at": utc_now(),
        }
    )
    member = persist_tenant_membership(
        {
            "tenant_id": tenant_id,
            "email": email,
            "role": request.role,
            "status": request.status,
            "source": "owner_provisioned",
            "updated_at": utc_now(),
        }
    )
    return {
        "status": request.status,
        "tenant_id": tenant_id,
        "email": email,
        "role": request.role,
        "membership_id": member["membership_id"],
        "credential_values_exposed": False,
    }


@app.get("/api/connectors/bindings")
def get_connector_bindings(
    operator: str,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """List metadata-only connector bindings for the caller's tenant."""
    identity = _verify_approval_mode(
        "connector-bindings-list",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    bindings = list_connector_bindings(identity["tenant_id"])
    return {
        "tenant_id": identity["tenant_id"],
        "bindings": [
            {
                key: value
                for key, value in binding.items()
                if key not in {"token", "secret_value", "access_token", "refresh_token"}
            }
            for binding in bindings
        ],
        "credential_values_exposed": False,
    }


@app.get("/api/connectors/credentials")
def get_connector_credentials(
    operator: str,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return the tenant credential-broker inventory without secret values."""
    identity = _verify_approval_mode(
        "connector-credentials-list",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    bindings = list_connector_bindings(identity["tenant_id"])
    credentials = []
    for binding in bindings:
        connector = str(binding.get("connector", ""))
        credentials.append(
            {
                "credential_id": binding.get(
                    "credential_id", f"cred-{identity['tenant_id']}-{connector}"
                ),
                "connector": connector,
                "status": binding.get("status", "unknown"),
                "secret_backend": binding.get(
                    "secret_backend", "google_secret_manager"
                ),
                "secret_reference_scope": binding.get(
                    "secret_reference_scope", "exact_tenant_connector_secret"
                ),
                "secret_version": binding.get("secret_version", "latest"),
                "allowed_operations": sorted(
                    binding.get(
                        "allowed_operations", allowed_operations(connector)
                    )
                ),
                "lease_seconds": int(binding.get("lease_seconds", 300)),
                "namespace_verified": bool(binding.get("credential_namespace")),
                "credential_namespace": binding.get("credential_namespace"),
                "verified_at": binding.get("verified_at"),
                "updated_at": binding.get("updated_at"),
                "credential_values_exposed": False,
            }
        )
    return {
        "status": "ok",
        "tenant_id": identity["tenant_id"],
        "credentials": credentials,
        "architecture": {
            "isolation": "tenant_binding_to_exact_secret_manager_secret",
            "canonical_binding_path": "driftline_tenants/{tenant}/credentials/{connector}",
            "namespace_schema_version": 1,
            "namespace_migration": "scripts/migrate_tenant_credential_bindings.py",
            "legacy_flat_mirror_writes": os.getenv(
                "DRIFTLINE_WRITE_LEGACY_CONNECTOR_MIRROR", "false"
            ).casefold()
            == "true",
            "strict_namespace_required": os.getenv(
                "DRIFTLINE_REQUIRE_TENANT_CREDENTIAL_NAMESPACE", "false"
            ).casefold()
            == "true",
            "resolution": "short_lived_in_process_lease",
            "rotation": "owner_requested_then_version_pinned",
            "revocation": "binding_status_fail_closed",
            "audit_collection": "driftline_credential_access_events",
            "enrollment": {
                "start_route": "/api/connectors/{connector}/credential-enrollment",
                "complete_route": "/api/connectors/{connector}/credential-enrollment/{id}/complete",
                "session_ttl_seconds": 900,
                "default_new_scope": ["read_context"],
                "raw_secret_accepted": False,
            },
        },
        "credential_values_exposed": False,
    }


@app.get("/api/connectors/credentials/access")
def get_connector_credential_access(
    operator: str,
    tenant_id: str | None = None,
    limit: int = 100,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return one tenant's redacted credential lease audit trail."""
    identity = _verify_approval_mode(
        "connector-credentials-access",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    events = list_credential_access_events(identity["tenant_id"], limit=limit)
    redacted = [
        {
            key: value
            for key, value in event.items()
            if key
            not in {
                "value",
                "token",
                "secret_value",
                "access_token",
                "refresh_token",
                "client_secret",
            }
        }
        for event in events
    ]
    return {
        "status": "ok",
        "tenant_id": identity["tenant_id"],
        "events": redacted,
        "append_only": True,
        "credential_values_exposed": False,
    }


@app.get("/api/connectors/bindings/health")
def get_connector_binding_health(
    operator: str,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Reconcile tenant binding metadata with readable Secret Manager state.

    This is a read-only operator probe. It enumerates the fixed connector
    allowlist, never accepts a secret name, and never returns a credential
    value. Active bindings are checked against the exact deterministic secret;
    pending, revoked, or missing bindings remain fail-closed and are surfaced
    as attention items rather than being silently treated as healthy.
    """
    identity = _verify_approval_mode(
        "connector-bindings-health",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    if not _reserve_connector_call(identity["tenant_id"]):
        raise HTTPException(
            status_code=429,
            detail="Connector read quota reached; retry later.",
        )
    bound = {
        str(binding.get("connector")): binding
        for binding in list_connector_bindings(identity["tenant_id"])
        if binding.get("connector")
    }

    def profile_health(connector: str) -> dict[str, object]:
        """Reconcile the non-secret destination profile without returning values."""
        try:
            profile = load_connector_profile(identity["tenant_id"], connector)
        except Exception:  # noqa: BLE001 - health must not leak provider/storage errors.
            return {
                "status": "attention",
                "reason": "profile_lookup_failed",
                "configured_keys": [],
            }
        if not profile:
            return {
                "status": "not_configured",
                "reason": "profile_missing",
                "configured_keys": [],
            }
        if str(profile.get("status", "active")).casefold() != "active":
            return {
                "status": "attention",
                "reason": "profile_inactive",
                "configured_keys": [],
            }
        try:
            safe_settings = validate_connector_profile(
                connector, dict(profile.get("settings") or {})
            )
        except (TypeError, ValueError):
            return {
                "status": "attention",
                "reason": "profile_invalid",
                "configured_keys": [],
            }
        return {
            "status": "healthy",
            "reason": "profile_configured",
            "configured_keys": sorted(safe_settings),
        }

    checks: list[dict[str, object]] = []
    for connector in sorted(CONNECTOR_NAMES):
        expected_secret = tenant_connector_secret_name(identity["tenant_id"], connector)
        try:
            expected_namespace = tenant_credential_namespace(
                identity["tenant_id"], connector
            )
        except (TypeError, ValueError):
            expected_namespace = None
        binding = bound.get(connector)
        profile = profile_health(connector)
        if binding is None:
            checks.append(
                {
                    "connector": connector,
                    "status": "not_configured",
                    "secret_status": "not_configured",
                    "profile_status": profile["status"],
                    "profile_reason": profile["reason"],
                    "profile_configured_keys": profile["configured_keys"],
                    "secret_name": expected_secret,
                    "namespace_status": "not_configured",
                    "credential_values_exposed": False,
                }
            )
            continue
        binding_status = str(binding.get("status", "unknown"))
        secret_name = str(binding.get("secret_name", ""))
        namespace = binding.get("credential_namespace")
        namespace_status = (
            "verified"
            if isinstance(namespace, dict)
            and isinstance(expected_namespace, dict)
            and all(namespace.get(key) == expected_namespace.get(key) for key in (
                "schema_version",
                "tenant_id",
                "connector",
                "secret_resource",
                "service_account",
                "isolation",
            ))
            else "missing"
            if expected_namespace is not None and namespace is None
            else "not_checked"
            if expected_namespace is None
            else "mismatch"
        )
        check: dict[str, object] = {
            "connector": connector,
            "binding_status": binding_status,
            "secret_name": expected_secret,
            "namespace_status": namespace_status,
            "profile_status": profile["status"],
            "profile_reason": profile["reason"],
            "profile_configured_keys": profile["configured_keys"],
            "credential_values_exposed": False,
        }
        if secret_name != expected_secret:
            check.update(status="attention", secret_status="name_mismatch")
        elif namespace_status in {"missing", "mismatch"} or binding_status != "active":
            check.update(status="attention", secret_status="not_checked")
        else:
            try:
                readable = bool(_read_tenant_secret(tenant_id, expected_secret).strip())
            except Exception:  # noqa: BLE001 - health must not leak provider errors.
                readable = False
            check.update(
                status=(
                    "healthy"
                    if readable and profile["status"] == "healthy"
                    else "attention"
                ),
                secret_status="readable" if readable else "unreadable",
            )
        checks.append(check)
    return {
        "status": "ok",
        "tenant_id": identity["tenant_id"],
        "generated_at": utc_now(),
        "summary": {
            "total": len(checks),
            "healthy": sum(item["status"] == "healthy" for item in checks),
            "attention": sum(item["status"] == "attention" for item in checks),
            "not_configured": sum(
                item["status"] == "not_configured" for item in checks
            ),
        },
        "checks": checks,
        "credential_values_exposed": False,
    }


@app.get("/api/ops/value-proof")
def get_value_proof(
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return observed workflow throughput without cross-tenant disclosure."""
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for value metrics"
            )
        identity = _verify_approval_mode(
            "ops:value-proof",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    with _jobs_lock:
        job_records = list(_jobs.values())
    jobs = [
        job
        for job in _merge_durable_records(
            job_records, list_jobs, limit=50, key=lambda item: item.job_id
        )
        if _visible_tenant_record(job, identity)
    ]
    workflow_records = list(workflow_store._runs.values())
    workflows = [
        state
        for state in _merge_durable_records(
            workflow_records,
            list_workflows,
            limit=50,
            key=lambda item: item.workflow_id,
        )
        if _visible_tenant_record(state, identity)
    ]
    action_items = [item for state in workflows for item in state.action_items]
    source_health = source_registry_health(
        tenant_id=identity.get("tenant_id") if identity else None
    )
    change_cards = [state.change_card for state in workflows if state.change_card]
    materiality_cards = [card.get("materiality") or {} for card in change_cards]
    closure_cards = [card.get("closure") or {} for card in change_cards]
    workflow_data_modes = _count_record_modes(workflows, "data_mode")
    job_run_modes = _count_record_modes(jobs, "run_mode")
    external_writes = sum(
        bool((state.action_record or {}).get("external_write")) for state in workflows
    )
    reversed_workflows = sum(
        any(event.get("outcome") == "decision_reopened" for event in state.events)
        for state in workflows
    )
    approval_latencies: list[float] = []
    for state in workflows:
        approval_event = next(
            (
                event
                for event in state.events
                if event.get("outcome") == "approval_recorded"
            ),
            None,
        )
        if not approval_event:
            continue
        try:
            created = datetime.fromisoformat(state.created_at)
            approved = datetime.fromisoformat(str(approval_event["timestamp"]))
            approval_latencies.append(max(0.0, (approved - created).total_seconds()))
        except (KeyError, TypeError, ValueError):
            continue
    approval_latencies.sort()
    p50_latency = (
        approval_latencies[len(approval_latencies) // 2] if approval_latencies else None
    )
    p90_latency = (
        approval_latencies[
            min(len(approval_latencies) - 1, int(len(approval_latencies) * 0.9))
        ]
        if approval_latencies
        else None
    )
    return {
        "generated_at": utc_now(),
        "scope": (
            "observed_tenant_records"
            if identity
            else "observed_driftline_sandbox_records"
        ),
        "observed": {
            "jobs": len(jobs),
            "workflows": len(workflows),
            "workflow_data_modes": workflow_data_modes,
            "job_run_modes": job_run_modes,
            "tenant_scoped_workflows": sum(
                state.tenant_id is not None for state in workflows
            ),
            "tenantless_workflows": sum(
                state.tenant_id is None for state in workflows
            ),
            "workflows_reversed_or_reopened": reversed_workflows,
            "external_write_actions": external_writes,
            "action_items": len(action_items),
            "action_items_completed": sum(
                item.get("status") == ActionItemStatus.COMPLETED.value
                for item in action_items
            ),
            "healthy_sources": sum(
                item.get("status") == "healthy" for item in source_health
            ),
            "source_observations": sum(
                int(item.get("observation_count", 0)) for item in source_health
            ),
            "approval_latency_seconds": {
                "sample_count": len(approval_latencies),
                "p50": p50_latency,
                "p90": p90_latency,
            },
            "action_item_completion_rate": (
                round(
                    sum(
                        item.get("status") == ActionItemStatus.COMPLETED.value
                        for item in action_items
                    )
                    / len(action_items),
                    3,
                )
                if action_items
                else None
            ),
            "change_cards": len(change_cards),
            "high_materiality_cards": sum(
                item.get("severity") == "high" for item in materiality_cards
            ),
            "cards_with_named_owners": sum(
                bool(card.get("owners")) for card in change_cards
            ),
            "cards_closed": sum(
                item.get("state") == "closed" for item in closure_cards
            ),
            "cards_dismissed": sum(
                item.get("state") == "dismissed" for item in closure_cards
            ),
            "overdue_owner_actions": sum(
                int(item.get("overdue", 0)) for item in closure_cards
            ),
        },
        "not_measured": [
            "hours_saved_per_change",
            "revenue_or_win_rate_lift",
            "customer_retention_impact",
            "willingness_to_pay",
        ],
        "interpretation": (
            "Counts are direct records from this isolated Driftline deployment; "
            "they are not customer or revenue claims."
        ),
    }


@app.get("/api/ops/outcomes")
def get_outcome_measurements(
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return aggregate outcomes only for the public or signed tenant scope."""
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for outcome records"
            )
        identity = _verify_approval_mode(
            "ops:outcomes",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    records = [
        record
        for record in list_outcome_measurements(50)
        if record.get("tenant_id") is None
        or (identity is not None and record.get("tenant_id") == identity.get("tenant_id"))
    ]
    return {
        "scope": "operator_reported_outcome_ledger",
        "records": records,
        "count": len(records),
        "status": "measured_records_available" if records else "not_measured",
        "not_measured": []
        if records
        else [
            "hours_saved_per_change",
            "revenue_or_win_rate_lift",
            "customer_retention_impact",
            "willingness_to_pay",
        ],
        "disclosure": "Records are operator-reported aggregate evidence and remain unverified until reviewed against the referenced source.",
    }


@app.post("/api/ops/outcomes")
def record_outcome_measurement(request: OutcomeMeasurementRequest) -> dict[str, object]:
    """Ingest one aggregate pilot measurement through the signed operator lane."""
    approval_identity = _verify_approval_mode(
        f"outcome:{request.cohort_label}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if not request.evidence_ref.startswith(("https://", "gs://", "artifact://")):
        raise HTTPException(
            status_code=422,
            detail="evidence_ref_must_point_to_audit_artifact_or_https_source",
        )
    measurement_id = f"measurement-{uuid4().hex[:16]}"
    payload = {
        "measurement_id": measurement_id,
        "tenant_id": approval_identity["tenant_id"],
        "source_type": request.source_type,
        "cohort_label": request.cohort_label,
        "changes_observed": request.changes_observed,
        "baseline_minutes": request.baseline_minutes,
        "driftline_minutes": request.driftline_minutes,
        "time_saved_minutes_per_change": round(
            request.baseline_minutes - request.driftline_minutes, 2
        ),
        "revenue_lift_usd": request.revenue_lift_usd,
        "retention_lift_pct": request.retention_lift_pct,
        "willingness_to_pay_usd": request.willingness_to_pay_usd,
        "evidence_ref": request.evidence_ref,
        "status": "operator_reported_unverified",
        "approval_identity": approval_identity.get("identity", "signed_operator"),
        "captured_at": utc_now(),
    }
    try:
        persist_outcome_measurement(payload)
    except Exception as exc:  # pragma: no cover - Firestore-only failure path.
        logger.exception("Outcome measurement persistence failed")
        raise HTTPException(
            status_code=503, detail="Outcome ledger unavailable"
        ) from exc
    return {
        "status": "recorded",
        "measurement": payload,
        "disclosure": "This is operator-reported aggregate evidence, not an independently verified customer claim.",
    }


@app.get("/api/ops/pilot-report")
def get_pilot_report(
    cohort_label: str | None = None,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Summarize signed, aggregate pilot records without exposing evidence refs.

    A pilot report is intentionally separate from public value proof. It only
    reads the caller's tenant records, keeps the records marked
    ``operator_reported_unverified``, and computes deltas without turning them
    into independently verified customer claims.
    """
    if not operator or not tenant_id:
        raise HTTPException(
            status_code=401, detail="Signed approval is required for pilot reports"
        )
    identity = _verify_approval_mode(
        "ops:pilot-report",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    requested_cohort = cohort_label.strip() if cohort_label else None
    if requested_cohort and len(requested_cohort) > 80:
        raise HTTPException(status_code=422, detail="cohort_label_too_long")
    records = [
        record
        for record in list_outcome_measurements(100)
        if record.get("tenant_id") == identity["tenant_id"]
        and (not requested_cohort or record.get("cohort_label") == requested_cohort)
    ]
    total_changes = sum(int(record.get("changes_observed", 0) or 0) for record in records)
    baseline_total = sum(float(record.get("baseline_minutes", 0) or 0) for record in records)
    driftline_total = sum(float(record.get("driftline_minutes", 0) or 0) for record in records)
    wtp_values = [
        float(record["willingness_to_pay_usd"])
        for record in records
        if record.get("willingness_to_pay_usd") is not None
    ]
    revenue_values = [
        float(record["revenue_lift_usd"])
        for record in records
        if record.get("revenue_lift_usd") is not None
    ]
    retention_values = [
        float(record["retention_lift_pct"])
        for record in records
        if record.get("retention_lift_pct") is not None
    ]
    return {
        "scope": "signed_tenant_pilot_records",
        "tenant_id": identity["tenant_id"],
        "cohort_label": requested_cohort,
        "status": "not_measured" if not records else "operator_reported_unverified",
        "record_count": len(records),
        "changes_observed": total_changes,
        "baseline_minutes_total": round(baseline_total, 2),
        "driftline_minutes_total": round(driftline_total, 2),
        "time_saved_minutes_total": round(baseline_total - driftline_total, 2),
        "time_saved_pct": (
            round((baseline_total - driftline_total) / baseline_total * 100, 2)
            if baseline_total
            else None
        ),
        "revenue_lift_usd_total": round(sum(revenue_values), 2) if revenue_values else None,
        "retention_lift_pct_median": round(median(retention_values), 2) if retention_values else None,
        "willingness_to_pay_usd_median": round(median(wtp_values), 2) if wtp_values else None,
        "disclosure": (
            "Aggregate operator-reported evidence only; independently verify each "
            "record against its source before making a customer or revenue claim."
        ),
    }


@app.get("/api/sources/{source_id:path}/history")
def get_source_history(
    source_id: str,
    limit: int = 12,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for source history"
            )
        identity = _verify_approval_mode(
            f"source-history:{source_id}",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    bound_tenant = identity.get("tenant_id") if identity else None
    definition = source_definition(source_id, bound_tenant)
    if definition is None:
        raise HTTPException(status_code=404, detail="Source is not allowlisted")
    if (
        definition.get("dynamic") == "true"
        and not identity
    ):
        raise HTTPException(status_code=403, detail="Tenant-scoped source requires signed approval")
    bounded_limit = max(1, min(limit, 50))
    observations = list_source_history(source_id, bounded_limit, bound_tenant)
    return {
        "source_id": source_id,
        "append_only": True,
        "observations": observations,
        "memory": build_memory_summary({source_id: observations}, [])["sources"][0],
    }


@app.get("/api/memory/summary")
def get_memory_summary(
    limit: int = 50,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return append-only change memory plus recurring and unresolved work."""
    bounded_limit = max(1, min(limit, 100))
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for tenant memory"
            )
        identity = _verify_approval_mode(
            "memory:summary",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    source_tenant = identity.get("tenant_id") if identity else None
    source_observations = {
        source_id: list_source_history(source_id, bounded_limit, source_tenant)
        for source_id in source_definitions(source_tenant)
    }
    with _jobs_lock:
        workflow_records = list(workflow_store._runs.values())
    workflows = [
        state.to_dict()
        for state in _merge_durable_records(
            workflow_records,
            list_workflows,
            limit=bounded_limit,
            key=lambda item: item.workflow_id,
        )
        if _visible_tenant_record(state, identity)
    ]
    return build_memory_summary(source_observations, workflows)


@app.get("/api/multimodal/assets/{asset_id}/{side}")
def get_multimodal_asset(
    asset_id: str, side: str, mode: Literal["live", "demo"] = "live"
) -> Response:
    """Serve only bytes from the visual registry through the same origin."""
    try:
        asset = visual_asset_bytes(asset_id, side, mode)
    except MultimodalUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=asset.body, media_type=asset.mime_type)


@app.get("/api/multimodal/evidence/{asset_id}")
def get_multimodal_evidence(
    asset_id: str, mode: Literal["live", "demo"] = "live"
) -> dict[str, object]:
    """Return before/after visual metadata and the combined evidence hash."""
    fallback_reason: str | None = None
    resolved_mode = mode
    try:
        evidence = get_visual_evidence(asset_id, mode)
    except MultimodalUnavailable as exc:
        # The anonymous fixed visual lane should remain judgeable during a
        # transient GitHub/public-byte outage. Keep the strict multimodal
        # helper semantics intact, but return a visibly labelled synthetic
        # pair from this public metadata route instead of a broken panel.
        if mode != "live":
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        try:
            evidence = get_visual_evidence(asset_id, "demo")
            resolved_mode = "demo"
            fallback_reason = str(exc)
        except MultimodalUnavailable:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    payload = evidence.to_dict()
    payload["before_url"] = f"/api/multimodal/assets/{asset_id}/before?mode={resolved_mode}"
    payload["after_url"] = f"/api/multimodal/assets/{asset_id}/after?mode={resolved_mode}"
    if fallback_reason:
        payload["fallback_reason"] = fallback_reason
    return payload


@app.post("/api/multimodal/analyze")
async def analyze_multimodal(request: MultimodalAnalysisRequest) -> dict[str, object]:
    """Run Gemini vision only on the bounded allowlisted visual pair."""
    retry_after = _reserve_multimodal_call()
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Multimodal analysis quota reached; retry later.",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        return await asyncio.to_thread(
            analyze_visual_evidence, request.asset_id, request.mode
        )
    except MultimodalUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/workflows/{workflow_id}/scenarios")
def get_workflow_scenarios(
    workflow_id: str,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Preview approve/grandfather/defer outcomes without making any writes."""
    try:
        state = _resolve_workflow(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _authorize_read_tenant(
        state,
        resource_id=state.workflow_id,
        operator=operator,
        tenant_id=tenant_id,
        approval_token=approval_token,
        identity_token=identity_token,
    )
    impacts = [item.__dict__ for item in state.impacts]
    return simulate_scenarios(
        impacts,
        state.evidence.evidence_hash if state.evidence else None,
        state.integration_targets,
    )


@app.post("/api/workflows/demo")
def start_demo(source_id: str = "public/pricing") -> dict:
    """Legacy deterministic fixture endpoint retained for reproducible tests."""
    if not _reserve_demo_mutation():
        raise HTTPException(
            status_code=429,
            detail="Demo workflow rate limit reached; retry later.",
        )
    definition = source_definition(source_id)
    if definition is None:
        raise HTTPException(status_code=422, detail="Source is not allowlisted")
    if definition.get("dynamic") == "true":
        raise HTTPException(
            status_code=422,
            detail="Operator-registered sources require a public monitor run",
        )
    state = workflow_store.start_demo(
        source_id=source_id,
        source_name=definition["name"],
        source_url=definition["url"],
        before_text=definition["before"],
        after_text=definition["after"],
        snapshot_label=f"Synthetic replay fixture · {source_id}",
        data_mode="synthetic_demo",
    )
    persist_workflow(state)
    return state.to_dict()


@app.post("/api/jobs/demo")
async def start_demo_job(
    request: JobStartRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    tenant_id: str | None = None
    if request.run_mode in {"monitor", "tenant_demo"}:
        auth_resource = (
            "monitor" if request.run_mode == "monitor" else "tenant-demo"
        )
        monitor_identity = _verify_approval_mode(
            f"{auth_resource}:{request.source_id}",
            request.operator,
            "signed",
            request.approval_token,
            request.identity_token,
            request.tenant_id,
        )
        tenant_id = monitor_identity["tenant_id"]
    definition = source_definition(request.source_id, tenant_id)
    if definition is None:
        raise HTTPException(status_code=422, detail="Source is not allowlisted")
    if definition.get("dynamic") == "true" and request.run_mode != "monitor":
        raise HTTPException(
            status_code=422,
            detail="Operator-registered sources require run_mode=monitor",
        )
    if not _reserve_agent_call(tenant_id):
        raise HTTPException(
            status_code=429,
            detail="Live agent demo rate limit reached; retry later.",
        )
    if request.run_mode == "demo" and tenant_id is None:
        # The anonymous lane is a deterministic judge surface. Do not persist
        # or send arbitrary caller text to Gemini; otherwise a public visitor
        # could accidentally submit private material into the demo ledger.
        query = (
            f"Inspect the allowlisted {request.source_id} change, verify the "
            "evidence, map affected artifacts, and stop at the human approval "
            "gate."
        )
        user_id = "public-demo"
    else:
        query = (
            f"{request.query.strip()} Use the exact allowlisted source_id "
            f'"{request.source_id}". Do not choose a different source.'
        )
        user_id = request.user_id
    job = _start_job(
        query=query,
        user_id=user_id,
        run_mode=request.run_mode,
        background_tasks=background_tasks,
        tenant_id=tenant_id,
        source_id=request.source_id,
    )
    return job.to_dict()


@app.get("/api/jobs")
def get_jobs(
    limit: int = 8,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Expose bounded history while filtering tenant-bound jobs by identity."""
    bounded_limit = max(1, min(limit, 20))
    identity: dict[str, str] | None = None
    if any(value is not None for value in (operator, tenant_id, approval_token, identity_token)):
        if not operator or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Signed approval is required for tenant jobs"
            )
        identity = _verify_approval_mode(
            "jobs:list",
            operator,
            "signed",
            approval_token,
            identity_token,
            tenant_id,
        )
    with _jobs_lock:
        memory_jobs = list(_jobs.values())
    candidates = _merge_durable_records(
        memory_jobs, list_jobs, limit=bounded_limit, key=lambda item: item.job_id
    )
    candidates.sort(key=lambda item: item.created_at or "", reverse=True)
    jobs = [
        job
        for job in candidates
        if _visible_tenant_record(job, identity)
    ][:bounded_limit]
    return {"jobs": [_job_payload(job) for job in jobs]}


@app.post("/api/scheduler/tick")
async def scheduler_tick(
    request: Request,
    background_tasks: BackgroundTasks,
    source_id: str | None = None,
) -> dict:
    """Fan out one bounded historical monitor run per approved source.

    A signed scheduler can pass ``source_id`` for a single canary. With no
    query parameter, the explicit production registry is used. The fan-out is
    intentionally capped before any model call so a bad scheduler configuration
    cannot turn into an unbounded crawler or spend spike.
    """
    _verify_scheduler_request(request)
    configured_value = os.getenv("DRIFTLINE_MONITOR_SOURCES", "all").strip()
    if configured_value.casefold() in {"", "all"}:
        configured_entries = scheduler_source_entries()
    else:
        requested_ids = [
            item.strip() for item in configured_value.split(",") if item.strip()
        ]
        configured_entries = [
            (None, item, source_definition(item) or {}) for item in requested_ids
        ]
    if source_id:
        configured_entries = [
            entry for entry in configured_entries if entry[1] == source_id.strip()
        ]
    source_entries = configured_entries
    max_sources = _positive_int("DRIFTLINE_MONITOR_MAX_SOURCES", 5)
    source_entries = source_entries[:max_sources]
    invalid = [
        item
        for tenant_id, item, definition in source_entries
        if not definition or source_definition(item, tenant_id) is None
    ]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={"message": "Source is not allowlisted", "source_ids": invalid},
        )
    jobs: list[JobState] = []
    queued_source_ids: list[str] = []
    skipped: list[str] = []
    in_flight: list[str] = []
    for current_tenant_id, current_source_id, _definition in source_entries:
        if _inflight_monitor_job_exists(current_source_id, current_tenant_id):
            in_flight.append(current_source_id)
            continue
        if not _reserve_agent_call(current_tenant_id):
            skipped.append(current_source_id)
            continue
        job = _start_job(
            query=(
                f"Monitor the historical allowlisted {current_source_id} snapshot. "
                "Report baseline_established, unchanged, or a verified material "
                "change; never invent an approval."
            ),
            user_id="driftline-scheduler",
            run_mode="monitor",
            background_tasks=background_tasks,
            tenant_id=current_tenant_id,
            source_id=current_source_id,
        )
        jobs.append(job)
        queued_source_ids.append(current_source_id)
    if not jobs and skipped:
        raise HTTPException(
            status_code=429, detail="Monitor rate limit reached; retry later."
        )
    return {
        "status": "queued",
        "source_ids": queued_source_ids,
        "jobs": [job.to_dict() for job in jobs],
        "skipped_source_ids": skipped,
        "in_flight_source_ids": in_flight,
        # Preserve the one-job response shape for a canary invocation.
        "job_id": jobs[0].job_id if len(jobs) == 1 else None,
    }


def _job_payload(job: JobState) -> dict[str, object]:
    payload = job.to_dict()
    if job.tenant_id is None:
        # Anonymous demo jobs are useful for judging, but callers can submit
        # arbitrary text. Never echo that text, raw model output, failure
        # details, or the opaque Cloud Tasks claim into public history.
        payload.pop("query", None)
        payload.pop("user_id", None)
        payload.pop("response", None)
        payload.pop("error", None)
        payload.pop("claim_id", None)
        if job.status == "failed":
            summary = "Public demo run failed; internal details are withheld."
        elif job.status == "complete":
            summary = "Run complete; evidence-bound workflow is available."
        elif job.status == "needs_approval":
            summary = "Evidence verified; waiting for human approval."
        elif job.status == "running":
            summary = "Agent run in progress."
        else:
            summary = "Awaiting durable agent execution."
        payload["public_summary"] = summary
    if job.workflow_id:
        try:
            payload["workflow"] = _resolve_workflow(job.workflow_id).to_dict()
        except KeyError:
            payload["workflow"] = None
    return payload


@app.get("/api/jobs/{job_id}")
def get_job(
    job_id: str,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict:
    try:
        job = _resolve_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _authorize_read_tenant(
        job,
        resource_id=job.job_id,
        operator=operator,
        tenant_id=tenant_id,
        approval_token=approval_token,
        identity_token=identity_token,
    )
    return _job_payload(job)


@app.post("/api/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    request: JobRetryRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    """Queue one bounded retry for a failed tenant job.

    The caller cannot replace the original query, source, tenant, or run mode.
    Anonymous/public jobs remain packet-safe and are retried from the normal
    public Run scan control instead of exposing a mutation endpoint.
    """
    try:
        failed_job = _resolve_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    if failed_job.tenant_id is None:
        raise HTTPException(
            status_code=403,
            detail="Public jobs can be rerun from the public scan control",
        )
    if failed_job.status != "failed":
        raise HTTPException(
            status_code=409,
            detail="Only terminally failed jobs can be retried",
        )
    identity = _verify_approval_mode(
        f"job-retry:{job_id}",
        request.operator,
        "signed",
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    if identity.get("tenant_id") != failed_job.tenant_id:
        raise HTTPException(status_code=403, detail="Job tenant mismatch")
    if source_definition(failed_job.source_id, identity["tenant_id"]) is None:
        raise HTTPException(status_code=422, detail="Job source is no longer allowlisted")
    # Cloud Tasks and browser retries can race across instances.  Return the
    # existing active successor instead of spending a second agent call.
    try:
        with _jobs_lock:
            recent_jobs = list(_jobs.values())
        recent_jobs.extend(list_jobs(limit=50))
    except Exception:
        logger.exception("Unable to inspect retry idempotency ledger for %s", job_id)
        recent_jobs = []
    existing = next(
        (
            candidate
            for candidate in recent_jobs
            if candidate.retry_of == failed_job.job_id
            and candidate.tenant_id == failed_job.tenant_id
            and candidate.status in {"queued", "running", "needs_approval", "complete"}
        ),
        None,
    )
    if existing is not None:
        return {
            "status": "already_queued",
            "retried_job_id": failed_job.job_id,
            "job": existing.to_dict(),
            "tenant_id": identity["tenant_id"],
            "source_id": failed_job.source_id,
        }
    if not _reserve_agent_call(identity["tenant_id"]):
        raise HTTPException(status_code=429, detail="Tenant agent rate limit reached; retry later.")
    retried = _start_job(
        query=failed_job.query,
        user_id=failed_job.user_id,
        run_mode=failed_job.run_mode,
        background_tasks=background_tasks,
        tenant_id=identity["tenant_id"],
        source_id=failed_job.source_id,
        retry_of=failed_job.job_id,
    )
    return {
        "status": "queued",
        "retried_job_id": failed_job.job_id,
        "job": retried.to_dict(),
        "tenant_id": identity["tenant_id"],
        "source_id": failed_job.source_id,
    }


@app.get("/api/ops/job-failures")
def get_job_failures(
    operator: str,
    tenant_id: str | None = None,
    limit: int = 50,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    """Return terminal async failures for the caller's tenant only.

    Cloud Tasks removes a task after its bounded retry policy is exhausted;
    this signed, metadata-only ledger preserves the operational signal without
    returning prompts, source bodies, exception text, or credentials.
    """
    identity = _verify_approval_mode(
        "job-failures",
        operator,
        "signed",
        approval_token,
        identity_token,
        tenant_id,
    )
    failures = list_job_failures(identity["tenant_id"], limit=limit)
    return {
        "status": "ok",
        "tenant_id": identity["tenant_id"],
        "failures": failures,
        "retention": f"bounded_{os.getenv('DRIFTLINE_RETENTION_DAYS', '30')}_days",
        "credential_values_exposed": False,
    }


@app.post("/api/jobs/{job_id}/run")
async def run_job(job_id: str, request: Request) -> dict:
    _verify_task_request(request)
    try:
        _resolve_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await _run_job(job_id)
    payload = _job_payload(_resolve_job(job_id))
    if payload.get("status") == "queued" and payload.get("error", "").startswith(
        "Transient"
    ):
        raise HTTPException(
            status_code=503, detail="Transient job failure; Cloud Tasks will retry"
        )
    return payload


@app.post("/api/agent/run")
async def run_agent(request: AgentRunRequest) -> dict:
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")
    signed_identity: dict[str, str] | None = None
    has_signed_fields = any(
        value is not None
        for value in (
            request.operator,
            request.tenant_id,
            request.approval_token,
            request.identity_token,
        )
    )
    if has_signed_fields:
        if not request.operator or not request.tenant_id:
            raise HTTPException(
                status_code=401,
                detail="Signed agent execution requires operator and tenant_id",
            )
        signed_identity = _verify_approval_mode(
            f"agent-run:{request.source_id}",
            request.operator,
            "signed",
            request.approval_token,
            request.identity_token,
            request.tenant_id,
        )
    bound_tenant = signed_identity.get("tenant_id") if signed_identity else None
    # A registered public URL belongs to its tenant and must never be
    # discoverable or runnable from the anonymous lane. Resolve the source
    # only after authenticating the optional tenant, so direct API operators
    # receive the same real monitor path as the console and scheduler.
    definition = source_definition(request.source_id, bound_tenant)
    if definition is None or (
        definition.get("dynamic") == "true" and bound_tenant is None
    ):
        raise HTTPException(status_code=422, detail="Source is not allowlisted")
    if not _reserve_agent_call(bound_tenant):
        raise HTTPException(
            status_code=429,
            detail="Live agent demo rate limit reached; retry later.",
        )
    if bound_tenant is None:
        # Anonymous direct runs are a judge surface, not a general-purpose
        # prompt proxy. Keep caller text out of Gemini and the public workflow
        # ledger while preserving the signed tenant lane for real operators.
        query = (
            f"Inspect the allowlisted {request.source_id} change, verify the "
            "evidence, map affected artifacts, and stop at the human approval "
            "gate."
        )
        user_id = "public-demo"
    else:
        query = (
            f"{request.query.strip()} Use the exact allowlisted source_id "
            f'"{request.source_id}". Do not choose a different source.'
        )
        user_id = request.user_id
    try:
        if bound_tenant:
            return await run_agent_task(
                query,
                user_id,
                run_mode="live",
                tenant_id=bound_tenant,
            )
        return await run_agent_task(query, user_id)
    except Exception as exc:
        logger.exception("Live ADK execution failed")
        raise HTTPException(
            status_code=503,
            detail="Live ADK execution is unavailable; check Google Cloud credentials.",
        ) from exc


@app.get("/api/workflows/{workflow_id}")
def get_workflow(
    workflow_id: str,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict:
    try:
        state = _resolve_workflow(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _authorize_read_tenant(
        state,
        resource_id=state.workflow_id,
        operator=operator,
        tenant_id=tenant_id,
        approval_token=approval_token,
        identity_token=identity_token,
    )
    return state.to_dict()


def _require_action_actor(actor: str) -> str:
    cleaned = actor.strip()
    if not cleaned or any(
        token in {"agent", "system", "gemini", "assistant"}
        for token in cleaned.casefold().split()
    ):
        raise HTTPException(status_code=400, detail="A named human actor is required")
    return cleaned


@app.get("/api/workflows/{workflow_id}/actions")
def get_actions(
    workflow_id: str,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> dict[str, object]:
    try:
        state = _resolve_workflow(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _authorize_read_tenant(
        state,
        resource_id=state.workflow_id,
        operator=operator,
        tenant_id=tenant_id,
        approval_token=approval_token,
        identity_token=identity_token,
    )
    return {"actions": state.action_items}


def _action_item(state: WorkflowState, item_id: str) -> dict[str, object]:
    item = next(
        (entry for entry in state.action_items if entry["item_id"] == item_id), None
    )
    if item is None:
        raise KeyError(f"Unknown action item: {item_id}")
    return item


def _action_event(state: WorkflowState, item_id: str, outcome: str, actor: str) -> None:
    state.events.append(
        {
            "event_id": f"event-{uuid4().hex[:12]}",
            "actor": "action_lifecycle",
            "outcome": f"{item_id}:{outcome}",
            "timestamp": utc_now(),
            "action_item_id": item_id,
            "human_actor": actor,
        }
    )
    state.updated_at = utc_now()


def _authorize_action_request(
    workflow_id: str, request: ActionItemRequest
) -> dict[str, str]:
    identity = _verify_approval_mode(
        workflow_id,
        request.actor,
        request.approval_mode,
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    _authorize_workflow_tenant(workflow_id, identity)
    if not _reserve_demo_mutation(identity.get("tenant_id")):
        raise HTTPException(
            status_code=429,
            detail="Action mutation rate limit reached for this tenant; retry later.",
        )
    return identity


def _action_transition(
    workflow_id: str,
    item_id: str,
    request: ActionItemRequest,
    transition: Callable[[WorkflowState, dict[str, object], str], None],
) -> dict:
    """Apply one idempotent action-item transition through workflow CAS."""
    _authorize_action_request(workflow_id, request)
    cleaned_actor = _require_action_actor(request.actor)

    def apply(state: WorkflowState) -> WorkflowState:
        if state.status.value != "complete":
            raise PolicyViolation("Actions are available after approval")
        transition(state, _action_item(state, item_id), cleaned_actor)
        if state.evidence is not None:
            state.change_card = build_change_card(
                workflow_id=state.workflow_id,
                evidence=state.evidence,
                impacts=state.impacts,
                impact_graph=state.impact_graph,
                data_mode=state.data_mode,
                approval=state.approval,
                action_items=state.action_items,
            )
        return state

    return _transition_workflow(workflow_id, "complete", apply).to_dict()


@app.post("/api/workflows/{workflow_id}/actions/{item_id}/claim")
def claim_action(workflow_id: str, item_id: str, request: ActionItemRequest) -> dict:
    try:

        def transition(
            state: WorkflowState, item: dict[str, object], actor: str
        ) -> None:
            if item.get("status") == ActionItemStatus.CLAIMED.value:
                if item.get("claimed_by") == actor:
                    return
                raise PolicyViolation("Action item is already claimed")
            if item.get("status") != ActionItemStatus.QUEUED.value:
                raise PolicyViolation("Action item is not queued")
            item.update(
                {
                    "status": ActionItemStatus.CLAIMED.value,
                    "claimed_by": actor,
                    "claimed_at": utc_now(),
                    "attempts": int(item.get("attempts", 0)) + 1,
                }
            )
            _action_event(state, item_id, "claimed", actor)

        return _action_transition(workflow_id, item_id, request, transition)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/actions/{item_id}/complete")
def complete_action(workflow_id: str, item_id: str, request: ActionItemRequest) -> dict:
    try:

        def transition(
            state: WorkflowState, item: dict[str, object], actor: str
        ) -> None:
            if item.get("status") == ActionItemStatus.COMPLETED.value:
                if item.get("completed_by") == actor or item.get("claimed_by") == actor:
                    return
                raise PolicyViolation(
                    "Only the claiming actor can complete this action"
                )
            if (
                item.get("status") != ActionItemStatus.CLAIMED.value
                or item.get("claimed_by") != actor
            ):
                raise PolicyViolation(
                    "Only the claiming actor can complete this action"
                )
            item.update(
                {
                    "status": ActionItemStatus.COMPLETED.value,
                    "completed_by": actor,
                    "completed_at": utc_now(),
                }
            )
            _action_event(state, item_id, "completed", actor)

        return _action_transition(workflow_id, item_id, request, transition)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/actions/{item_id}/fail")
def fail_action(workflow_id: str, item_id: str, request: ActionFailureRequest) -> dict:
    """Record a bounded human-visible failure so a queued retry is possible."""
    try:

        def transition(
            state: WorkflowState, item: dict[str, object], actor: str
        ) -> None:
            if item.get("status") == ActionItemStatus.FAILED.value:
                if (
                    item.get("failed_by") == actor
                    and item.get("failure_reason") == request.reason
                ):
                    return
                raise PolicyViolation("Action item is already failed")
            if (
                item.get("status") != ActionItemStatus.CLAIMED.value
                or item.get("claimed_by") != actor
            ):
                raise PolicyViolation("Only the claiming actor can fail this action")
            item.update(
                {
                    "status": ActionItemStatus.FAILED.value,
                    "failed_by": actor,
                    "failed_at": utc_now(),
                    "failure_reason": request.reason,
                }
            )
            _action_event(state, item_id, "failed", actor)

        return _action_transition(workflow_id, item_id, request, transition)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/actions/{item_id}/retry")
def retry_action(workflow_id: str, item_id: str, request: ActionItemRequest) -> dict:
    """Requeue a failed item; repeat retries by the same actor are idempotent."""
    try:

        def transition(
            state: WorkflowState, item: dict[str, object], actor: str
        ) -> None:
            if item.get("status") == ActionItemStatus.QUEUED.value:
                if item.get("retried_by") in (None, actor):
                    return
                raise PolicyViolation("Action item is already queued")
            if item.get("status") != ActionItemStatus.FAILED.value:
                raise PolicyViolation("Only a failed action can be retried")
            item.update(
                {
                    "status": ActionItemStatus.QUEUED.value,
                    "retried_by": actor,
                    "retried_at": utc_now(),
                    "retry_count": int(item.get("retry_count", 0)) + 1,
                }
            )
            _action_event(state, item_id, "retried", actor)

        return _action_transition(workflow_id, item_id, request, transition)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/actions/{item_id}/reverse")
def reverse_action(workflow_id: str, item_id: str, request: ActionItemRequest) -> dict:
    """Reversibly close an individual action item without deleting its audit."""
    try:

        def transition(
            state: WorkflowState, item: dict[str, object], actor: str
        ) -> None:
            if item.get("status") == ActionItemStatus.REVERSED.value:
                return
            if item.get("status") not in {
                ActionItemStatus.QUEUED.value,
                ActionItemStatus.CLAIMED.value,
                ActionItemStatus.COMPLETED.value,
                ActionItemStatus.FAILED.value,
            }:
                raise PolicyViolation("Action item cannot be reversed")
            item.update(
                {
                    "status": ActionItemStatus.REVERSED.value,
                    "reversed_by": actor,
                    "reversed_at": utc_now(),
                }
            )
            _action_event(state, item_id, "reversed", actor)

        return _action_transition(workflow_id, item_id, request, transition)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/workflows/{workflow_id}/packet", response_class=PlainTextResponse)
def get_packet(
    workflow_id: str,
    operator: str | None = None,
    tenant_id: str | None = None,
    approval_token: str | None = None,
    identity_token: str | None = None,
) -> str:
    try:
        state = _resolve_workflow(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _authorize_read_tenant(
        state,
        resource_id=state.workflow_id,
        operator=operator,
        tenant_id=tenant_id,
        approval_token=approval_token,
        identity_token=identity_token,
    )
    return packet_markdown(state)


@app.post("/api/workflows/{workflow_id}/approve")
def approve(workflow_id: str, request: ApprovalRequest) -> dict:
    approval_identity = _verify_approval_mode(
        workflow_id,
        request.approver,
        request.approval_mode,
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    _authorize_workflow_tenant(workflow_id, approval_identity)
    if not _reserve_demo_mutation(approval_identity.get("tenant_id")):
        raise HTTPException(
            status_code=429,
            detail="Workflow mutation rate limit reached for this tenant; retry later.",
        )
    try:

        def apply(current: WorkflowState) -> WorkflowState:
            try:
                validate_approval_choice(
                    current,
                    request.copilot_option_id,
                    request.decision,
                    request.artifact_decisions,
                    custom_override=request.copilot_artifact_override,
                    override_reason=request.copilot_override_reason,
                )
            except (ValueError, TypeError) as exc:
                raise PolicyViolation(str(exc)) from exc
            state = workflow_store.approve(
                current.workflow_id,
                request.approver,
                request.decision,
                request.artifact_decisions,
                approval_metadata={
                    "copilot_option_id": request.copilot_option_id,
                    "copilot_artifact_override": request.copilot_artifact_override,
                    **(
                        {"copilot_override_reason": request.copilot_override_reason.strip()}
                        if request.copilot_artifact_override
                        and request.copilot_override_reason
                        else {}
                    ),
                },
            )
            if state.approval is not None:
                state.approval["approval_identity"] = approval_identity
            return state

        state = _transition_workflow(
            workflow_id,
            "needs_approval",
            apply,
        )
        if state.action_record is not None:
            # Connector credentials are selected from the approved tenant, not
            # from deployment-wide environment variables. Keeping this opaque
            # tenant id on the action also lets a later signed undo resolve the
            # same binding after the approval object is cleared.
            state.action_record["tenant_id"] = approval_identity["tenant_id"]
        storage_info = persist_action_artifact(state, kind="active")
        operational_info = persist_operational_output(state, kind="active")
        connector_info = _connector_handoff_info(state, approval_identity)
        state.action_record = {
            **(state.action_record or {}),
            **storage_info,
            **operational_info,
            **connector_info,
            "operational_side_effect": operational_info.get(
                "operational_status", "not_configured"
            ),
            "external_write_authorized": approval_identity.get("scope") == "configured",
            "external_write": any(
                connector_info.get(f"{name}_external_write", False)
                or connector_info.get("external_write", False)
                for name, _, _ in _CONNECTOR_HANDOFFS
            ),
            "external_systems_changed": any(
                connector_info.get(f"{name}_external_write", False)
                or connector_info.get("external_write", False)
                for name, _, _ in _CONNECTOR_HANDOFFS
            ),
        }
        if storage_info.get("storage_status") != "not_configured":
            compare_and_set_workflow(state, "complete")
            workflow_store.restore(state)
        _sync_jobs_for_workflow(workflow_id, state.status.value)
        return state.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/dismiss")
def dismiss(workflow_id: str, request: DismissRequest) -> dict:
    approval_identity = _verify_approval_mode(
        workflow_id,
        request.actor,
        request.approval_mode,
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    _authorize_workflow_tenant(workflow_id, approval_identity)
    if not _reserve_demo_mutation(approval_identity.get("tenant_id")):
        raise HTTPException(
            status_code=429,
            detail="Workflow mutation rate limit reached for this tenant; retry later.",
        )
    try:

        def apply(current: WorkflowState) -> WorkflowState:
            state = workflow_store.dismiss(
                current.workflow_id,
                request.actor,
                request.reason,
            )
            if state.approval is not None:
                state.approval["approval_identity"] = approval_identity
            return state

        state = _transition_workflow(workflow_id, "needs_approval", apply)
        _sync_jobs_for_workflow(workflow_id, state.status.value)
        return state.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/undo")
def undo(workflow_id: str, request: UndoRequest) -> dict:
    approval_identity = _verify_approval_mode(
        workflow_id,
        request.actor,
        request.approval_mode,
        request.approval_token,
        request.identity_token,
        request.tenant_id,
    )
    _authorize_workflow_tenant(workflow_id, approval_identity)
    if not _reserve_demo_mutation(approval_identity.get("tenant_id")):
        raise HTTPException(
            status_code=429,
            detail="Workflow mutation rate limit reached for this tenant; retry later.",
        )
    try:

        def apply(current: WorkflowState) -> WorkflowState:
            if (
                current.action_record
                and current.action_record.get("external_write")
                and approval_identity.get("scope") != "configured"
            ):
                raise PolicyViolation(
                    "Signed approval is required to reverse configured connector writes"
                )
            state = workflow_store.undo(current.workflow_id, request.actor)
            state.events[-1]["approval_identity"] = approval_identity
            return state

        state = _transition_workflow(
            workflow_id,
            "complete",
            apply,
        )
        storage_info = persist_action_artifact(state, kind="rollback")
        operational_info = persist_operational_output(state, kind="rollback")
        connector_info = _connector_handoff_info(state, approval_identity, reverse=True)
        state.action_record = {
            **(state.action_record or {}),
            **storage_info,
            **operational_info,
            **connector_info,
            "operational_side_effect": operational_info.get(
                "operational_status", "not_configured"
            ),
            "external_write_authorized": approval_identity.get("scope") == "configured",
            "external_write": any(
                connector_info.get(f"{name}_external_write", False)
                or connector_info.get("external_write", False)
                for name, _, _ in _CONNECTOR_HANDOFFS
            ),
            "external_systems_changed": any(
                connector_info.get(f"{name}_external_write", False)
                or connector_info.get("external_write", False)
                for name, _, _ in _CONNECTOR_HANDOFFS
            ),
        }
        if storage_info.get("storage_status") != "not_configured":
            compare_and_set_workflow(state, "needs_approval")
            workflow_store.restore(state)
        _sync_jobs_for_workflow(workflow_id, state.status.value)
        return state.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


static_dir = Path(os.getenv("DRIFTLINE_STATIC_DIR", "/app/static"))
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="console")
