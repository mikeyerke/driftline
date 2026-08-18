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
from .models import JobState, WorkflowState
from .persistence import (
    claim_job,
    compare_and_set_workflow,
    load_job,
    load_workflow,
    persist_job,
    persist_workflow,
    update_jobs_for_workflow,
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
        )
    )
    try:
        client.create_task(parent=parent, task=task)
    except TaskAlreadyExists:
        logger.info("Cloud Task for %s already exists; treating enqueue as success", job.job_id)


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
        result = await run_agent_task(job.query, job.user_id)
        workflow_id = result.get("workflow_id")
        if not workflow_id:
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


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "driftline-agent",
        "persistence": os.getenv("DRIFTLINE_PERSISTENCE", "memory"),
        "async_jobs": _tasks_enabled(),
    }


@app.post("/api/workflows/demo")
def start_demo() -> dict:
    """Legacy deterministic fixture endpoint retained for reproducible tests."""
    if not _reserve_demo_mutation():
        raise HTTPException(
            status_code=429,
            detail="Demo workflow rate limit reached; retry later.",
        )
    state = workflow_store.start_demo()
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
    job = JobState(
        job_id=f"job-{uuid4().hex[:12]}",
        query=request.query,
        user_id=request.user_id,
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
        _sync_jobs_for_workflow(workflow_id, state.status.value)
        return state.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


static_dir = Path(os.getenv("DRIFTLINE_STATIC_DIR", "/app/static"))
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="console")
