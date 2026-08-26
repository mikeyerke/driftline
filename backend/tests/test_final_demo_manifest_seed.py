import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "prepare_final_demo_manifest.py"
SPEC = importlib.util.spec_from_file_location("prepare_final_demo_manifest", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def release_identity() -> dict[str, object]:
    sha = "1" * 40
    return {
        "verified_at": "2026-08-26T17:00:00Z",
        "source_url": "https://driftline-ops.web.app/",
        "release_sha": sha,
        "health_sha": sha,
        "public_main_sha": sha,
        "cloud_run_revision": "driftline-12345-abc",
        "cloud_build_id": "12345678-1234-1234-1234-123456789abc",
        "image_digest": "sha256:" + "2" * 64,
        "traffic_percent": 100,
        "trace_evaluation_id": "eval-release-123",
        "trace_release_sha": sha,
    }


def test_manifest_seed_binds_every_verified_release_identity(tmp_path: Path) -> None:
    identity_path = tmp_path / "release-identity.json"
    output_path = tmp_path / "final-demo.seed.json"
    identity_path.write_text(json.dumps(release_identity()))

    assert MODULE.build_manifest_seed(identity_path, output_path) == output_path
    manifest = json.loads(output_path.read_text())

    assert manifest["release_sha"] == "1" * 40
    assert manifest["health_sha"] == manifest["release_sha"]
    assert manifest["public_main_sha"] == manifest["release_sha"]
    assert manifest["cloud_run_revision"] == "driftline-12345-abc"
    assert manifest["cloud_build_id"] == release_identity()["cloud_build_id"]
    assert manifest["image_digest"] == "sha256:" + "2" * 64
    assert len(manifest["release_identity_receipt_sha256"]) == 64
    assert manifest["preapproval_background_workflow_visible"] is False
    assert manifest["candidate_watermark_absent"] is False
    assert output_path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("health_sha", "3" * 40, "must match"),
        ("traffic_percent", 99, "100 percent traffic"),
        ("source_url", "https://example.com/", "not canonical"),
        ("trace_evaluation_id", "", "trace evaluation ID"),
    ],
)
def test_release_identity_mismatch_fails_closed(
    field: str, value: object, message: str
) -> None:
    identity = release_identity()
    identity[field] = value
    with pytest.raises(MODULE.ManifestSeedError, match=message):
        MODULE.validate_release_identity(identity)


def test_manifest_seed_refuses_overwrite(tmp_path: Path) -> None:
    identity_path = tmp_path / "release-identity.json"
    output_path = tmp_path / "final-demo.seed.json"
    identity_path.write_text(json.dumps(release_identity()))
    output_path.write_text("do not replace")
    with pytest.raises(MODULE.ManifestSeedError, match="already exists"):
        MODULE.build_manifest_seed(identity_path, output_path)


def test_manifest_seed_refuses_repository_output() -> None:
    with pytest.raises(MODULE.ManifestSeedError, match="outside the repository"):
        MODULE.validate_output_path(ROOT / "final-demo.seed.json")
