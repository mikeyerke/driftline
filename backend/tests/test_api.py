from fastapi.testclient import TestClient

from app import api
from app.api import app

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
