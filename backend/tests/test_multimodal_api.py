from fastapi.testclient import TestClient

from app import api, multimodal


class _Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, _limit: int) -> bytes:
        return self.body


def test_visual_evidence_and_asset_routes_are_same_origin(monkeypatch) -> None:
    payloads = iter([b"before", b"after", b"before", b"after"])
    monkeypatch.setattr(
        multimodal,
        "urlopen",
        lambda request, timeout: _Response(next(payloads)),
    )
    client = TestClient(api.app)

    evidence = client.get("/api/multimodal/evidence/promise-card?mode=live")
    asset = client.get("/api/multimodal/assets/promise-card/before?mode=live")

    assert evidence.status_code == 200
    assert evidence.json()["data_mode"] == "public_source"
    assert len(evidence.json()["evidence_hash"]) == 64
    assert asset.status_code == 200
    assert asset.headers["content-type"].startswith("image/png")


def test_demo_vision_endpoint_returns_explicit_synthetic_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        multimodal,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(OSError("offline")),
    )
    client = TestClient(api.app)

    response = client.post(
        "/api/multimodal/analyze",
        json={"asset_id": "promise-card", "mode": "demo"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "synthetic_demo"
    assert response.json()["analysis"]["confidence"] == 0.0


def test_scenario_endpoint_returns_no_write_counterfactuals() -> None:
    state = api.workflow_store.start_demo()
    client = TestClient(api.app)

    response = client.get(f"/api/workflows/{state.workflow_id}/scenarios")

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["scenarios"]] == [
        "approve",
        "grandfather",
        "defer",
    ]
    assert payload["external_writes"] is False
