from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "verify_submission_readiness", ROOT / "scripts" / "verify_submission_readiness.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_png_header(path: Path, width: int, height: int) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + struct.pack(">II", width, height)
    )


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


def final_manifest(receipt_hash: str, video_hash: str, captions_hash: str) -> dict[str, object]:
    identity = release_identity()
    manifest: dict[str, object] = {
        "recorded_at": "2026-08-26T17:10:00Z",
        "source_url": identity["source_url"],
        "release_sha": identity["release_sha"],
        "health_sha": identity["release_sha"],
        "public_main_sha": identity["release_sha"],
        "cloud_run_revision": identity["cloud_run_revision"],
        "cloud_build_id": identity["cloud_build_id"],
        "image_digest": identity["image_digest"],
        "release_identity_receipt_sha256": receipt_hash,
        "video_sha256": video_hash,
        "captions_sha256": captions_hash,
        "duration_seconds": 178,
        "first_agent_action_timestamp_seconds": 10,
        "human_approval_timestamp_seconds": 75,
        "bounded_action_receipt_timestamp_seconds": 82,
        "generation_2_timestamp_seconds": 112,
        "google_cloud_proof_type": "cloud_run_url",
        "google_cloud_proof_timestamp_seconds": 160,
    }
    for key in (
        "first_agent_action_visible",
        "preapproval_background_workflow_visible",
        "continuous_native_take",
        "setup_and_loading_omitted",
        "approval_to_reopen_continuous",
        "release_proof_visible",
        "google_cloud_proof_visible",
        "google_cloud_proof_identity_matches_release",
        "candidate_watermark_absent",
        "named_human_approval_visible",
        "bounded_action_receipt_visible",
        "generation_2_reopen_visible",
        "generation_1_lineage_visible",
        "external_writes_none_visible",
        "secrets_reviewed",
    ):
        manifest[key] = True
    return manifest


def valid_attestations() -> dict[str, object]:
    return {
        "reviewed_at": "2026-08-26T12:00:00-05:00",
        "entrant_name": "Example Entrant",
        "eligibility_confirmed": True,
        "ownership_rights_confirmed": True,
        "originality_disclosure_confirmed": True,
        "official_rules_reviewed": True,
        "final_entry_reviewed": True,
        "public_video_logged_out_verified": True,
        "submission_authorized": True,
    }


def test_attestations_require_every_owner_affirmation(tmp_path: Path) -> None:
    path = tmp_path / "attestations.json"
    value = valid_attestations()
    value["submission_authorized"] = False
    path.write_text(json.dumps(value))
    with pytest.raises(MODULE.SubmissionReadinessError, match="submission_authorized"):
        MODULE.validate_attestations(path)


def test_valid_attestations_return_no_identity(tmp_path: Path) -> None:
    path = tmp_path / "attestations.json"
    path.write_text(json.dumps(valid_attestations()))
    assert MODULE.validate_attestations(path)["status"] == "affirmed"


def test_ready_gate_resolution_does_not_require_submission_or_pm_evidence() -> None:
    gates = [
        "deploy_exact_public_main_candidate",
        "record_and_publish_exact_release_video",
        "entrant_eligibility_ownership_and_rules_attestations",
    ]
    assert MODULE.resolve_ready_gates(
        gates, release_ready=True, attestations_ready=True
    ) == []


def test_ready_gate_resolution_preserves_unproved_gates() -> None:
    gates = [
        "deploy_exact_public_main_candidate",
        "record_and_publish_exact_release_video",
        "entrant_eligibility_ownership_and_rules_attestations",
    ]
    assert MODULE.resolve_ready_gates(
        gates, release_ready=False, attestations_ready=True
    ) == [
        "deploy_exact_public_main_candidate",
        "record_and_publish_exact_release_video",
    ]


def test_repository_attestation_template_is_safely_unaffirmed() -> None:
    template = json.loads(
        (ROOT / "submission/entrant-attestations.template.json").read_text()
    )
    assert set(template) == MODULE.ATTESTATION_FIELDS
    assert template["entrant_name"] == ""
    assert all(template[field] is False for field in MODULE.TRUE_ATTESTATIONS)


def test_cli_exposes_no_release_or_media_verification_bypass() -> None:
    source = (ROOT / "scripts/verify_submission_readiness.py").read_text()
    assert "--skip-current-release-check" not in source
    assert "--skip-media-verifier" not in source


def test_release_media_and_rendered_packet_form_one_hash_bound_chain(
    tmp_path: Path,
) -> None:
    receipt_path = tmp_path / "release-receipt.json"
    receipt_path.write_text(json.dumps(release_identity()))
    video_path = tmp_path / "final.mp4"
    captions_path = tmp_path / "final.srt"
    video_path.write_bytes(b"verified-final-video")
    captions_path.write_text("verified captions")
    manifest_path = tmp_path / "final-manifest.json"
    manifest_path.write_text(
        json.dumps(
            final_manifest(
                sha256(receipt_path), sha256(video_path), sha256(captions_path)
            )
        )
    )

    expected = MODULE.validate_release_media(
        release_identity_path=receipt_path,
        final_manifest_path=manifest_path,
        video_path=video_path,
        captions_path=captions_path,
        video_url="https://youtu.be/abcdefghijk",
        run_media_verifier=False,
        verify_current_release=False,
    )

    packet = tmp_path / "packet"
    packet.mkdir()
    for name in MODULE.PACKET_FILES - {"release-identity.json"}:
        (packet / name).write_bytes(f"verified {name}".encode())
    (packet / "driftline-final-demo-release.srt").write_bytes(
        captions_path.read_bytes()
    )
    gallery_names = (
        "decision-twin-hero-release.png",
        "decision-twin-generation-1-release.png",
        "decision-twin-generation-2-receipt-release.png",
    )
    for name in gallery_names:
        write_png_header(packet / name, 1600, 900)
    write_png_header(packet / "driftline-final-demo-review-sheet.png", 1920, 1080)
    write_png_header(
        packet / "driftline-decision-twin-release-architecture.png", 1600, 900
    )
    release_identity_payload = {
        **expected,
        "gallery_sha256": {name: sha256(packet / name) for name in gallery_names},
        "submission_files_sha256": {
            name: sha256(packet / name)
            for name in ("DEVPOST.release.md", "devpost-submission.release.md")
        },
        "verified_media": {
            "video_sha256": expected["video_sha256"],
            "captions_file": "driftline-final-demo-release.srt",
            "captions_sha256": sha256(packet / "driftline-final-demo-release.srt"),
            "review_sheet_file": "driftline-final-demo-review-sheet.png",
            "review_sheet_sha256": sha256(
                packet / "driftline-final-demo-review-sheet.png"
            ),
        },
        "architecture_svg_sha256": sha256(
            packet / "driftline-decision-twin-release-architecture.svg"
        ),
        "architecture_png_sha256": sha256(
            packet / "driftline-decision-twin-release-architecture.png"
        ),
        "gallery_capture_sha256": sha256(packet / "release-gallery-capture.json"),
    }
    (packet / "release-identity.json").write_text(
        json.dumps(release_identity_payload)
    )
    MODULE.validate_release_packet(packet, expected)

    (packet / "DEVPOST.release.md").write_text("tampered")
    with pytest.raises(MODULE.SubmissionReadinessError, match="hash mismatch"):
        MODULE.validate_release_packet(packet, expected)


def test_release_packet_rejects_unexpected_hash_paths(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    packet.mkdir()
    for name in MODULE.PACKET_FILES:
        (packet / name).write_text("placeholder")
    expected = {
        key: "value"
        for key in (
            "release_sha",
            "revision",
            "build_id",
            "digest",
            "release_identity_receipt_sha256",
            "video_sha256",
            "captions_sha256",
            "video_url",
        )
    }
    identity = {
        **expected,
        "gallery_sha256": {"../outside.png": "0" * 64},
        "submission_files_sha256": {"DEVPOST.release.md": "0" * 64},
    }
    (packet / "release-identity.json").write_text(json.dumps(identity))
    with pytest.raises(MODULE.SubmissionReadinessError, match="fields differ"):
        MODULE.validate_release_packet(packet, expected)
