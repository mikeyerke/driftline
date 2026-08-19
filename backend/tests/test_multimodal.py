import pytest

from app import multimodal


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
    assert evidence.before.mime_type == "image/png"
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
    monkeypatch.setattr(
        multimodal,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(OSError("offline")),
    )

    evidence = multimodal.get_visual_evidence("promise-card", mode="demo")

    assert evidence.data_mode == "synthetic_demo"
    assert evidence.before.source_url.startswith("synthetic://")
    assert evidence.after.mime_type == "image/svg+xml"


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
