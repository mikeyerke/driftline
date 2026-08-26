from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "verify_judge_evidence", ROOT / "scripts" / "verify_judge_evidence.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
MANIFEST = json.loads((ROOT / "submission" / "judge-evidence-manifest.json").read_text())


def test_repository_judge_manifest_is_valid() -> None:
    report = MODULE.validate_manifest(MANIFEST)
    assert report["criteria_weight"] == 100
    assert report["claims"] == 9
    assert report["evidence_anchors"] >= 20
    assert report["candidate_sha"] != report["serving_sha"]
    assert "record_and_publish_exact_release_video" in report["open_gates"]
    assert "devpost_form_save_and_submit" not in report["open_ready_gates"]
    assert "independent_pm_validation" in report["open_score_gates"]


def test_rejects_rubric_weight_drift() -> None:
    payload = copy.deepcopy(MANIFEST)
    payload["criteria"][0]["weight"] = 39
    with pytest.raises(MODULE.EvidenceAuditError, match="40/30/30"):
        MODULE.validate_manifest(payload, check_files=False)


def test_rejects_candidate_marked_deployed() -> None:
    payload = copy.deepcopy(MANIFEST)
    payload["candidate_baseline"]["deployed"] = True
    with pytest.raises(MODULE.EvidenceAuditError, match="deployed=false"):
        MODULE.validate_manifest(payload, check_files=False)


def test_rejects_missing_evidence_anchor() -> None:
    payload = copy.deepcopy(MANIFEST)
    payload["criteria"][0]["claims"][0]["evidence"][0]["path"] = "does-not-exist.md"
    with pytest.raises(MODULE.EvidenceAuditError, match="evidence is missing"):
        MODULE.validate_manifest(payload)


def test_rejects_path_escape() -> None:
    payload = copy.deepcopy(MANIFEST)
    payload["criteria"][0]["claims"][0]["evidence"][0]["path"] = "../secret"
    with pytest.raises(MODULE.EvidenceAuditError, match="inside the repository"):
        MODULE.validate_manifest(payload, check_files=False)


def test_rejects_serving_candidate_identity_collapse() -> None:
    payload = copy.deepcopy(MANIFEST)
    payload["candidate_baseline"]["last_verified_sha"] = payload["serving_release"]["release_sha"]
    with pytest.raises(MODULE.EvidenceAuditError, match="separately unreleased"):
        MODULE.validate_manifest(payload, check_files=False)
