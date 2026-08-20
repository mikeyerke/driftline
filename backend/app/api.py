from __future__ import annotations

import asyncio
import base64
import copy
import hashlib
import hmac
import json
import logging
import os
import secrets
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Literal
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
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
    write_secret_version,
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
    list_jobs,
    list_outcome_measurements,
    list_tenant_memberships,
    list_workflows,
    load_job,
    load_salesforce_connection,
    load_tenant,
    load_workflow,
    persist_connector_binding,
    persist_job,
    persist_outcome_measurement,
    persist_salesforce_connection,
    persist_salesforce_oauth_state,
    persist_tenant,
    persist_tenant_membership,
    persist_workflow,
    update_jobs_for_workflow,
)
from .simulator import simulate_scenarios
from .source import (
    list_allowlisted_sources,
    list_source_history,
    register_operator_source,
    scheduler_source_entries,
    source_definition,
    source_definitions,
    source_registry_health,
)
from .tenant import (
    principal_for_claims,
    principal_for_hmac,
    public_demo_principal,
    tenant_connector_secret_name,
    validate_connector_name,
    validate_tenant_id,
)
from .workflow import PolicyViolation, packet_markdown, workflow_store

logger = logging.getLogger("driftline.api")
app = FastAPI(title="Driftline API", version="0.2.0")
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
        "Content-Security-Policy",
        "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    )
    # Cloud Run terminates TLS before forwarding to Uvicorn, so the app often
    # sees an internal HTTP scheme even for the public HTTPS URL. The service
    # has no HTTP-only public route; emit HSTS unconditionally so the browser
    # never downgrades the deployed console.
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )
    return response


class ApprovalRequest(BaseModel):
    approver: str = Field(min_length=1, max_length=120)
    tenant_id: str | None = Field(default=None, min_length=3, max_length=63)
    decision: str = Field(default="grandfather_existing_customers", max_length=64)
    artifact_decisions: dict[str, str] | None = None
    copilot_option_id: str | None = Field(default=None, min_length=3, max_length=64)
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
    run_mode: Literal["demo", "monitor"] = "demo"
    source_id: str = Field(default="public/pricing", min_length=1, max_length=80)
    operator: str = Field(default="demo-operator", min_length=1, max_length=120)
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
    parser: Literal["html", "text"] = "html"
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
MAX_JOB_ATTEMPTS = _positive_int("DRIFTLINE_MAX_JOB_ATTEMPTS", 3)

_salesforce_oauth_states: dict[str, dict[str, object]] = {}
_salesforce_oauth_lock = Lock()

_jobs: dict[str, JobState] = {}
_jobs_lock = Lock()
_workflow_transition_lock = Lock()
_background_tasks: set[asyncio.Task[None]] = set()


def _reserve_agent_call(tenant_id: str | None = None) -> bool:
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
        if len(times) >= AGENT_MAX_CALLS:
            return False
        times.append(now)
        return True


def _reserve_demo_mutation(tenant_id: str | None = None) -> bool:
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
        if len(times) >= DEMO_MAX_MUTATIONS:
            return False
        times.append(now)
        return True


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
    if scope == "sandbox_packet_only":
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
    except ConnectorError as exc:
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

    The public judge console intentionally runs in ``demo`` mode and creates
    sandbox packets only. A configured operator lane can use a Google OIDC
    identity for the allowlisted operator email, or an HMAC token generated
    from the dedicated approval secret as an isolated break-glass path;
    unsigned public names are rejected before the workflow policy engine runs.
    """
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
            "scope": "sandbox_packet_only",
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
            from google.auth.transport.requests import Request as GoogleRequest
            from google.oauth2 import id_token

            claims = id_token.verify_oauth2_token(
                identity_token.removeprefix("Bearer ").strip(),
                GoogleRequest(),
                audience=audience,
            )
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


async def _run_job(job_id: str) -> None:
    if not _claim_job_for_run(job_id):
        logger.info("Job %s was already claimed or completed", job_id)
        return
    job = _resolve_job(job_id)
    try:
        if job.run_mode == "demo" and job.tenant_id is None:
            result = await run_agent_task(job.query, job.user_id)
        elif job.tenant_id is None:
            result = await run_agent_task(job.query, job.user_id, job.run_mode)
        else:
            result = await run_agent_task(
                job.query,
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
    except Exception:
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
    _set_job(job)


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
) -> JobState:
    job = JobState(
        job_id=f"job-{uuid4().hex[:12]}",
        query=query,
        user_id=user_id,
        tenant_id=tenant_id,
        run_mode=run_mode,
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


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "driftline-agent",
        "persistence": os.getenv("DRIFTLINE_PERSISTENCE", "memory"),
        "async_jobs": _tasks_enabled(),
    }


def _salesforce_secret_name(tenant_id: str) -> str:
    safe = validate_tenant_id(tenant_id)
    # Secret names are deliberately deterministic, bounded, and never based
    # on an email address or arbitrary user input.
    return f"driftline-sf-{safe}"[:100]


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
    result = durable or payload
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
        secret_name = _salesforce_secret_name(tenant_id)
        write_secret_version(secret_name, refresh_token)
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
    tenant_id = identity["tenant_id"]
    connection = load_salesforce_connection(tenant_id)
    if not connection or connection.get("status") != "connected_read_only":
        raise HTTPException(
            status_code=409, detail="Salesforce is not connected for this tenant"
        )
    config = SalesforceConfig.from_env()
    try:
        refresh_token = read_secret(str(connection["secret_name"]))
        token = refresh_salesforce_token(config, refresh_token)
        client = SalesforceReadOnlyClient(
            config,
            access_token=str(token["access_token"]),
            instance_url=str(connection["instance_url"]),
        )
        result = client.health_summary()
        return {"tenant_id": tenant_id, **result}
    except ConnectorError as exc:
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
    delete_salesforce_connection(identity["tenant_id"])
    return {
        "status": "disconnected",
        "tenant_id": identity["tenant_id"],
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
    return {
        "status": "registered",
        "source": {
            key: value
            for key, value in definition.items()
            if key not in {"registered_by", "registered_at"}
        },
        "approval_identity": approval_identity,
        "next_step": "Run a signed monitor tick for this source to establish its baseline.",
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
        jobs = [
            job
            for job in _jobs.values()
            if job.tenant_id is None
            or (identity is not None and job.tenant_id == identity.get("tenant_id"))
        ]
    if (
        not jobs
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    ):
        candidates = list_jobs(20)
        jobs = [
            job
            for job in candidates
            if job.tenant_id is None
            or (identity is not None and job.tenant_id == identity.get("tenant_id"))
        ]
    workflows = [
        state
        for state in workflow_store._runs.values()
        if state.tenant_id is None
        or (identity is not None and state.tenant_id == identity.get("tenant_id"))
    ]
    if (
        not workflows
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    ):
        candidates = list_workflows(20)
        workflows = [
            state
            for state in candidates
            if state.tenant_id is None
            or (identity is not None and state.tenant_id == identity.get("tenant_id"))
        ]
    source_health = source_registry_health(
        tenant_id=identity.get("tenant_id") if identity else None
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
            "monitor_max_sources": _positive_int("DRIFTLINE_MONITOR_MAX_SOURCES", 5),
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
                "tenant_collection": "driftline_tenants",
                "membership_collection": "driftline_tenant_memberships",
            },
            "tenant_auth": {
                "configured": bool(os.getenv("DRIFTLINE_TENANT_MEMBERS", "").strip()),
                "durable_memberships": True,
                "default_tenant": os.getenv(
                    "DRIFTLINE_DEFAULT_TENANT_ID", "driftline-demo"
                ),
                "role_model": ["viewer", "operator", "owner"],
            },
        },
        "jobs": {
            "total": len(jobs),
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
            "user_input_scope": "none; connector targets come only from deployment configuration",
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
    secret_name = tenant_connector_secret_name(tenant_id, safe_connector)
    status = "active"
    try:
        if not read_secret(secret_name).strip():
            status = "pending_secret"
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
            "configured_by": identity.get("email") or identity.get("identity"),
            "updated_at": utc_now(),
        }
    )
    return {
        "status": status,
        "tenant_id": tenant_id,
        "connector": safe_connector,
        "secret_name": secret_name,
        "scope": binding["scope"],
        "credential_value_accepted": False,
        "next_step": (
            "Binding is active; connector calls will use this tenant secret."
            if status == "active"
            else "Provision the deterministic secret, then repeat this signed owner request."
        ),
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
    memberships = list_tenant_memberships(identity["tenant_id"])
    return {
        "tenant": {
            key: value
            for key, value in tenant.items()
            if key not in {"token", "secret_value", "access_token", "refresh_token"}
        },
        "role": identity["role"],
        "connector_binding_count": len(bindings),
        "membership_count": len(memberships),
        "credential_values_exposed": False,
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
        jobs = [
            job
            for job in _jobs.values()
            if job.tenant_id is None
            or (identity is not None and job.tenant_id == identity.get("tenant_id"))
        ]
    if (
        not jobs
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    ):
        candidates = list_jobs(50)
        jobs = [
            job
            for job in candidates
            if job.tenant_id is None
            or (identity is not None and job.tenant_id == identity.get("tenant_id"))
        ]
    workflows = [
        state
        for state in workflow_store._runs.values()
        if state.tenant_id is None
        or (identity is not None and state.tenant_id == identity.get("tenant_id"))
    ]
    if (
        not workflows
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    ):
        candidates = list_workflows(50)
        workflows = [
            state
            for state in candidates
            if state.tenant_id is None
            or (identity is not None and state.tenant_id == identity.get("tenant_id"))
        ]
    action_items = [item for state in workflows for item in state.action_items]
    source_health = source_registry_health(
        tenant_id=identity.get("tenant_id") if identity else None
    )
    change_cards = [state.change_card for state in workflows if state.change_card]
    materiality_cards = [card.get("materiality") or {} for card in change_cards]
    closure_cards = [card.get("closure") or {} for card in change_cards]
    external_writes = sum(
        bool((state.action_record or {}).get("external_write")) for state in workflows
    )
    reversed_workflows = sum(
        any(event.get("detail") == "decision_reopened" for event in state.events)
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
        "scope": "observed_driftline_sandbox_records",
        "observed": {
            "jobs": len(jobs),
            "workflows": len(workflows),
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
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
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
        workflows = [
            state.to_dict()
            for state in workflow_store._runs.values()
            if state.tenant_id is None
            or (identity is not None and state.tenant_id == identity.get("tenant_id"))
        ]
    if (
        not workflows
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    ):
        workflows = [
            state.to_dict()
            for state in list_workflows(bounded_limit)
            if state.tenant_id is None
            or (identity is not None and state.tenant_id == identity.get("tenant_id"))
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
    try:
        evidence = get_visual_evidence(asset_id, mode)
    except MultimodalUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    payload = evidence.to_dict()
    payload["before_url"] = f"/api/multimodal/assets/{asset_id}/before?mode={mode}"
    payload["after_url"] = f"/api/multimodal/assets/{asset_id}/after?mode={mode}"
    return payload


@app.post("/api/multimodal/analyze")
async def analyze_multimodal(request: MultimodalAnalysisRequest) -> dict[str, object]:
    """Run Gemini vision only on the bounded allowlisted visual pair."""
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
    if request.run_mode == "monitor":
        monitor_identity = _verify_approval_mode(
            f"monitor:{request.source_id}",
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
    query = (
        f"{request.query.strip()} Use the exact allowlisted source_id "
        f'"{request.source_id}". Do not choose a different source.'
    )
    job = _start_job(
        query=query,
        user_id=request.user_id,
        run_mode=request.run_mode,
        background_tasks=background_tasks,
        tenant_id=tenant_id,
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
        candidates = sorted(
            _jobs.values(), key=lambda item: item.created_at or "", reverse=True
        )
    if (
        not candidates
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    ):
        candidates = list_jobs(20)
    jobs = [
        job
        for job in candidates
        if job.tenant_id is None
        or (identity is not None and job.tenant_id == identity.get("tenant_id"))
    ][:bounded_limit]
    return {"jobs": [job.to_dict() for job in jobs]}


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
    for current_tenant_id, current_source_id, _definition in source_entries:
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
        # Preserve the one-job response shape for a canary invocation.
        "job_id": jobs[0].job_id if len(jobs) == 1 else None,
    }


def _job_payload(job: JobState) -> dict[str, object]:
    payload = job.to_dict()
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
    if not _reserve_agent_call():
        raise HTTPException(
            status_code=429,
            detail="Live agent demo rate limit reached; retry later.",
        )
    try:
        return await run_agent_task(request.query, request.user_id)
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
                )
            except (ValueError, TypeError) as exc:
                raise PolicyViolation(str(exc)) from exc
            state = workflow_store.approve(
                current.workflow_id,
                request.approver,
                request.decision,
                request.artifact_decisions,
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
