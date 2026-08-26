#!/usr/bin/env python3
"""Render release-bound submission artifacts without changing public main."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SHA_RE = re.compile(r"[0-9a-f]{40}")
BUILD_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
REVISION_RE = re.compile(r"driftline-[0-9]{5}-[a-z0-9]{3}")
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
HASH_RE = re.compile(r"[0-9a-f]{64}")
VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "vimeo.com",
    "www.vimeo.com",
    "player.vimeo.com",
}
YOUTUBE_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
OLD_RELEASE_SHA = "03ec8f12fc23d265c89b462a345a5b599a6411e8"
OLD_BUILD_ID = "c01bec2e-a950-407c-873b-b1d4fdc6bae6"
OLD_REVISION = "driftline-00305-xln"
REQUIRED_MANIFEST_FIELDS = {
    "recorded_at",
    "source_url",
    "release_sha",
    "health_sha",
    "public_main_sha",
    "cloud_run_revision",
    "cloud_build_id",
    "image_digest",
    "video_sha256",
    "captions_sha256",
    "duration_seconds",
    "first_agent_action_timestamp_seconds",
    "first_agent_action_visible",
    "continuous_native_take",
    "setup_and_loading_omitted",
    "human_approval_timestamp_seconds",
    "named_human_approval_visible",
    "bounded_action_receipt_timestamp_seconds",
    "bounded_action_receipt_visible",
    "generation_2_timestamp_seconds",
    "generation_2_reopen_visible",
    "generation_1_lineage_visible",
    "approval_to_reopen_continuous",
    "secrets_reviewed",
    "external_writes_none_visible",
    "google_cloud_proof_type",
    "google_cloud_proof_timestamp_seconds",
    "google_cloud_proof_visible",
    "google_cloud_proof_identity_matches_release",
    "release_proof_visible",
    "candidate_watermark_absent",
}


class ReleaseRenderError(ValueError):
    pass


def _replace(text: str, old: str, new: str, *, count: int = 1) -> str:
    actual = text.count(old)
    if actual != count:
        raise ReleaseRenderError(
            f"expected {count} occurrence(s) of release-template text, found {actual}: {old!r}"
        )
    return text.replace(old, new)


def _validate_manifest(manifest: dict[str, object]) -> dict[str, str]:
    if not isinstance(manifest, dict):
        raise ReleaseRenderError("final-demo manifest must be a JSON object")
    if set(manifest) != REQUIRED_MANIFEST_FIELDS:
        missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
        unexpected = sorted(set(manifest) - REQUIRED_MANIFEST_FIELDS)
        raise ReleaseRenderError(
            f"final-demo manifest fields differ; missing={missing}, unexpected={unexpected}"
        )
    try:
        recorded_at = dt.datetime.fromisoformat(
            str(manifest["recorded_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ReleaseRenderError("recorded_at must be an ISO-8601 timestamp") from exc
    if recorded_at.tzinfo is None:
        raise ReleaseRenderError("recorded_at must include a timezone")
    if manifest["source_url"] != "https://driftline-ops.web.app/":
        raise ReleaseRenderError("source_url must be the canonical hosted application")

    identity_keys = ("release_sha", "health_sha", "public_main_sha")
    identities = [str(manifest.get(key, "")) for key in identity_keys]
    if any(not SHA_RE.fullmatch(value) for value in identities):
        raise ReleaseRenderError(
            "release, health, and public-main SHAs must be full commits"
        )
    if len(set(identities)) != 1 or identities[0] == "0" * 40:
        raise ReleaseRenderError("release, health, and public-main SHAs must match")

    revision = str(manifest.get("cloud_run_revision", ""))
    build_id = str(manifest.get("cloud_build_id", ""))
    digest = str(manifest.get("image_digest", ""))
    video_sha256 = str(manifest.get("video_sha256", ""))
    captions_sha256 = str(manifest.get("captions_sha256", ""))
    if not REVISION_RE.fullmatch(revision):
        raise ReleaseRenderError("Cloud Run revision is invalid")
    if not BUILD_RE.fullmatch(build_id):
        raise ReleaseRenderError("Cloud Build ID is invalid")
    if not DIGEST_RE.fullmatch(digest):
        raise ReleaseRenderError("image digest is invalid")
    if any(
        not HASH_RE.fullmatch(value) or value == "0" * 64
        for value in (video_sha256, captions_sha256)
    ):
        raise ReleaseRenderError(
            "final video and captions hashes must be nonzero SHA-256 values"
        )

    for key in (
        "first_agent_action_visible",
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
        if manifest.get(key) is not True:
            raise ReleaseRenderError(f"final-demo manifest gate is not affirmed: {key}")

    try:
        duration = float(manifest["duration_seconds"])
        first_action = float(manifest["first_agent_action_timestamp_seconds"])
        approval = float(manifest["human_approval_timestamp_seconds"])
        receipt = float(manifest["bounded_action_receipt_timestamp_seconds"])
        generation_2 = float(manifest["generation_2_timestamp_seconds"])
        cloud_proof = float(manifest["google_cloud_proof_timestamp_seconds"])
    except (TypeError, ValueError) as exc:
        raise ReleaseRenderError(
            "final-demo duration and proof timestamps must be numeric"
        ) from exc
    if not 0 < duration < 236:
        raise ReleaseRenderError("final demo duration must be below 3:56")
    if not 0 <= first_action <= 15 or first_action >= approval:
        raise ReleaseRenderError(
            "first agent action must be visible by 0:15 before approval"
        )
    if not 60 <= approval <= 100:
        raise ReleaseRenderError("named approval must be visible between 1:00 and 1:40")
    if not approval <= receipt <= approval + 20:
        raise ReleaseRenderError(
            "bounded action receipt must follow approval within 20 seconds"
        )
    if not receipt < generation_2 <= 140:
        raise ReleaseRenderError("generation 2 must follow the receipt by 2:20")
    if manifest["google_cloud_proof_type"] not in {
        "cloud_run_console",
        "cloud_run_url",
    }:
        raise ReleaseRenderError("Google Cloud proof type is invalid")
    if not 0 <= cloud_proof <= duration - 10:
        raise ReleaseRenderError(
            "Google Cloud proof must begin at least ten seconds before the end"
        )

    return {
        "release_sha": identities[0],
        "revision": revision,
        "build_id": build_id,
        "digest": digest,
        "video_sha256": video_sha256,
        "captions_sha256": captions_sha256,
    }


def _validate_video_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in VIDEO_HOSTS:
        raise ReleaseRenderError("video URL must be HTTPS on public YouTube or Vimeo")
    path = parsed.path.strip("/")
    if not path:
        raise ReleaseRenderError("video URL must identify a specific video")
    if parsed.hostname in {"youtube.com", "www.youtube.com"}:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if path != "watch" or not YOUTUBE_ID_RE.fullmatch(video_id):
            raise ReleaseRenderError("YouTube URL must identify a specific watch video")
    elif parsed.hostname == "youtu.be" and not YOUTUBE_ID_RE.fullmatch(path):
        raise ReleaseRenderError("youtu.be URL must identify one specific video")
    elif parsed.hostname in {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}:
        segments = path.split("/")
        video_id = segments[-1]
        if (
            parsed.hostname == "player.vimeo.com"
            and len(segments) == 2
            and segments[0] == "video"
        ):
            video_id = segments[1]
        if not video_id.isdigit():
            raise ReleaseRenderError("Vimeo URL must identify a numeric video")
    return value


def _validate_optional_public_url(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.path.strip("/"):
        raise ReleaseRenderError(f"{label} must be a specific public HTTPS URL")
    return value


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
        raise ReleaseRenderError(f"release gallery asset is not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_gallery(paths: list[Path]) -> None:
    if len(paths) != 3 or len({path.resolve() for path in paths}) != 3:
        raise ReleaseRenderError("three distinct release gallery PNGs are required")
    for path in paths:
        if not path.is_file():
            raise ReleaseRenderError(f"release gallery asset is missing: {path}")
        width, height = _png_dimensions(path)
        if width < 1200 or height < 675:
            raise ReleaseRenderError(
                f"release gallery asset is too small: {path} is {width}x{height}"
            )
        if any(token in path.name.casefold() for token in ("candidate", "rehearsal")):
            raise ReleaseRenderError(
                f"release gallery filename carries candidate custody: {path}"
            )


def _validate_gallery_manifest(
    manifest_path: Path,
    identity: dict[str, str],
    paths: list[Path],
    proof_video_path: Path,
) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict):
        raise ReleaseRenderError("release gallery manifest must be a JSON object")
    expected_fields = {
        "captured_at",
        "source_url",
        "release_sha",
        "build_id",
        "continuous_browser_session",
        "assets",
        "proof_video",
    }
    if set(manifest) != expected_fields:
        raise ReleaseRenderError("release gallery manifest fields differ")
    try:
        captured_at = dt.datetime.fromisoformat(
            str(manifest["captured_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ReleaseRenderError("gallery captured_at must be ISO-8601") from exc
    if captured_at.tzinfo is None:
        raise ReleaseRenderError("gallery captured_at must include a timezone")
    if manifest["source_url"] != "https://driftline-ops.web.app/":
        raise ReleaseRenderError(
            "gallery must come from the canonical hosted application"
        )
    if manifest["release_sha"] != identity["release_sha"]:
        raise ReleaseRenderError(
            "gallery release SHA does not match the final manifest"
        )
    if manifest["build_id"] != identity["build_id"]:
        raise ReleaseRenderError("gallery build ID does not match the final manifest")
    if manifest["continuous_browser_session"] is not True:
        raise ReleaseRenderError(
            "gallery must come from one continuous browser session"
        )

    assets = manifest["assets"]
    keys = ("hero", "generation_1", "generation_2")
    if not isinstance(assets, dict) or set(assets) != set(keys):
        raise ReleaseRenderError(
            "gallery manifest must contain hero and both generations"
        )
    normalized_assets: dict[str, object] = {}
    for key, expected_path in zip(keys, paths, strict=True):
        asset = assets[key]
        if not isinstance(asset, dict) or set(asset) != {
            "path",
            "sha256",
            "width",
            "height",
        }:
            raise ReleaseRenderError(f"gallery manifest asset fields differ: {key}")
        if Path(str(asset["path"])).resolve() != expected_path.resolve():
            raise ReleaseRenderError(
                f"gallery path does not match supplied asset: {key}"
            )
        digest = str(asset["sha256"])
        if not HASH_RE.fullmatch(digest) or digest != _sha256_file(expected_path):
            raise ReleaseRenderError(
                f"gallery hash does not match supplied asset: {key}"
            )
        width, height = _png_dimensions(expected_path)
        if asset["width"] != width or asset["height"] != height:
            raise ReleaseRenderError(
                f"gallery dimensions do not match supplied asset: {key}"
            )
        normalized_assets[key] = {
            "sha256": digest,
            "width": width,
            "height": height,
        }
    proof_video = manifest["proof_video"]
    if not isinstance(proof_video, dict) or set(proof_video) != {
        "path",
        "sha256",
        "frames",
        "pointer_clicks",
    }:
        raise ReleaseRenderError("gallery proof-video fields differ")
    if Path(str(proof_video["path"])).resolve() != proof_video_path.resolve():
        raise ReleaseRenderError("gallery proof-video path does not match")
    if (
        proof_video_path.suffix.casefold() != ".mp4"
        or proof_video_path.stat().st_size < 100_000
    ):
        raise ReleaseRenderError("gallery proof video is missing or too small")
    proof_digest = str(proof_video["sha256"])
    if not HASH_RE.fullmatch(proof_digest) or proof_digest != _sha256_file(
        proof_video_path
    ):
        raise ReleaseRenderError("gallery proof-video hash does not match")
    frames = proof_video["frames"]
    pointer_clicks = proof_video["pointer_clicks"]
    if (
        not isinstance(frames, int)
        or isinstance(frames, bool)
        or frames < 10
        or not isinstance(pointer_clicks, int)
        or isinstance(pointer_clicks, bool)
        or pointer_clicks < 7
    ):
        raise ReleaseRenderError("gallery proof video lacks the complete click journey")
    return {
        "captured_at": manifest["captured_at"],
        "source_url": manifest["source_url"],
        "release_sha": manifest["release_sha"],
        "build_id": manifest["build_id"],
        "continuous_browser_session": True,
        "assets": normalized_assets,
        "proof_video": {
            "sha256": proof_digest,
            "frames": frames,
            "pointer_clicks": pointer_clicks,
        },
    }


def _validate_gallery_decodable(paths: list[Path]) -> None:
    for path in paths:
        result = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        width = re.search(r"pixelWidth:\s+(\d+)", result.stdout)
        height = re.search(r"pixelHeight:\s+(\d+)", result.stdout)
        if width is None or height is None:
            raise ReleaseRenderError(f"release gallery PNG is not decodable: {path}")
        if int(width.group(1)) < 1200 or int(height.group(1)) < 675:
            raise ReleaseRenderError(
                f"decoded release gallery asset is too small: {path}"
            )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_output_target(output_dir: Path) -> Path:
    resolved = output_dir.resolve()
    if resolved.is_relative_to(ROOT.resolve()):
        raise ReleaseRenderError(
            "release-bound output directory must be outside the repository"
        )
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise ReleaseRenderError("release-bound output directory must be empty")
    return resolved


def render_devpost_story(source: str, identity: dict[str, str], video_url: str) -> str:
    story = _replace(
        source,
        "- Demo video: **TODO — public YouTube or Vimeo URL, maximum four minutes**",
        f"- Demo video: {video_url}",
    )
    story = _replace(
        story,
        "> Draft custody note: the immutable production proof below describes the\n"
        "> currently serving release. The bounded internal-allocation card and authored\n"
        "> custom measurement contract exist only in the unreleased local candidate and\n"
        "> must not be presented as live until that candidate is released and reverified.",
        "> Release custody: this rendered copy is bound to the exact serving release,\n"
        f"> `{identity['release_sha']}`, Cloud Run revision `{identity['revision']}`, and\n"
        f"> Cloud Build `{identity['build_id']}`. The final manifest binds the release\n"
        "> and media; the generated identity record binds this URL and every rendered\n"
        "> visual. This rendered copy is not committed.",
    )
    story = _replace(story, "In the unreleased candidate,", "In this release,")
    story = _replace(story, OLD_RELEASE_SHA, identity["release_sha"], count=2)
    story = _replace(story, OLD_REVISION, identity["revision"])
    story = _replace(story, OLD_BUILD_ID, identity["build_id"], count=2)
    story = _replace(story, "7/7 policy checks", "10/10 policy checks", count=2)
    story = _replace(
        story,
        "current local-candidate checkpoint",
        "exact release checkpoint",
    )
    return story


def render_form_packet(
    source: str,
    identity: dict[str, str],
    video_url: str,
    gallery: list[Path],
    architecture_png: Path,
    build_story_url: str | None,
    social_url: str | None,
) -> str:
    packet = _replace(
        source,
        "Status: live-field-schema-ready, not release-ready, publish-ready, or\n"
        "submission-ready. Devpost's authenticated MCP verified all 17 custom fields,\n"
        "selector options, deliverable flags, and the architecture upload contract on\n"
        "August 26. The local candidate must still be released and reverified before its\n"
        "behavior can be presented as live; the public video and entrant attestations\n"
        "also remain open. Do not publish or submit without explicit entrant approval.",
        "Status: release-bound render for entrant review; not submitted. Devpost's\n"
        "authenticated MCP verified all 17 custom fields, selector options, deliverable\n"
        f"flags, and architecture contract. Serving release `{identity['release_sha']}`,\n"
        f"revision `{identity['revision']}`, and build `{identity['build_id']}` are bound\n"
        "by the final manifest; its video hash and the generated identity record bind\n"
        "the public URL and release assets. Submission still requires explicit entrant\n"
        "approval and personal attestations.",
    )
    packet = _replace(packet, "7/7 policy checks", "10/10 policy checks")
    packet = _replace(
        packet,
        "| Demo video | **ENTRANT TODO:** public YouTube or Vimeo URL, 4:00 maximum |",
        f"| Demo video | {video_url} |",
    )
    bonus = build_story_url or "Not claimed"
    social = social_url or "Not claimed"
    packet = _replace(
        packet,
        "| Bonus build content | **ENTRANT TODO:** publish the reviewed Decision Twin story from `submission/BUILD_STORY.md`, then paste its verified public URL; the current public `main` URL serves an older promise-drift story and must not be used. |",
        f"| Bonus build content | {bonus} |",
    )
    packet = _replace(
        packet,
        "| Social post | **ENTRANT TODO:** publish an approved draft from `submission/SOCIAL_POST_DRAFTS.md` and paste the public URL |",
        f"| Social post | {social} |",
    )
    old_gallery = (
        "| Image gallery order | 1. `submission/assets/decision-twin-hero-final.png`; "
        "2. `submission/assets/decision-twin-generation-1-final.png`; 3. "
        "`submission/assets/decision-twin-generation-2-receipt-final.png`; 4. "
        "`submission/assets/driftline-decision-twin-architecture.png`. Replace the "
        "release-bound browser captures after any authorized candidate release. |"
    )
    new_gallery = (
        f"| Image gallery order | 1. `{gallery[0]}`; 2. `{gallery[1]}`; "
        f"3. `{gallery[2]}`; 4. `{architecture_png}`. |"
    )
    packet = _replace(packet, old_gallery, new_gallery)
    packet = _replace(
        packet,
        "| Architecture upload | `submission/assets/driftline-decision-twin-architecture.png` |",
        f"| Architecture upload | `{architecture_png}` |",
    )
    packet = _replace(
        packet,
        "from older drafts. At this checkpoint, production is the release identified in\n"
        "that file; the internal-allocation card and authored custom measurement\n"
        "contract remain an unreleased local candidate.",
        f"This render is bound to serving release `{identity['release_sha']}`, revision\n"
        f"`{identity['revision']}`, build `{identity['build_id']}`, and image digest\n"
        f"`{identity['digest']}`. The rendered files remain outside the repository so\n"
        "public `main` continues to equal the deployed application commit.",
    )
    packet = _replace(packet, "same released candidate", "same serving release")
    return packet


def render_architecture(source: str, identity: dict[str, str]) -> str:
    svg = _replace(
        source,
        '<rect x="1288" y="44" width="250" height="34" rx="17" class="badgebox"/><text x="1311" y="66" class="badge">UNRELEASED CANDIDATE</text>',
        '<rect x="1288" y="44" width="250" height="34" rx="17" class="pill"/><text x="1311" y="66" class="pillt">RELEASE VERIFIED</text>',
    )
    svg = _replace(
        svg,
        "Google Cloud release proof required before publication",
        "Google Cloud release proof",
    )
    svg = _replace(
        svg,
        "Pending gate · bind candidate commit to Cloud Run revision, Cloud Build ID, image digest, live trace, and browser proof.",
        f"Release {identity['release_sha'][:12]} · {identity['revision']} · build {identity['build_id']} · immutable digest verified.",
    )
    return svg


def _assert_final(text: str, *, label: str) -> None:
    forbidden = (
        "ENTRANT TODO",
        "candidate",
        "7/7 policy checks",
        OLD_RELEASE_SHA,
        OLD_BUILD_ID,
        OLD_REVISION,
    )
    found = [value for value in forbidden if value.casefold() in text.casefold()]
    if found:
        raise ReleaseRenderError(f"{label} retains stale release markers: {found}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--video-url", required=True)
    parser.add_argument("--hero-image", required=True, type=Path)
    parser.add_argument("--generation-1-image", required=True, type=Path)
    parser.add_argument("--generation-2-image", required=True, type=Path)
    parser.add_argument("--gallery-manifest", required=True, type=Path)
    parser.add_argument("--gallery-proof-video", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--build-story-url")
    parser.add_argument("--social-url")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    identity = _validate_manifest(manifest)
    video_url = _validate_video_url(args.video_url)
    build_story_url = _validate_optional_public_url(
        args.build_story_url, "build-story URL"
    )
    social_url = _validate_optional_public_url(args.social_url, "social URL")
    gallery = [
        args.hero_image.resolve(),
        args.generation_1_image.resolve(),
        args.generation_2_image.resolve(),
    ]
    _validate_gallery(gallery)
    gallery_capture = _validate_gallery_manifest(
        args.gallery_manifest.resolve(),
        identity,
        gallery,
        args.gallery_proof_video.resolve(),
    )
    output_dir = _validate_output_target(args.output_dir)

    story = render_devpost_story(
        (ROOT / "submission/DEVPOST.md").read_text(), identity, video_url
    )
    architecture_svg = render_architecture(
        (
            ROOT
            / "submission/assets/driftline-decision-twin-candidate-architecture.svg"
        ).read_text(),
        identity,
    )
    if not shutil.which("sips"):
        raise ReleaseRenderError(
            "sips is required to render the release architecture PNG"
        )
    _validate_gallery_decodable(gallery)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        names = (
            "decision-twin-hero-release.png",
            "decision-twin-generation-1-release.png",
            "decision-twin-generation-2-receipt-release.png",
        )
        rendered_gallery = [Path(name) for name in names]
        for source, name in zip(gallery, names, strict=True):
            shutil.copy2(source, stage / name)
        source_assets = gallery_capture["assets"]
        assert isinstance(source_assets, dict)
        gallery_capture["assets"] = {
            key: {"file": name, **source_assets[key]}
            for key, name in zip(
                ("hero", "generation_1", "generation_2"), names, strict=True
            )
        }
        gallery_capture_path = stage / "release-gallery-capture.json"
        gallery_capture_path.write_text(
            json.dumps(gallery_capture, indent=2, sort_keys=True) + "\n"
        )

        architecture_svg_path = (
            stage / "driftline-decision-twin-release-architecture.svg"
        )
        staged_architecture_png = (
            stage / "driftline-decision-twin-release-architecture.png"
        )
        final_architecture_png = Path(staged_architecture_png.name)
        architecture_svg_path.write_text(architecture_svg)
        subprocess.run(
            [
                "sips",
                "-s",
                "format",
                "png",
                str(architecture_svg_path),
                "--out",
                str(staged_architecture_png),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        if _png_dimensions(staged_architecture_png) != (1600, 900):
            raise ReleaseRenderError("release architecture PNG must be 1600x900")

        packet = render_form_packet(
            (ROOT / "devpost-submission.md").read_text(),
            identity,
            video_url,
            rendered_gallery,
            final_architecture_png,
            build_story_url,
            social_url,
        )
        _assert_final(story, label="Devpost story")
        _assert_final(packet, label="form packet")
        (stage / "DEVPOST.release.md").write_text(story)
        (stage / "devpost-submission.release.md").write_text(packet)
        release_identity: dict[str, object] = {
            **identity,
            "video_url": video_url,
            "manifest_proof": {
                key: manifest[key]
                for key in (
                    "recorded_at",
                    "source_url",
                    "duration_seconds",
                    "first_agent_action_timestamp_seconds",
                    "human_approval_timestamp_seconds",
                    "bounded_action_receipt_timestamp_seconds",
                    "generation_2_timestamp_seconds",
                    "google_cloud_proof_type",
                    "google_cloud_proof_timestamp_seconds",
                )
            },
            "gallery_sha256": {name: _sha256_file(stage / name) for name in names},
            "gallery_capture_sha256": _sha256_file(gallery_capture_path),
            "architecture_svg_sha256": _sha256_file(architecture_svg_path),
            "architecture_png_sha256": _sha256_file(staged_architecture_png),
            "submission_files_sha256": {
                "DEVPOST.release.md": _sha256_file(stage / "DEVPOST.release.md"),
                "devpost-submission.release.md": _sha256_file(
                    stage / "devpost-submission.release.md"
                ),
            },
        }
        (stage / "release-identity.json").write_text(
            json.dumps(release_identity, indent=2, sort_keys=True) + "\n"
        )
        if output_dir.exists():
            output_dir.rmdir()
        stage.rename(output_dir)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    print(f"Release-bound submission render passed: {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        ReleaseRenderError,
        json.JSONDecodeError,
        OSError,
        subprocess.CalledProcessError,
    ) as exc:
        raise SystemExit(f"Release-bound submission render failed: {exc}") from None
