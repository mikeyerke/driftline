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
    assert asset.headers["content-type"].startswith("image/jpeg")


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


def test_live_visual_metadata_degrades_to_labelled_demo_pair(monkeypatch) -> None:
    monkeypatch.setattr(
        multimodal,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(OSError("offline")),
    )
    client = TestClient(api.app)

    response = client.get("/api/multimodal/evidence/promise-card?mode=live")

    assert response.status_code == 200
    assert response.json()["data_mode"] == "synthetic_demo"
    assert response.json()["fallback_reason"] == "visual_asset_fetch_failed"
    assert "mode=demo" in response.json()["before_url"]
    assert "mode=demo" in response.json()["after_url"]


def test_multimodal_analysis_has_a_bounded_retryable_quota(monkeypatch) -> None:
    monkeypatch.setattr(api, "MULTIMODAL_MAX_CALLS", 1)
    monkeypatch.setattr(api, "MULTIMODAL_WINDOW_SECONDS", 3600)
    api._multimodal_call_times.clear()
    monkeypatch.setattr(
        api,
        "analyze_visual_evidence",
        lambda _asset_id, _mode: {"mode": "synthetic_demo"},
    )
    client = TestClient(api.app)

    first = client.post(
        "/api/multimodal/analyze",
        json={"asset_id": "promise-card", "mode": "demo"},
    )
    second = client.post(
        "/api/multimodal/analyze",
        json={"asset_id": "promise-card", "mode": "demo"},
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"].isdigit()
    assert "quota" in second.json()["detail"].casefold()


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
