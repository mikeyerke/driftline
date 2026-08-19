import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app import api
from app.api import app
from app.models import JobState

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_approval_and_undo_round_trip() -> None:
    started = client.post("/api/workflows/demo")
    assert started.status_code == 200
    workflow_id = started.json()["workflow_id"]

    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "complete"

    undone = client.post(
        f"/api/workflows/{workflow_id}/undo",
        json={"actor": "Demo operator"},
    )
    assert undone.status_code == 200
    assert undone.json()["status"] == "needs_approval"


def test_approved_action_item_can_be_claimed_and_completed_by_same_human() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    actions = approved.json()["action_items"]
    assert len(actions) == 4
    item_id = actions[0]["item_id"]

    claimed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    assert claimed.status_code == 200
    assert (
        next(
            item
            for item in claimed.json()["action_items"]
            if item["item_id"] == item_id
        )["status"]
        == "claimed"
    )

    wrong_actor = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Taylor Lee"},
    )
    assert wrong_actor.status_code == 409

    completed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )
    assert completed.status_code == 200
    assert (
        next(
            item
            for item in completed.json()["action_items"]
            if item["item_id"] == item_id
        )["status"]
        == "completed"
    )


def test_live_agent_query_is_bounded_before_execution() -> None:
    response = client.post("/api/agent/run", json={"query": "x" * 2001})
    assert response.status_code == 422


def test_packet_endpoint_is_available_after_approval() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )

    assert approved.status_code == 200
    packet = client.get(f"/api/workflows/{workflow_id}/packet")
    assert packet.status_code == 200
    assert "External systems changed: **No**" in packet.text


def test_async_job_records_agent_trace_and_workflow(monkeypatch) -> None:
    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        state = api.workflow_store.start_demo()
        return {
            "workflow_id": state.workflow_id,
            "model": "test-model",
            "execution_mode": "google_adk",
            "tool_calls": ["inspect_source_change", "get_workflow_state"],
            "event_count": 4,
            "response": "Evidence verified; waiting for a human decision.",
            "agent_trace": {"model": "test-model", "event_count": 4},
        }

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post("/api/jobs/demo", json={"query": "test"})

    assert response.status_code == 200
    queued = response.json()
    payload = client.get(f"/api/jobs/{queued['job_id']}").json()
    assert payload["status"] == "needs_approval"
    assert payload["workflow"]["status"] == "needs_approval"
    assert payload["tool_calls"] == [
        "inspect_source_change",
        "get_workflow_state",
    ]
    assert payload["workflow"]["agent_trace"]["model"] == "test-model"

    workflow_id = payload["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Alex Kim",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    assert client.get(f"/api/jobs/{queued['job_id']}").json()["status"] == "complete"


def test_identity_free_demo_mutations_are_rate_limited(monkeypatch) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 1)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()

    first = client.post("/api/workflows/demo")
    second = client.post("/api/workflows/demo")

    assert first.status_code == 200
    assert second.status_code == 429
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()


@pytest.mark.asyncio
async def test_duplicate_job_delivery_cannot_run_agent_twice(monkeypatch) -> None:
    calls = 0

    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        nonlocal calls
        calls += 1
        state = api.workflow_store.start_demo()
        return {"workflow_id": state.workflow_id, "model": "test-model"}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()
    job = JobState(job_id="job-idempotent", query="test")
    api._set_job(job)

    await api._run_job(job.job_id)
    await api._run_job(job.job_id)

    assert calls == 1
    assert api._resolve_job(job.job_id).run_attempts == 1


@pytest.mark.asyncio
async def test_monitor_job_completes_without_inventing_a_workflow(monkeypatch) -> None:
    async def fake_run_agent_task(query: str, user_id: str, run_mode: str) -> dict:
        assert run_mode == "monitor"
        return {
            "model": "test-model",
            "execution_mode": "google_adk",
            "tool_calls": ["inspect_source_change"],
            "event_count": 2,
            "response": "No material source change was found.",
            "source_status": "unchanged",
            "change_detected": False,
        }

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    job = JobState(job_id="job-monitor-unchanged", query="monitor", run_mode="monitor")
    api._set_job(job)

    await api._run_job(job.job_id)

    result = api._resolve_job(job.job_id)
    assert result.status == "complete"
    assert result.workflow_id is None
    assert result.response == "No material source change was found."


def test_approval_requires_explicit_signed_token_when_signed_mode_enabled(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "signed")
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]

    rejected = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Alex Kim"},
    )
    assert rejected.status_code == 403

    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    token = hmac.new(
        secret.encode(), f"{workflow_id}:Alex Kim".encode(), hashlib.sha256
    ).hexdigest()
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Alex Kim",
            "approval_mode": "signed",
            "approval_token": token,
        },
    )
    assert approved.status_code == 200
    assert approved.json()["approval"]["approval_identity"]["mode"] == "signed"


def test_failed_workflow_cas_restores_pending_state(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    monkeypatch.setattr(api, "compare_and_set_workflow", lambda state, expected: False)

    response = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )

    assert response.status_code == 409
    assert client.get(f"/api/workflows/{workflow_id}").json()["status"] == (
        "needs_approval"
    )
