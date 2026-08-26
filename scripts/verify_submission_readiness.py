#!/usr/bin/env python3
"""Chain judge, release, media, packet, and entrant evidence into one verdict."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
JUDGE_MANIFEST = ROOT / "submission" / "judge-evidence-manifest.json"
ATTESTATION_FIELDS = {
    "reviewed_at",
    "entrant_name",
    "eligibility_confirmed",
    "ownership_rights_confirmed",
    "originality_disclosure_confirmed",
    "official_rules_reviewed",
    "final_entry_reviewed",
    "public_video_logged_out_verified",
    "submission_authorized",
}
TRUE_ATTESTATIONS = ATTESTATION_FIELDS - {"reviewed_at", "entrant_name"}
PACKET_FILES = {
    "DEVPOST.release.md",
    "devpost-submission.release.md",
    "driftline-final-demo-release.srt",
    "driftline-final-demo-review-sheet.png",
    "driftline-decision-twin-release-architecture.svg",
    "driftline-decision-twin-release-architecture.png",
    "decision-twin-hero-release.png",
    "decision-twin-generation-1-release.png",
    "decision-twin-generation-2-receipt-release.png",
    "release-gallery-capture.json",
    "release-identity.json",
}


class SubmissionReadinessError(ValueError):
    pass


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SubmissionReadinessError(f"cannot load verifier module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


JUDGE = _load_module("verify_judge_evidence", ROOT / "scripts/verify_judge_evidence.py")
SEED = _load_module(
    "prepare_final_demo_manifest", ROOT / "scripts/prepare_final_demo_manifest.py"
)
RENDER = _load_module(
    "render_release_submission", ROOT / "scripts/render_release_submission.py"
)


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SubmissionReadinessError(f"{label} is not readable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise SubmissionReadinessError(f"{label} must be a JSON object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_attestations(path: Path) -> dict[str, str]:
    value = _load_object(path, "entrant attestations")
    if set(value) != ATTESTATION_FIELDS:
        missing = sorted(ATTESTATION_FIELDS - set(value))
        unexpected = sorted(set(value) - ATTESTATION_FIELDS)
        raise SubmissionReadinessError(
            f"entrant attestation fields differ; missing={missing}, unexpected={unexpected}"
        )
    try:
        reviewed_at = dt.datetime.fromisoformat(str(value["reviewed_at"]))
    except ValueError as exc:
        raise SubmissionReadinessError(
            "entrant attestations need a valid reviewed_at timestamp"
        ) from exc
    if reviewed_at.tzinfo is None:
        raise SubmissionReadinessError("entrant reviewed_at must include a timezone")
    if not isinstance(value["entrant_name"], str) or not value["entrant_name"].strip():
        raise SubmissionReadinessError("entrant_name must be completed outside the repository")
    false_fields = sorted(field for field in TRUE_ATTESTATIONS if value[field] is not True)
    if false_fields:
        raise SubmissionReadinessError(
            "entrant attestations are not all affirmed: " + ", ".join(false_fields)
        )
    return {"reviewed_at": reviewed_at.isoformat(), "status": "affirmed"}


def _validate_current_release(identity: dict[str, Any]) -> None:
    request = urllib.request.Request(
        str(identity["source_url"]) + "health",
        headers={"User-Agent": "driftline-submission-readiness/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            health = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise SubmissionReadinessError(f"current live health check failed: {exc}") from exc
    if health.get("status") != "ok":
        raise SubmissionReadinessError("current live health status is not ok")
    if health.get("release_sha") != identity["release_sha"]:
        raise SubmissionReadinessError("current live release SHA does not match the receipt")
    if health.get("build_id") != identity["cloud_build_id"]:
        raise SubmissionReadinessError("current live build ID does not match the receipt")

    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-remote", "origin", "refs/heads/main"],
        check=True,
        capture_output=True,
        text=True,
    )
    public_main = result.stdout.split()[0] if result.stdout.split() else ""
    if public_main != identity["release_sha"]:
        raise SubmissionReadinessError(
            f"public main {public_main} does not match release {identity['release_sha']}"
        )


def validate_release_media(
    *,
    release_identity_path: Path,
    final_manifest_path: Path,
    video_path: Path,
    captions_path: Path,
    video_url: str,
    run_media_verifier: bool,
    verify_current_release: bool,
) -> dict[str, str]:
    receipt = _load_object(release_identity_path, "release identity receipt")
    receipt_identity = SEED.validate_release_identity(receipt)
    manifest = _load_object(final_manifest_path, "final demo manifest")
    rendered_identity = RENDER._validate_manifest(manifest)
    RENDER._validate_final_media_files(manifest, video_path, captions_path)
    normalized_video_url = RENDER._validate_video_url(video_url)

    if _sha256(release_identity_path) != rendered_identity["release_identity_receipt_sha256"]:
        raise SubmissionReadinessError(
            "final demo manifest is not bound to the supplied release receipt"
        )
    for receipt_key, rendered_key in (
        ("release_sha", "release_sha"),
        ("cloud_run_revision", "revision"),
        ("cloud_build_id", "build_id"),
        ("image_digest", "digest"),
    ):
        if receipt_identity[receipt_key] != rendered_identity[rendered_key]:
            raise SubmissionReadinessError(
                f"final demo {rendered_key} does not match the release receipt"
            )
    if verify_current_release:
        _validate_current_release(receipt)
    if run_media_verifier:
        subprocess.run(
            [
                str(ROOT / "scripts/verify_final_demo_package.sh"),
                str(video_path),
                str(captions_path),
                str(final_manifest_path),
            ],
            check=True,
        )
    return {
        **rendered_identity,
        "video_url": normalized_video_url,
    }


def validate_release_packet(packet_dir: Path, expected: dict[str, str]) -> None:
    directory = packet_dir.resolve()
    if directory == ROOT or ROOT in directory.parents:
        raise SubmissionReadinessError("release packet must remain outside the repository")
    missing = sorted(name for name in PACKET_FILES if not (directory / name).is_file())
    if missing:
        raise SubmissionReadinessError("release packet is missing files: " + ", ".join(missing))
    identity = _load_object(directory / "release-identity.json", "release packet identity")
    for key in (
        "release_sha",
        "revision",
        "build_id",
        "digest",
        "release_identity_receipt_sha256",
        "video_sha256",
        "captions_sha256",
        "video_url",
    ):
        if identity.get(key) != expected[key]:
            raise SubmissionReadinessError(f"release packet identity mismatch: {key}")

    hash_groups = (
        (
            identity.get("gallery_sha256"),
            {
                "decision-twin-hero-release.png",
                "decision-twin-generation-1-release.png",
                "decision-twin-generation-2-receipt-release.png",
            },
        ),
        (
            identity.get("submission_files_sha256"),
            {"DEVPOST.release.md", "devpost-submission.release.md"},
        ),
    )
    for group, expected_names in hash_groups:
        if not isinstance(group, dict) or not group:
            raise SubmissionReadinessError("release packet hash group is missing")
        if set(group) != expected_names:
            raise SubmissionReadinessError("release packet hash group fields differ")
        for name, digest in group.items():
            path = directory / str(name)
            if not path.is_file() or _sha256(path) != digest:
                raise SubmissionReadinessError(f"release packet hash mismatch: {name}")

    verified_media = identity.get("verified_media")
    if not isinstance(verified_media, dict):
        raise SubmissionReadinessError("release packet verified_media is missing")
    if verified_media.get("video_sha256") != expected["video_sha256"]:
        raise SubmissionReadinessError("release packet video hash is not bound to the final manifest")
    for file_key, hash_key in (
        ("captions_file", "captions_sha256"),
        ("review_sheet_file", "review_sheet_sha256"),
    ):
        name = verified_media.get(file_key)
        digest = verified_media.get(hash_key)
        if not isinstance(name, str) or not isinstance(digest, str):
            raise SubmissionReadinessError(f"release packet media metadata is missing: {file_key}")
        expected_name = {
            "captions_file": "driftline-final-demo-release.srt",
            "review_sheet_file": "driftline-final-demo-review-sheet.png",
        }[file_key]
        if name != expected_name:
            raise SubmissionReadinessError(
                f"release packet media filename is invalid: {name}"
            )
        if not (directory / name).is_file() or _sha256(directory / name) != digest:
            raise SubmissionReadinessError(f"release packet media hash mismatch: {name}")
    if verified_media.get("captions_sha256") != expected["captions_sha256"]:
        raise SubmissionReadinessError(
            "release packet captions hash is not bound to the final manifest"
        )

    capture_digest = identity.get("gallery_capture_sha256")
    if not isinstance(capture_digest, str) or _sha256(
        directory / "release-gallery-capture.json"
    ) != capture_digest:
        raise SubmissionReadinessError("release gallery capture hash mismatch")

    architecture = {
        "driftline-decision-twin-release-architecture.svg": identity.get(
            "architecture_svg_sha256"
        ),
        "driftline-decision-twin-release-architecture.png": identity.get(
            "architecture_png_sha256"
        ),
    }
    for name, digest in architecture.items():
        if not isinstance(digest, str) or _sha256(directory / name) != digest:
            raise SubmissionReadinessError(f"release packet architecture hash mismatch: {name}")

    for name in ("DEVPOST.release.md", "devpost-submission.release.md"):
        try:
            RENDER._assert_final((directory / name).read_text(), label=name)
        except UnicodeDecodeError as exc:
            raise SubmissionReadinessError(f"release packet text is not UTF-8: {name}") from exc
    for name in (
        "decision-twin-hero-release.png",
        "decision-twin-generation-1-release.png",
        "decision-twin-generation-2-receipt-release.png",
    ):
        width, height = RENDER._png_dimensions(directory / name)
        if width < 1200 or height < 675:
            raise SubmissionReadinessError(f"release gallery dimensions are invalid: {name}")
    if RENDER._png_dimensions(
        directory / "driftline-final-demo-review-sheet.png"
    ) != (1920, 1080):
        raise SubmissionReadinessError("release review sheet must be 1920x1080")
    if RENDER._png_dimensions(
        directory / "driftline-decision-twin-release-architecture.png"
    ) != (1600, 900):
        raise SubmissionReadinessError("release architecture must be 1600x900")


def resolve_ready_gates(
    base_open_gates: list[str], *, release_ready: bool, attestations_ready: bool
) -> list[str]:
    resolved = set(base_open_gates)
    if release_ready:
        resolved.discard("deploy_exact_public_main_candidate")
        resolved.discard("record_and_publish_exact_release_video")
    if attestations_ready:
        resolved.discard("entrant_eligibility_ownership_and_rules_attestations")
    return sorted(resolved)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-identity", type=Path)
    parser.add_argument("--final-demo-manifest", type=Path)
    parser.add_argument("--video-file", type=Path)
    parser.add_argument("--captions-file", type=Path)
    parser.add_argument("--video-url")
    parser.add_argument("--release-packet-dir", type=Path)
    parser.add_argument("--entrant-attestations", type=Path)
    parser.add_argument("--require-ready-to-submit", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    release_args = {
        "release_identity_path": args.release_identity,
        "final_manifest_path": args.final_demo_manifest,
        "video_path": args.video_file,
        "captions_path": args.captions_file,
        "video_url": args.video_url,
        "packet_dir": args.release_packet_dir,
    }
    supplied = {key for key, value in release_args.items() if value is not None}
    try:
        judge_payload = JUDGE._load_manifest(JUDGE_MANIFEST)
        judge_report = JUDGE.validate_manifest(judge_payload)
        release_ready = False
        release_result: dict[str, str] | None = None
        if supplied:
            if supplied != set(release_args):
                missing = sorted(set(release_args) - supplied)
                raise SubmissionReadinessError(
                    "release evidence inputs are all-or-none; missing: " + ", ".join(missing)
                )
            release_result = validate_release_media(
                release_identity_path=args.release_identity.resolve(),
                final_manifest_path=args.final_demo_manifest.resolve(),
                video_path=args.video_file.resolve(),
                captions_path=args.captions_file.resolve(),
                video_url=args.video_url,
                run_media_verifier=True,
                verify_current_release=True,
            )
            validate_release_packet(args.release_packet_dir, release_result)
            release_ready = True

        attestations_ready = False
        if args.entrant_attestations is not None:
            validate_attestations(args.entrant_attestations.resolve())
            attestations_ready = True

        open_ready = resolve_ready_gates(
            judge_report["open_ready_gates"],
            release_ready=release_ready,
            attestations_ready=attestations_ready,
        )
        if args.require_ready_to_submit and open_ready:
            raise SubmissionReadinessError(
                "not ready to submit; open gates: " + ", ".join(open_ready)
            )
        report: dict[str, Any] = {
            "status": "pass",
            "ready_to_submit": not open_ready,
            "open_ready_gates": open_ready,
            "submission_completion_gate": "devpost_form_save_and_submit",
            "open_score_opportunities": judge_report["open_score_gates"],
            "release_evidence_verified": release_ready,
            "entrant_attestations_verified": attestations_ready,
        }
        if release_result is not None:
            report["release_sha"] = release_result["release_sha"]
            report["video_url"] = release_result["video_url"]
    except (
        SubmissionReadinessError,
        JUDGE.EvidenceAuditError,
        SEED.ManifestSeedError,
        RENDER.ReleaseRenderError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"Submission readiness audit failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Submission readiness audit: PASS")
        print(f"Ready to submit: {'yes' if report['ready_to_submit'] else 'no'}")
        print("Open readiness gates: " + (", ".join(open_ready) if open_ready else "none"))
        print(
            "Open score opportunities: "
            + ", ".join(report["open_score_opportunities"])
        )
        print("Completion gate: devpost_form_save_and_submit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
