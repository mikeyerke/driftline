from fastapi.testclient import TestClient

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
