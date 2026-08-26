#!/usr/bin/env python3
"""Build a fail-closed final-demo manifest seed from verified release identity."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "submission/final-demo-manifest.template.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
BUILD_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
REVISION_RE = re.compile(r"^driftline-[0-9]{5}-[a-z0-9]{3}$")
EXPECTED_IDENTITY_FIELDS = {
    "verified_at",
    "source_url",
    "release_sha",
    "health_sha",
    "public_main_sha",
    "cloud_run_revision",
    "cloud_build_id",
    "image_digest",
    "traffic_percent",
    "trace_evaluation_id",
    "trace_release_sha",
}


class ManifestSeedError(ValueError):
    pass


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestSeedError(f"{label} is not readable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ManifestSeedError(f"{label} must be a JSON object")
    return value


def validate_release_identity(identity: dict[str, Any]) -> dict[str, str]:
    if set(identity) != EXPECTED_IDENTITY_FIELDS:
        missing = sorted(EXPECTED_IDENTITY_FIELDS - set(identity))
        unexpected = sorted(set(identity) - EXPECTED_IDENTITY_FIELDS)
        raise ManifestSeedError(
            f"release identity fields differ; missing={missing}, unexpected={unexpected}"
        )
    try:
        verified_at = dt.datetime.fromisoformat(
            str(identity["verified_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ManifestSeedError("verified_at must be an ISO-8601 timestamp") from exc
    if verified_at.tzinfo is None:
        raise ManifestSeedError("verified_at must include a timezone")
    if identity["source_url"] != "https://driftline-ops.web.app/":
        raise ManifestSeedError("release identity source URL is not canonical")
    sha_keys = ("release_sha", "health_sha", "public_main_sha", "trace_release_sha")
    shas = [str(identity[key]) for key in sha_keys]
    if any(not SHA_RE.fullmatch(value) for value in shas):
        raise ManifestSeedError("release identity SHAs must be full lowercase commits")
    if len(set(shas)) != 1 or shas[0] == "0" * 40:
        raise ManifestSeedError("release, health, public-main, and trace SHAs must match")
    revision = str(identity["cloud_run_revision"])
    build_id = str(identity["cloud_build_id"])
    digest = str(identity["image_digest"])
    if not REVISION_RE.fullmatch(revision):
        raise ManifestSeedError("Cloud Run revision is invalid")
    if not BUILD_RE.fullmatch(build_id):
        raise ManifestSeedError("Cloud Build ID is invalid")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ManifestSeedError("image digest is invalid")
    if identity["traffic_percent"] != 100:
        raise ManifestSeedError("release identity must prove 100 percent traffic")
    trace_id = str(identity["trace_evaluation_id"])
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,120}", trace_id):
        raise ManifestSeedError("trace evaluation ID is invalid")
    return {
        "release_sha": shas[0],
        "cloud_run_revision": revision,
        "cloud_build_id": build_id,
        "image_digest": digest,
    }


def validate_output_path(path: Path) -> Path:
    if not path.is_absolute():
        raise ManifestSeedError("manifest seed output path must be absolute")
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ManifestSeedError("manifest seed output must be outside the repository")
    if resolved.exists():
        raise ManifestSeedError("manifest seed output already exists")
    if not resolved.parent.is_dir():
        raise ManifestSeedError("manifest seed output parent does not exist")
    return resolved


def build_manifest_seed(identity_path: Path, output_path: Path) -> Path:
    identity_path = identity_path.resolve()
    identity = _load_object(identity_path, "release identity")
    verified = validate_release_identity(identity)
    template = _load_object(TEMPLATE, "final-demo manifest template")
    output = validate_output_path(output_path)
    receipt_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
    if not HASH_RE.fullmatch(receipt_hash):  # pragma: no cover - hashlib invariant
        raise ManifestSeedError("release identity receipt hash is invalid")
    template.update(
        {
            "source_url": identity["source_url"],
            "release_sha": verified["release_sha"],
            "health_sha": verified["release_sha"],
            "public_main_sha": verified["release_sha"],
            "cloud_run_revision": verified["cloud_run_revision"],
            "cloud_build_id": verified["cloud_build_id"],
            "image_digest": verified["image_digest"],
            "release_identity_receipt_sha256": receipt_hash,
        }
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(template, handle, indent=2)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-identity", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = build_manifest_seed(args.release_identity, args.output)
    print(f"Final-demo manifest seed created: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
