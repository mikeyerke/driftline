from concurrent.futures import ThreadPoolExecutor

import pytest

from app import multimodal


@pytest.fixture(autouse=True)
def clear_visual_caches() -> None:
    multimodal._DEMO_EVIDENCE_CACHE.clear()
    multimodal._PUBLIC_ASSET_CACHE.clear()
    multimodal._PUBLIC_ASSET_FAILURES.clear()


class _Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, _limit: int) -> bytes:
        return self.body


def test_visual_registry_rejects_arbitrary_asset_ids() -> None:
    with pytest.raises(multimodal.MultimodalUnavailable, match="not_allowlisted"):
        multimodal.get_visual_evidence("arbitrary-url", mode="demo")


def test_public_visual_pair_is_bounded_and_hash_bound(monkeypatch) -> None:
    payloads = iter([b"before-image", b"after-image"])
    monkeypatch.setattr(
        multimodal,
        "urlopen",
        lambda request, timeout: _Response(next(payloads)),
    )

    evidence = multimodal.get_visual_evidence("promise-card", mode="live")

    assert evidence.data_mode == "public_source"
    assert evidence.before.body == b"before-image"
    assert evidence.after.body == b"after-image"
    assert evidence.before.mime_type == "image/jpeg"
    assert evidence.after.snapshot_hash != evidence.before.snapshot_hash
    assert len(evidence.evidence_hash) == 64
    assert (
        evidence.to_dict()["before"]["snapshot_hash"] == evidence.before.snapshot_hash
    )


def test_live_fetch_failure_never_uses_synthetic_fallback(monkeypatch) -> None:
    def fail(request, timeout):
        raise OSError("offline")

    monkeypatch.setattr(multimodal, "urlopen", fail)

    with pytest.raises(multimodal.MultimodalUnavailable, match="fetch_failed"):
        multimodal.get_visual_evidence("promise-card", mode="live")


def test_demo_fetch_failure_is_labeled_synthetic(monkeypatch) -> None:
    multimodal._DEMO_EVIDENCE_CACHE.clear()
    monkeypatch.setattr(
        multimodal,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(OSError("offline")),
    )

    evidence = multimodal.get_visual_evidence("promise-card", mode="demo")

    assert evidence.data_mode == "synthetic_demo"
    assert evidence.before.source_url.startswith("synthetic://")
    assert evidence.after.mime_type == "image/svg+xml"


def test_demo_byte_route_reuses_pair_wide_fallback(monkeypatch) -> None:
    multimodal._DEMO_EVIDENCE_CACHE.clear()
    calls = 0

    def fetch(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("after unavailable")
        return _Response(b"live-before")

    monkeypatch.setattr(multimodal, "urlopen", fetch)
    evidence = multimodal.get_visual_evidence("promise-card", mode="demo")
    asset = multimodal.visual_asset_bytes("promise-card", "before", mode="demo")

    assert evidence.data_mode == "synthetic_demo"
    assert asset.snapshot_hash == evidence.before.snapshot_hash
    assert asset.data_mode == "synthetic_demo"
    assert calls == 2


def test_asset_byte_route_fetches_only_requested_side(monkeypatch) -> None:
    requested_urls: list[str] = []

    def fetch(request, timeout):
        requested_urls.append(request.full_url)
        return _Response(b"before-image")

    monkeypatch.setattr(multimodal, "urlopen", fetch)

    asset = multimodal.visual_asset_bytes("promise-card", "before", mode="live")

    assert asset.side == "before"
    assert len(requested_urls) == 1
    assert requested_urls[0].endswith("change-operations-primary.jpg")


def test_live_pair_and_byte_routes_reuse_two_upstream_fetches(monkeypatch) -> None:
    requested_urls: list[str] = []

    def fetch(request, timeout):
        requested_urls.append(request.full_url)
        return _Response(request.full_url.encode())

    monkeypatch.setattr(multimodal, "urlopen", fetch)

    first = multimodal.get_visual_evidence("promise-card", mode="live")
    before = multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    after = multimodal.visual_asset_bytes("promise-card", "after", mode="live")
    second = multimodal.get_visual_evidence("promise-card", mode="live")

    assert len(requested_urls) == 2
    assert before.snapshot_hash == first.before.snapshot_hash
    assert after.snapshot_hash == first.after.snapshot_hash
    assert second.evidence_hash == first.evidence_hash


def test_concurrent_live_asset_misses_are_single_flight(monkeypatch) -> None:
    calls = 0

    def fetch(request, timeout):
        nonlocal calls
        calls += 1
        return _Response(b"one-pinned-image")

    monkeypatch.setattr(multimodal, "urlopen", fetch)
    with ThreadPoolExecutor(max_workers=20) as executor:
        assets = list(
            executor.map(
                lambda _: multimodal.visual_asset_bytes(
                    "promise-card", "before", mode="live"
                ),
                range(20),
            )
        )

    assert calls == 1
    assert len({asset.snapshot_hash for asset in assets}) == 1


def test_live_asset_cache_is_scoped_to_configured_ref(monkeypatch) -> None:
    calls = 0

    def fetch(request, timeout):
        nonlocal calls
        calls += 1
        return _Response(request.full_url.encode())

    monkeypatch.setattr(multimodal, "urlopen", fetch)
    monkeypatch.setenv("DRIFTLINE_VISUAL_ASSET_REF", "a" * 40)
    first = multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    monkeypatch.setenv("DRIFTLINE_VISUAL_ASSET_REF", "b" * 40)
    second = multimodal.visual_asset_bytes("promise-card", "before", mode="live")

    assert calls == 2
    assert first.source_url != second.source_url


def test_mutable_visual_ref_cache_expires_without_affecting_pinned_refs(
    monkeypatch,
) -> None:
    calls = 0
    now = 100.0

    def fetch(request, timeout):
        nonlocal calls
        calls += 1
        return _Response(f"image-{calls}".encode())

    monkeypatch.setattr(multimodal, "urlopen", fetch)
    monkeypatch.setattr(multimodal, "monotonic", lambda: now)
    monkeypatch.setenv("DRIFTLINE_VISUAL_ASSET_REF", "main")
    first = multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    now += multimodal._PUBLIC_ASSET_MUTABLE_REF_TTL_SECONDS + 1
    refreshed = multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    assert calls == 2
    assert first.snapshot_hash != refreshed.snapshot_hash

    monkeypatch.setenv("DRIFTLINE_VISUAL_ASSET_REF", "a" * 40)
    pinned = multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    now += multimodal._PUBLIC_ASSET_MUTABLE_REF_TTL_SECONDS + 1
    reused = multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    assert calls == 3
    assert pinned.snapshot_hash == reused.snapshot_hash


def test_live_fetch_failure_has_bounded_backoff_and_retries(monkeypatch) -> None:
    calls = 0
    now = 100.0

    def fetch(request, timeout):
        nonlocal calls
        calls += 1
        raise OSError("offline")

    monkeypatch.setattr(multimodal, "urlopen", fetch)
    monkeypatch.setattr(multimodal, "monotonic", lambda: now)
    with pytest.raises(multimodal.MultimodalUnavailable, match="fetch_failed"):
        multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    with pytest.raises(multimodal.MultimodalUnavailable, match="fetch_backoff"):
        multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    assert calls == 1

    now += multimodal.PUBLIC_ASSET_FAILURE_BACKOFF_SECONDS + 1
    with pytest.raises(multimodal.MultimodalUnavailable, match="fetch_failed"):
        multimodal.visual_asset_bytes("promise-card", "before", mode="live")
    assert calls == 2


def test_vision_output_must_copy_combined_evidence_hash() -> None:
    payload = {
        "evidence_hash": "a" * 64,
        "summary": "The after visual adds an approval state.",
        "before_observation": "The workflow is waiting for review.",
        "after_observation": "The workflow shows approved outputs.",
        "material_change": True,
        "confidence": 0.91,
    }

    result = multimodal.validate_vision_analysis(payload, "a" * 64)

    assert result.material_change is True
    with pytest.raises(multimodal.MultimodalUnavailable, match="hash_mismatch"):
        multimodal.validate_vision_analysis(payload, "b" * 64)


def test_synthetic_analysis_does_not_call_gemini(monkeypatch) -> None:
    multimodal._DEMO_EVIDENCE_CACHE.clear()
    monkeypatch.setattr(
        multimodal,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(OSError("offline")),
    )
    monkeypatch.setattr(
        multimodal,
        "_run_vision_model",
        lambda evidence: (_ for _ in ()).throw(AssertionError("model called")),
    )

    result = multimodal.analyze_visual_evidence("promise-card", mode="demo")

    assert result["mode"] == "synthetic_demo"
    assert result["analysis"]["confidence"] == 0.0
