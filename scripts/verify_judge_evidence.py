#!/usr/bin/env python3
"""Fail-closed audit of Driftline's judge-facing evidence map."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "submission" / "judge-evidence-manifest.json"
ALLOWED_STATES = {
    "implemented",
    "tested",
    "prepared",
    "deployed",
    "live_verified",
    "customer_verified",
    "open",
    "not_claimed",
}
EXPECTED_CRITERIA = {
    "innovation_operational_utility": 40,
    "architecture_tech_stack": 30,
    "demo_production_readiness": 30,
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class EvidenceAuditError(ValueError):
    pass


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceAuditError(f"cannot read manifest: {exc}") from exc
    if not isinstance(payload, dict):
        raise EvidenceAuditError("manifest root must be an object")
    return payload


def _safe_repo_path(raw_path: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise EvidenceAuditError(f"evidence path must stay inside the repository: {raw_path}")
    resolved = (ROOT / relative).resolve()
    if not resolved.is_relative_to(ROOT):
        raise EvidenceAuditError(f"evidence path escapes the repository: {raw_path}")
    return resolved


def validate_manifest(payload: dict[str, Any], *, check_files: bool = True) -> dict[str, Any]:
    if payload.get("schema_version") != 1:
        raise EvidenceAuditError("schema_version must be 1")
    if payload.get("category") != "Taskmaster":
        raise EvidenceAuditError("category must be Taskmaster")

    criteria = payload.get("criteria")
    if not isinstance(criteria, list):
        raise EvidenceAuditError("criteria must be a list")
    weights: dict[str, int] = {}
    claim_ids: set[str] = set()
    state_counts: Counter[str] = Counter()
    evidence_count = 0
    for criterion in criteria:
        if not isinstance(criterion, dict):
            raise EvidenceAuditError("each criterion must be an object")
        criterion_id = criterion.get("id")
        weight = criterion.get("weight")
        if not isinstance(criterion_id, str) or not isinstance(weight, int):
            raise EvidenceAuditError("criterion id and integer weight are required")
        if criterion_id in weights:
            raise EvidenceAuditError(f"duplicate criterion: {criterion_id}")
        weights[criterion_id] = weight
        claims = criterion.get("claims")
        if not isinstance(claims, list) or not claims:
            raise EvidenceAuditError(f"criterion {criterion_id} has no claims")
        for claim in claims:
            if not isinstance(claim, dict):
                raise EvidenceAuditError(f"criterion {criterion_id} has a malformed claim")
            claim_id = claim.get("id")
            state = claim.get("state")
            text = claim.get("claim")
            evidence = claim.get("evidence")
            if not isinstance(claim_id, str) or not claim_id:
                raise EvidenceAuditError("every claim needs an id")
            if claim_id in claim_ids:
                raise EvidenceAuditError(f"duplicate claim: {claim_id}")
            claim_ids.add(claim_id)
            if state not in ALLOWED_STATES:
                raise EvidenceAuditError(f"claim {claim_id} has invalid state: {state}")
            if not isinstance(text, str) or len(text.strip()) < 30:
                raise EvidenceAuditError(f"claim {claim_id} is not specific enough")
            if not isinstance(evidence, list) or len(evidence) < 2:
                raise EvidenceAuditError(f"claim {claim_id} needs at least two evidence anchors")
            state_counts[state] += 1
            for anchor in evidence:
                if not isinstance(anchor, dict) or not isinstance(anchor.get("path"), str):
                    raise EvidenceAuditError(f"claim {claim_id} has a malformed evidence anchor")
                path = _safe_repo_path(anchor["path"])
                if check_files:
                    if not path.is_file() or path.stat().st_size == 0:
                        raise EvidenceAuditError(f"claim {claim_id} evidence is missing: {anchor['path']}")
                    needle = anchor.get("contains")
                    if needle is not None:
                        if not isinstance(needle, str) or not needle:
                            raise EvidenceAuditError(f"claim {claim_id} has an invalid contains assertion")
                        try:
                            contents = path.read_text(encoding="utf-8")
                        except UnicodeDecodeError as exc:
                            raise EvidenceAuditError(
                                f"claim {claim_id} uses contains against binary evidence: {anchor['path']}"
                            ) from exc
                        if needle not in contents:
                            raise EvidenceAuditError(
                                f"claim {claim_id} evidence lost required text in {anchor['path']}: {needle}"
                            )
                evidence_count += 1

    if weights != EXPECTED_CRITERIA:
        raise EvidenceAuditError(f"rubric weights do not match the official 40/30/30 criteria: {weights}")

    candidate = payload.get("candidate_baseline")
    if not isinstance(candidate, dict) or not SHA_RE.fullmatch(str(candidate.get("last_verified_sha", ""))):
        raise EvidenceAuditError("candidate baseline needs a valid last_verified_sha")
    if candidate.get("deployed") is not False or candidate.get("state") != "tested":
        raise EvidenceAuditError("unreleased candidate baseline must remain tested and deployed=false")

    serving = payload.get("serving_release")
    if not isinstance(serving, dict) or serving.get("state") != "live_verified":
        raise EvidenceAuditError("serving release must be explicitly live_verified")
    if not SHA_RE.fullmatch(str(serving.get("release_sha", ""))):
        raise EvidenceAuditError("serving release needs a valid release_sha")
    if serving["release_sha"] == candidate["last_verified_sha"]:
        raise EvidenceAuditError("candidate cannot be marked separately unreleased while matching the serving SHA")

    for section in ("stage_one_requirements", "submission_gates"):
        rows = payload.get(section)
        if not isinstance(rows, list) or not rows:
            raise EvidenceAuditError(f"{section} must be a non-empty list")
        ids: set[str] = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise EvidenceAuditError(f"{section} has a malformed row")
            if row["id"] in ids:
                raise EvidenceAuditError(f"{section} has duplicate id: {row['id']}")
            ids.add(row["id"])
            if row.get("state") not in ALLOWED_STATES:
                raise EvidenceAuditError(f"{section} {row['id']} has invalid state")

    open_gates = [row["id"] for row in payload["submission_gates"] if row["state"] == "open"]
    return {
        "criteria_weight": sum(weights.values()),
        "claims": len(claim_ids),
        "evidence_anchors": evidence_count,
        "claim_states": dict(sorted(state_counts.items())),
        "open_gates": open_gates,
        "candidate_sha": candidate["last_verified_sha"],
        "serving_sha": serving["release_sha"],
    }


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify_release_candidate() -> dict[str, str]:
    if _git("status", "--porcelain"):
        raise EvidenceAuditError("release-candidate audit requires a clean tree")
    origin = _git("remote", "get-url", "origin")
    if origin not in {"https://github.com/mikeyerke/driftline.git", "git@github.com:mikeyerke/driftline.git"}:
        raise EvidenceAuditError(f"unexpected origin: {origin}")
    head = _git("rev-parse", "HEAD")
    remote_line = _git("ls-remote", "origin", "refs/heads/main")
    remote_sha = remote_line.split()[0] if remote_line else ""
    if head != remote_sha:
        raise EvidenceAuditError(f"HEAD {head} does not equal public main {remote_sha}")
    return {"head_sha": head, "public_main_sha": remote_sha}


def verify_live_identity(payload: dict[str, Any]) -> dict[str, str]:
    serving = payload["serving_release"]
    request = urllib.request.Request(serving["health_url"], headers={"User-Agent": "driftline-judge-audit/1"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            health = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # network and malformed-response failures are equally fatal here
        raise EvidenceAuditError(f"live health check failed: {exc}") from exc
    if health.get("status") != "ok":
        raise EvidenceAuditError(f"live health status is not ok: {health.get('status')}")
    if health.get("release_sha") != serving["release_sha"]:
        raise EvidenceAuditError("live release SHA drifted from the evidence manifest")
    if health.get("build_id") != serving["build_id"]:
        raise EvidenceAuditError("live build ID drifted from the evidence manifest")
    return {"release_sha": health["release_sha"], "build_id": health["build_id"]}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--live", action="store_true", help="verify the recorded serving identity over HTTPS")
    parser.add_argument(
        "--release-candidate",
        action="store_true",
        help="require clean HEAD to equal the current public main tip",
    )
    parser.add_argument(
        "--require-submission-ready",
        action="store_true",
        help="fail while any submission gate remains open",
    )
    parser.add_argument("--json", action="store_true", help="emit a machine-readable result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = _load_manifest(args.manifest.resolve())
        report = validate_manifest(payload)
        if args.live:
            report["live_identity"] = verify_live_identity(payload)
        if args.release_candidate:
            report["release_candidate"] = verify_release_candidate()
        if args.require_submission_ready and report["open_gates"]:
            raise EvidenceAuditError(
                "submission is not ready; open gates: " + ", ".join(report["open_gates"])
            )
    except (EvidenceAuditError, subprocess.CalledProcessError) as exc:
        print(f"Judge evidence audit failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"status": "pass", **report}, indent=2, sort_keys=True))
    else:
        print("Judge evidence audit: PASS")
        print(f"Official rubric: {report['criteria_weight']}% mapped")
        print(f"Claims: {report['claims']} with {report['evidence_anchors']} evidence anchors")
        print(f"Candidate: {report['candidate_sha']} (tested, not deployed)")
        print(f"Serving:   {report['serving_sha']} (live verified)")
        print("Open gates: " + ", ".join(report["open_gates"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
