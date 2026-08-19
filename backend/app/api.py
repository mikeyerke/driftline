from __future__ import annotations

import asyncio
import copy
import hashlib
import hmac
import json
import logging
import os
from collections import deque
from collections.abc import Callable
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Literal
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
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
    ConnectorError,
    execute_jira_handoff,
    reverse_jira_handoff,
)
from .models import ActionItemStatus, JobState, WorkflowState, utc_now
from .persistence import (
    claim_job,
    compare_and_set_workflow,
    list_jobs,
    load_job,
    load_workflow,
    persist_job,
    persist_workflow,
    update_jobs_for_workflow,
)
from .source import (
    SOURCE_DEFINITIONS,
    list_allowlisted_sources,
    list_source_history,
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
    decision: str = Field(default="grandfather_existing_customers", max_length=64)
    artifact_decisions: dict[str, str] | None = None
    approval_mode: Literal["demo", "signed"] = "demo"
    approval_token: str | None = Field(default=None, max_length=256)


class UndoRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    approval_mode: Literal["demo", "signed"] = "demo"
    approval_token: str | None = Field(default=None, max_length=256)


class ActionItemRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)


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


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


AGENT_MAX_CALLS = _positive_int("DRIFTLINE_AGENT_MAX_CALLS", 10)
AGENT_WINDOW_SECONDS = _positive_int("DRIFTLINE_AGENT_WINDOW_SECONDS", 3600)
_agent_call_times: deque[float] = deque()
_agent_call_lock = Lock()

DEMO_MAX_MUTATIONS = _positive_int("DRIFTLINE_DEMO_MAX_MUTATIONS", 30)
DEMO_WINDOW_SECONDS = _positive_int("DRIFTLINE_DEMO_WINDOW_SECONDS", 3600)
_demo_mutation_times: deque[float] = deque()
_demo_mutation_lock = Lock()

_jobs: dict[str, JobState] = {}
_jobs_lock = Lock()
_workflow_transition_lock = Lock()
_background_tasks: set[asyncio.Task[None]] = set()


def _reserve_agent_call() -> bool:
    now = monotonic()
    cutoff = now - AGENT_WINDOW_SECONDS
    with _agent_call_lock:
        while _agent_call_times and _agent_call_times[0] <= cutoff:
            _agent_call_times.popleft()
        if len(_agent_call_times) >= AGENT_MAX_CALLS:
            return False
        _agent_call_times.append(now)
        return True


def _reserve_demo_mutation() -> bool:
    now = monotonic()
    cutoff = now - DEMO_WINDOW_SECONDS
    with _demo_mutation_lock:
        while _demo_mutation_times and _demo_mutation_times[0] <= cutoff:
            _demo_mutation_times.popleft()
        if len(_demo_mutation_times) >= DEMO_MAX_MUTATIONS:
            return False
        _demo_mutation_times.append(now)
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
) -> dict[str, str]:
    """Bound public decisions to an explicit demo or signed approval mode.

    The public judge console intentionally runs in ``demo`` mode and creates
    sandbox packets only.  A deployment that wants real operator identity can
    set ``DRIFTLINE_APPROVAL_MODE=signed`` and provide an HMAC token generated
    from the dedicated approval secret; unsigned public names are then
    rejected before the workflow policy engine runs.
    """
    configured = os.getenv("DRIFTLINE_APPROVAL_MODE", "demo").casefold()
    if mode != configured:
        raise HTTPException(status_code=403, detail="Approval mode is not enabled")
    cleaned = actor.strip()
    if mode == "demo":
        return {
            "mode": "demo",
            "identity": "named_demo_actor",
            "scope": "sandbox_packet_only",
        }
    secret = os.getenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", "")
    if not secret or not token:
        raise HTTPException(status_code=401, detail="Signed approval is required")
    message = f"{workflow_id}:{cleaned}".encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid signed approval")
    return {"mode": "signed", "identity": "signed_operator", "scope": "configured"}


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
        if job.run_mode == "demo":
            result = await run_agent_task(job.query, job.user_id)
        else:
            result = await run_agent_task(job.query, job.user_id, job.run_mode)
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
        job.status = "failed"
        job.error = "The agent job failed before producing a workflow. Retry the scan."
    _set_job(job)


def _schedule_local_job(job: JobState) -> None:
    task = asyncio.create_task(_run_job(job.job_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _start_job(
    *, query: str, user_id: str, run_mode: str, background_tasks: BackgroundTasks
) -> JobState:
    job = JobState(
        job_id=f"job-{uuid4().hex[:12]}",
        query=query,
        user_id=user_id,
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


@app.get("/api/sources")
def get_sources() -> dict[str, object]:
    """Expose the deliberately small source registry to the monitor UI."""
    return {"sources": list_allowlisted_sources()}


@app.get("/api/sources/{source_id:path}/history")
def get_source_history(source_id: str, limit: int = 12) -> dict[str, object]:
    if source_id not in SOURCE_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Source is not allowlisted")
    bounded_limit = max(1, min(limit, 50))
    return {
        "source_id": source_id,
        "append_only": True,
        "observations": list_source_history(source_id, bounded_limit),
    }


@app.post("/api/workflows/demo")
def start_demo(source_id: str = "public/pricing") -> dict:
    """Legacy deterministic fixture endpoint retained for reproducible tests."""
    if not _reserve_demo_mutation():
        raise HTTPException(
            status_code=429,
            detail="Demo workflow rate limit reached; retry later.",
        )
    if source_id not in SOURCE_DEFINITIONS:
        raise HTTPException(status_code=422, detail="Source is not allowlisted")
    definition = SOURCE_DEFINITIONS[source_id]
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
    if not _reserve_agent_call():
        raise HTTPException(
            status_code=429,
            detail="Live agent demo rate limit reached; retry later.",
        )
    if request.source_id not in SOURCE_DEFINITIONS:
        raise HTTPException(status_code=422, detail="Source is not allowlisted")
    query = (
        f"{request.query.strip()} Use the exact allowlisted source_id "
        f'"{request.source_id}". Do not choose a different source.'
    )
    job = _start_job(
        query=query,
        user_id=request.user_id,
        run_mode=request.run_mode,
        background_tasks=background_tasks,
    )
    return job.to_dict()


@app.get("/api/jobs")
def get_jobs(limit: int = 8) -> dict[str, object]:
    """Expose bounded operator history without exposing arbitrary data."""
    bounded_limit = max(1, min(limit, 20))
    with _jobs_lock:
        jobs = sorted(
            _jobs.values(), key=lambda item: item.created_at or "", reverse=True
        )[:bounded_limit]
    if (
        not jobs
        and os.getenv("DRIFTLINE_PERSISTENCE", "memory").casefold() == "firestore"
    ):
        jobs = list_jobs(bounded_limit)
    return {"jobs": [job.to_dict() for job in jobs]}


@app.post("/api/scheduler/tick")
async def scheduler_tick(request: Request, background_tasks: BackgroundTasks) -> dict:
    """Start one historical source-monitor run from Cloud Scheduler."""
    _verify_scheduler_request(request)
    if not _reserve_agent_call():
        raise HTTPException(
            status_code=429, detail="Monitor rate limit reached; retry later."
        )
    job = _start_job(
        query=(
            "Monitor the historical allowlisted public/pricing snapshot. "
            "Report baseline_established, unchanged, or a verified material "
            "change; never invent an approval."
        ),
        user_id="driftline-scheduler",
        run_mode="monitor",
        background_tasks=background_tasks,
    )
    return job.to_dict()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        job = _resolve_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = job.to_dict()
    if job.workflow_id:
        try:
            payload["workflow"] = _resolve_workflow(job.workflow_id).to_dict()
        except KeyError:
            payload["workflow"] = None
    return payload


@app.post("/api/jobs/{job_id}/run")
async def run_job(job_id: str, request: Request) -> dict:
    _verify_task_request(request)
    try:
        _resolve_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await _run_job(job_id)
    return get_job(job_id)


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
def get_workflow(workflow_id: str) -> dict:
    try:
        return _resolve_workflow(workflow_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _require_action_actor(actor: str) -> str:
    cleaned = actor.strip()
    if not cleaned or cleaned.casefold() in {"agent", "system", "gemini"}:
        raise HTTPException(status_code=400, detail="A named human actor is required")
    return cleaned


@app.get("/api/workflows/{workflow_id}/actions")
def get_actions(workflow_id: str) -> dict[str, object]:
    try:
        state = _resolve_workflow(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"actions": state.action_items}


@app.post("/api/workflows/{workflow_id}/actions/{item_id}/claim")
def claim_action(workflow_id: str, item_id: str, request: ActionItemRequest) -> dict:
    actor = _require_action_actor(request.actor)

    def apply(state: WorkflowState) -> WorkflowState:
        if state.status.value != "complete":
            raise PolicyViolation("Actions are available after approval")
        item = next(
            (entry for entry in state.action_items if entry["item_id"] == item_id), None
        )
        if item is None:
            raise KeyError(f"Unknown action item: {item_id}")
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
        state.events.append(
            {
                "event_id": f"event-{uuid4().hex[:12]}",
                "actor": "action_lifecycle",
                "outcome": f"{item_id}:claimed",
                "timestamp": utc_now(),
                "action_item_id": item_id,
                "human_actor": actor,
            }
        )
        state.updated_at = utc_now()
        return state

    try:
        return _transition_workflow(workflow_id, "complete", apply).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/workflows/{workflow_id}/actions/{item_id}/complete")
def complete_action(workflow_id: str, item_id: str, request: ActionItemRequest) -> dict:
    actor = _require_action_actor(request.actor)

    def apply(state: WorkflowState) -> WorkflowState:
        if state.status.value != "complete":
            raise PolicyViolation("Actions are available after approval")
        item = next(
            (entry for entry in state.action_items if entry["item_id"] == item_id), None
        )
        if item is None:
            raise KeyError(f"Unknown action item: {item_id}")
        if (
            item.get("status") != ActionItemStatus.CLAIMED.value
            or item.get("claimed_by") != actor
        ):
            raise PolicyViolation("Only the claiming actor can complete this action")
        item.update(
            {
                "status": ActionItemStatus.COMPLETED.value,
                "completed_by": actor,
                "completed_at": utc_now(),
            }
        )
        state.events.append(
            {
                "event_id": f"event-{uuid4().hex[:12]}",
                "actor": "action_lifecycle",
                "outcome": f"{item_id}:completed",
                "timestamp": utc_now(),
                "action_item_id": item_id,
                "human_actor": actor,
            }
        )
        state.updated_at = utc_now()
        return state

    try:
        return _transition_workflow(workflow_id, "complete", apply).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/workflows/{workflow_id}/packet", response_class=PlainTextResponse)
def get_packet(workflow_id: str) -> str:
    try:
        state = _resolve_workflow(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return packet_markdown(state)


@app.post("/api/workflows/{workflow_id}/approve")
def approve(workflow_id: str, request: ApprovalRequest) -> dict:
    if not _reserve_demo_mutation():
        raise HTTPException(
            status_code=429,
            detail="Demo workflow rate limit reached; retry later.",
        )
    approval_identity = _verify_approval_mode(
        workflow_id,
        request.approver,
        request.approval_mode,
        request.approval_token,
    )
    try:

        def apply(current: WorkflowState) -> WorkflowState:
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
        storage_info = persist_action_artifact(state, kind="active")
        operational_info = persist_operational_output(state, kind="active")
        try:
            jira_info = execute_jira_handoff(state)
        except ConnectorError as exc:
            logger.warning("Jira handoff failed: %s", exc)
            jira_info = {"jira_status": "failed", "external_write": False}
        state.action_record = {
            **(state.action_record or {}),
            **storage_info,
            **operational_info,
            **jira_info,
            "operational_side_effect": operational_info.get(
                "operational_status", "not_configured"
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


@app.post("/api/workflows/{workflow_id}/undo")
def undo(workflow_id: str, request: UndoRequest) -> dict:
    if not _reserve_demo_mutation():
        raise HTTPException(
            status_code=429,
            detail="Demo workflow rate limit reached; retry later.",
        )
    approval_identity = _verify_approval_mode(
        workflow_id,
        request.actor,
        request.approval_mode,
        request.approval_token,
    )
    try:

        def apply(current: WorkflowState) -> WorkflowState:
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
        try:
            jira_info = reverse_jira_handoff(state)
        except ConnectorError as exc:
            logger.warning("Jira reversal failed: %s", exc)
            jira_info = {"jira_status": "failed", "external_write": False}
        state.action_record = {
            **(state.action_record or {}),
            **storage_info,
            **operational_info,
            **jira_info,
            "operational_side_effect": operational_info.get(
                "operational_status", "not_configured"
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
