import hashlib
import importlib.util
import json
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "render_release_submission.py"
SPEC = importlib.util.spec_from_file_location("render_release_submission", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


IDENTITY = {
    "release_sha": "1" * 40,
    "revision": "driftline-12345-abc",
    "build_id": "12345678-1234-1234-1234-123456789abc",
    "digest": "sha256:" + "2" * 64,
    "video_sha256": "3" * 64,
    "captions_sha256": "4" * 64,
}


def valid_manifest() -> dict[str, object]:
    manifest: dict[str, object] = {
        "recorded_at": "2026-08-26T09:00:00-05:00",
        "source_url": "https://driftline-ops.web.app/",
        "release_sha": IDENTITY["release_sha"],
        "health_sha": IDENTITY["release_sha"],
        "public_main_sha": IDENTITY["release_sha"],
        "cloud_run_revision": IDENTITY["revision"],
        "cloud_build_id": IDENTITY["build_id"],
        "image_digest": IDENTITY["digest"],
        "video_sha256": IDENTITY["video_sha256"],
        "captions_sha256": IDENTITY["captions_sha256"],
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


def write_png_header(path: Path, width: int = 1200, height: int = 675) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + struct.pack(">II", width, height)
    )


def write_gallery_manifest(path: Path, gallery: list[Path]) -> Path:
    assets = {}
    for key, image in zip(
        ("hero", "generation_1", "generation_2"), gallery, strict=True
    ):
        width, height = MODULE._png_dimensions(image)
        assets[key] = {
            "path": str(image.resolve()),
            "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            "width": width,
            "height": height,
        }
    proof_video = path.parent / "continuous-proof.mp4"
    proof_video.write_bytes(b"release-proof" * 10_000)
    path.write_text(
        json.dumps(
            {
                "captured_at": "2026-08-26T09:05:00-05:00",
                "source_url": "https://driftline-ops.web.app/",
                "release_sha": IDENTITY["release_sha"],
                "build_id": IDENTITY["build_id"],
                "continuous_browser_session": True,
                "assets": assets,
                "proof_video": {
                    "path": str(proof_video.resolve()),
                    "sha256": hashlib.sha256(proof_video.read_bytes()).hexdigest(),
                    "frames": 500,
                    "pointer_clicks": 7,
                },
            }
        )
    )
    return proof_video


def test_valid_manifest_returns_one_release_identity() -> None:
    assert MODULE._validate_manifest(valid_manifest()) == IDENTITY


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("health_sha", "5" * 40, "must match"),
        ("candidate_watermark_absent", False, "candidate_watermark_absent"),
        ("video_sha256", "0" * 64, "nonzero"),
        ("approval_to_reopen_continuous", False, "approval_to_reopen_continuous"),
        (
            "preapproval_background_workflow_visible",
            False,
            "preapproval_background_workflow_visible",
        ),
        ("duration_seconds", 236, "below 3:56"),
        ("google_cloud_proof_timestamp_seconds", 170, "ten seconds"),
    ],
)
def test_manifest_mismatch_or_missing_proof_fails_closed(
    field: str, value: object, message: str
) -> None:
    manifest = valid_manifest()
    manifest[field] = value
    with pytest.raises(MODULE.ReleaseRenderError, match=message):
        MODULE._validate_manifest(manifest)


@pytest.mark.parametrize(
    "url",
    [
        "https://youtu.be/abcdefghijk",
        "https://www.youtube.com/watch?v=abcdefghijk",
        "https://vimeo.com/123456789",
        "https://player.vimeo.com/video/123456789",
    ],
)
def test_video_url_accepts_specific_youtube_or_vimeo_video(url: str) -> None:
    assert MODULE._validate_video_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://youtu.be/abcdefghijk",
        "https://youtube.com/",
        "https://youtube.com/channel/abcdefghijk",
        "https://youtube.com/watch?v=too-short",
        "https://youtu.be/too-short",
        "https://vimeo.com/channels/staffpicks",
        "https://example.com/watch?v=abcdefghijk",
    ],
)
def test_video_url_rejects_non_specific_or_unapproved_host(url: str) -> None:
    with pytest.raises(MODULE.ReleaseRenderError):
        MODULE._validate_video_url(url)


def test_gallery_requires_distinct_release_sized_pngs(tmp_path: Path) -> None:
    gallery = [tmp_path / f"release-{index}.png" for index in range(3)]
    for path in gallery:
        write_png_header(path)
    MODULE._validate_gallery(gallery)

    write_png_header(gallery[0], 1199, 675)
    with pytest.raises(MODULE.ReleaseRenderError, match="too small"):
        MODULE._validate_gallery(gallery)


def test_gallery_rejects_candidate_custody_filename(tmp_path: Path) -> None:
    gallery = [
        tmp_path / "release-hero.png",
        tmp_path / "candidate-generation-1.png",
        tmp_path / "release-generation-2.png",
    ]
    for path in gallery:
        write_png_header(path)
    with pytest.raises(MODULE.ReleaseRenderError, match="candidate custody"):
        MODULE._validate_gallery(gallery)


def test_gallery_manifest_binds_same_release_session_and_asset_hashes(
    tmp_path: Path,
) -> None:
    gallery = [tmp_path / f"release-{index}.png" for index in range(3)]
    for image in gallery:
        write_png_header(image)
    manifest_path = tmp_path / "gallery.json"
    proof_video = write_gallery_manifest(manifest_path, gallery)

    validated = MODULE._validate_gallery_manifest(
        manifest_path, IDENTITY, gallery, proof_video
    )
    assert validated["release_sha"] == IDENTITY["release_sha"]
    assert validated["continuous_browser_session"] is True
    assert set(validated["assets"]) == {"hero", "generation_1", "generation_2"}


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("release_sha", "5" * 40, "release SHA"),
        ("build_id", "87654321-4321-4321-4321-cba987654321", "build ID"),
        ("continuous_browser_session", False, "continuous browser session"),
        ("source_url", "https://example.com/", "canonical hosted"),
    ],
)
def test_gallery_manifest_rejects_mixed_custody(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    gallery = [tmp_path / f"release-{index}.png" for index in range(3)]
    for image in gallery:
        write_png_header(image)
    manifest_path = tmp_path / "gallery.json"
    proof_video = write_gallery_manifest(manifest_path, gallery)
    manifest = json.loads(manifest_path.read_text())
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(MODULE.ReleaseRenderError, match=message):
        MODULE._validate_gallery_manifest(manifest_path, IDENTITY, gallery, proof_video)


def test_gallery_manifest_rejects_changed_asset(tmp_path: Path) -> None:
    gallery = [tmp_path / f"release-{index}.png" for index in range(3)]
    for image in gallery:
        write_png_header(image)
    manifest_path = tmp_path / "gallery.json"
    proof_video = write_gallery_manifest(manifest_path, gallery)
    gallery[1].write_bytes(gallery[1].read_bytes() + b"changed")
    with pytest.raises(MODULE.ReleaseRenderError, match="hash does not match"):
        MODULE._validate_gallery_manifest(manifest_path, IDENTITY, gallery, proof_video)


def test_gallery_manifest_rejects_changed_proof_video(tmp_path: Path) -> None:
    gallery = [tmp_path / f"release-{index}.png" for index in range(3)]
    for image in gallery:
        write_png_header(image)
    manifest_path = tmp_path / "gallery.json"
    proof_video = write_gallery_manifest(manifest_path, gallery)
    proof_video.write_bytes(proof_video.read_bytes() + b"changed")
    with pytest.raises(MODULE.ReleaseRenderError, match="proof-video hash"):
        MODULE._validate_gallery_manifest(manifest_path, IDENTITY, gallery, proof_video)


def test_output_must_stay_outside_repository(tmp_path: Path) -> None:
    assert (
        MODULE._validate_output_target(tmp_path / "render")
        == (tmp_path / "render").resolve()
    )
    with pytest.raises(MODULE.ReleaseRenderError, match="outside the repository"):
        MODULE._validate_output_target(ROOT / "rendered-release")


def test_actual_final_media_bytes_must_match_manifest(tmp_path: Path) -> None:
    video = tmp_path / "final.mp4"
    captions = tmp_path / "final.srt"
    video.write_bytes(b"final-video-bytes")
    captions.write_text("1\n00:00:00,000 --> 00:00:01,000\nDriftline\n")
    manifest = valid_manifest()
    manifest["video_sha256"] = hashlib.sha256(video.read_bytes()).hexdigest()
    manifest["captions_sha256"] = hashlib.sha256(captions.read_bytes()).hexdigest()
    MODULE._validate_final_media_files(manifest, video, captions)


@pytest.mark.parametrize("changed", ["video", "captions"])
def test_changed_final_media_is_rejected(tmp_path: Path, changed: str) -> None:
    video = tmp_path / "final.mp4"
    captions = tmp_path / "final.srt"
    video.write_bytes(b"final-video-bytes")
    captions.write_text("1\n00:00:00,000 --> 00:00:01,000\nDriftline\n")
    manifest = valid_manifest()
    manifest["video_sha256"] = hashlib.sha256(video.read_bytes()).hexdigest()
    manifest["captions_sha256"] = hashlib.sha256(captions.read_bytes()).hexdigest()
    if changed == "video":
        video.write_bytes(video.read_bytes() + b"changed")
    else:
        captions.write_text(captions.read_text() + "changed")
    with pytest.raises(MODULE.ReleaseRenderError, match="hash does not match"):
        MODULE._validate_final_media_files(manifest, video, captions)


def test_story_and_form_render_exact_release_without_stale_markers(
    tmp_path: Path,
) -> None:
    video_url = "https://youtu.be/abcdefghijk"
    story = MODULE.render_devpost_story(
        (ROOT / "submission" / "DEVPOST.md").read_text(), IDENTITY, video_url
    )
    packet = MODULE.render_form_packet(
        (ROOT / "devpost-submission.md").read_text(),
        IDENTITY,
        video_url,
        [
            tmp_path / "hero.png",
            tmp_path / "generation-1.png",
            tmp_path / "generation-2.png",
        ],
        tmp_path / "architecture.png",
        None,
        None,
    )
    MODULE._assert_final(story, label="story")
    MODULE._assert_final(packet, label="packet")
    for rendered in (story, packet):
        assert IDENTITY["release_sha"] in rendered
        assert "10/10 policy checks" in rendered
        assert video_url in rendered
    assert "Not claimed" in packet


def test_architecture_render_replaces_candidate_badge_and_pending_gate() -> None:
    rendered = MODULE.render_architecture(
        (
            ROOT
            / "submission"
            / "assets"
            / "driftline-decision-twin-candidate-architecture.svg"
        ).read_text(),
        IDENTITY,
    )
    assert "RELEASE VERIFIED" in rendered
    assert "UNRELEASED CANDIDATE" not in rendered
    assert "release proof required before publication" not in rendered
    assert IDENTITY["release_sha"][:12] in rendered
    assert IDENTITY["build_id"] in rendered


def test_template_drift_fails_closed() -> None:
    source = (
        (ROOT / "submission" / "DEVPOST.md")
        .read_text()
        .replace("7/7 policy checks", "changed checks", 1)
    )
    with pytest.raises(MODULE.ReleaseRenderError, match="expected 2 occurrence"):
        MODULE.render_devpost_story(source, IDENTITY, "https://youtu.be/abcdefghijk")
