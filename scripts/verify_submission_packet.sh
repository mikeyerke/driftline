#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'Submission packet check failed: %s\n' "$1" >&2
  exit 1
}

require_text() {
  local file="$1"
  local text="$2"
  rg -Fq -- "$text" "$file" || fail "$file is missing required text: $text"
}

for file in \
  devpost-submission.md \
  submission/DEVPOST.md \
  submission/DEMO_SCRIPT.md \
  submission/REMOTE_CHECKLIST.md \
  submission/GITHUB_REPOSITORY_METADATA.md \
  submission/DEVPOST_FORM_AUDIT.md \
  submission/JUDGE_EVIDENCE_INDEX.md \
  submission/ORIGINALITY_PROVENANCE.md \
  submission/THIRD_PARTY_DISCLOSURE.md \
  submission/JUDGE_SCORECARD.md \
  submission/final-demo-manifest.template.json \
  docs/JUDGE_SCORECARD.md \
  scripts/build_final_demo_rehearsal.sh \
  scripts/build_candidate_rehearsal.sh \
  scripts/verify_final_demo_package.sh \
  scripts/verify_contest_provenance.sh \
  scripts/verify_third_party_licenses.py \
  scripts/summarize_real_pm_pilot.py \
  scripts/verify_release_candidate_local.sh \
  docs/REAL_PM_CUSTOMER_SPRINT.md \
  docs/validation/real-pm-pilot-template.json \
  submission/assets/driftline-candidate-rehearsal-narration.txt \
  submission/assets/driftline-candidate-rehearsal-overlays.svg \
  submission/assets/driftline-final-rehearsal-narration.txt \
  submission/assets/driftline-final-rehearsal.srt \
  submission/assets/driftline-final-take.srt \
  submission/assets/driftline-final-rehearsal-watermark.svg \
  submission/assets/driftline-final-rehearsal-caption-overlays.svg \
  submission/assets/ASSET_REVIEW.md \
  submission/assets/driftline-decision-twin-final.srt \
  submission/assets/driftline-decision-twin-candidate-architecture.svg \
  submission/assets/driftline-decision-twin-candidate-architecture.png; do
  [[ -s "$file" ]] || fail "$file is missing or empty"
done

cmp -s docs/JUDGE_SCORECARD.md submission/JUDGE_SCORECARD.md || \
  fail "judge scorecards have diverged"

if rg -Fq -- 'Final candidate identity is public `main`' submission/DEMO_SCRIPT.md; then
  fail "demo script mislabels the pre-candidate production release as the final candidate"
fi
if rg -Fq -- '1b8a8bfbcf2249136dbf08de54c0f7ee15f575d6' README.md; then
  fail "README release truth still carries the superseded August 24 identity"
fi
require_text submission/DEMO_SCRIPT.md 'This is the pre-candidate release,'
require_text submission/DEMO_SCRIPT.md 'Reject the take unless public `main`,'
require_text scripts/release_and_verify.sh './scripts/verify_release_candidate_local.sh --release-candidate'
require_text scripts/verify_release_candidate_local.sh 'expected mikeyerke/driftline'
require_text scripts/verify_release_candidate_local.sh 'refs/heads/$release_ref'
require_text scripts/verify_final_demo_package.sh 'approval_to_reopen_continuous'
require_text scripts/verify_final_demo_package.sh 'External writes: none'
require_text scripts/verify_final_demo_package.sh 'google_cloud_proof_type'
require_text scripts/verify_final_demo_package.sh 'Google Cloud proof must begin at least ten seconds before the video ends'
require_text scripts/verify_final_demo_package.sh 'quarantined rehearsal or historical proof asset'
require_text scripts/verify_final_demo_package.sh 'driftline-final-demo-rehearsal.mp4'
require_text scripts/verify_final_demo_package.sh 'persistent red top-band custody watermark detected'
require_text scripts/verify_final_demo_package.sh 'video content matches a quarantined rehearsal or historical proof asset'
require_text submission/JUDGE_EVIDENCE_INDEX.md '0:00–0:11'
require_text submission/JUDGE_EVIDENCE_INDEX.md 'Not demonstrated by the video'
require_text submission/assets/README.md 'detects a 4.53-second narration silence'
require_text submission/VIDEO_PRODUCTION_RUNBOOK.md 'verify_final_demo_package.sh'
require_text submission/VIDEO_PRODUCTION_RUNBOOK.md 'it is not a substitute for visible deployment proof'
require_text submission/VIDEO_PRODUCTION_RUNBOOK.md 'driftline-final-take.srt'
require_text submission/assets/ASSET_REVIEW.md 'inspected at original resolution'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_EXPECT_ACTION'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_FINAL_SCREENSHOT'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_EXPECT_RELEASE_SHA'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_EXPECT_BUILD_ID'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_PRESENTATION_MODE'
require_text scripts/capture_decision_twin_candidate.mjs 'current-release decision-loop proof'
require_text scripts/build_final_demo_rehearsal.sh 'continuous browser proof'
require_text submission/assets/driftline-final-rehearsal-watermark.svg 'UNRELEASED LOCAL CANDIDATE'
require_text scripts/summarize_real_pm_pilot.py 'unexpected fields are forbidden to reduce identity/raw-data risk'
require_text scripts/summarize_real_pm_pilot.py 'not a customer'
require_text scripts/summarize_real_pm_pilot.py 'No public pilot statement is authorized.'
require_text docs/REAL_PM_CUSTOMER_SPRINT.md 'A paid'
require_text docs/REAL_PM_CUSTOMER_SPRINT.md 'It should never send a message'
require_text README.md 'exactly equals the'
require_text docs/STATUS.md '## Unreleased candidate custody'
require_text submission/REMOTE_CHECKLIST.md 'Nothing here authorizes a push, merge, Cloud'
require_text submission/GITHUB_REPOSITORY_METADATA.md 'requires explicit publication authorization'
require_text submission/GITHUB_REPOSITORY_METADATA.md 'google-adk'
require_text submission/DEVPOST_FORM_AUDIT.md 'No Devpost account login'
require_text submission/DEVPOST_FORM_AUDIT.md 'not proof of exact form compatibility'
require_text README.md '## Judge it in 60 seconds'
require_text README.md 'The local candidate is **not deployed**.'
require_text README.md '03ec8f12fc23d265c89b462a345a5b599a6411e8'
require_text README.md 'c01bec2e-a950-407c-873b-b1d4fdc6bae6'
require_text submission/DEVPOST.md 'unreleased local candidate'
require_text submission/DEVPOST.md 'The repository timeline does not prove what the source package contained.'
require_text submission/DEVPOST.md '**Taskmaster proof:** one named authorization'
require_text submission/DEVPOST.md '**Firebase Hosting** for the stable public judge URL'
require_text devpost-submission.md 'Status: draft-ready, not release-ready or form-ready.'
require_text devpost-submission.md '| Submitter type | Individuals |'
require_text devpost-submission.md '| Project start date | 08-18-26 |'
require_text devpost-submission.md '| Originality disclosure | **OWNER GATE:**'
require_text devpost-submission.md '| Google SDK | Agent Development Kit (ADK) |'
require_text devpost-submission.md '| Google Cloud service selections | Cloud Run; Firestore |'
require_text devpost-submission.md '| Additional Google Cloud services described in entry | Firebase Hosting; BigQuery; Vertex AI;'
require_text devpost-submission.md '| Google AI model | Gemini 3.5 Flash via Vertex AI (global endpoint) |'
require_text devpost-submission.md '| Private testing instructions | Open https://driftline-ops.web.app/'
require_text devpost-submission.md '| Architecture upload | `submission/assets/driftline-decision-twin-architecture.png` |'
require_text submission/DEMO_SCRIPT.md 'I kept making roadmap calls whose evidence changed after the'
require_text submission/DEMO_SCRIPT.md 'driftline-final-take.srt'
require_text submission/DEMO_SCRIPT.md 'one continuous native screen capture'
require_text submission/DEMO_SCRIPT.md 'driftline-xvxczqg62a-uc.a.run.app/health'
require_text submission/assets/driftline-final-take.srt 'External writes: none'
require_text submission/assets/driftline-final-take.srt 'LIVE GOOGLE CLOUD PROOF'
require_text submission/BUILD_STORY.md 'for the purpose of entering the Google All Things'
require_text submission/BUILD_STORY.md 'evidence → dissent → counterfactuals → human experiment → outcome → reopen'
require_text submission/BUILD_STORY.md 'It does not yet prove independent PM adoption'
require_text submission/ORIGINALITY_PROVENANCE.md 'Entrant attestation required before submission'
require_text submission/ORIGINALITY_PROVENANCE.md '2026-08-18 13:57:39Z'
require_text scripts/verify_contest_provenance.sh 'EXPECTED_ROOT="b7a45f1b456f8e5e8cb630574b6e829bd4f575c4"'
require_text submission/THIRD_PARTY_DISCLOSURE.md '82 third-party Python distributions'
require_text submission/THIRD_PARTY_DISCLOSURE.md '44 Node package-lock entries'
require_text scripts/verify_third_party_licenses.py 'Third-party license checks passed'
require_text submission/assets/driftline-decision-twin-candidate-architecture.svg 'UNRELEASED CANDIDATE'
require_text submission/assets/driftline-decision-twin-candidate-architecture.svg 'release proof required before publication'
require_text submission/assets/driftline-decision-twin-architecture.svg 'Firebase → Cloud Run + Firestore'
require_text submission/assets/driftline-decision-twin-candidate-architecture.svg 'Firebase → Cloud Run + Firestore'
require_text submission/assets/driftline-candidate-rehearsal-overlays.svg 'UNRELEASED LOCAL CANDIDATE · NOT PRODUCTION'
require_text submission/assets/driftline-candidate-rehearsal-narration.txt 'not production proof'
require_text submission/assets/driftline-final-rehearsal-narration.txt 'not production proof'
require_text submission/assets/driftline-final-rehearsal-caption-overlays.svg 'External writes: none'

if rg -Fq -- 'submission/assets/driftline-architecture.png' devpost-submission.md; then
  fail "form packet still points at the historical architecture diagram"
fi

if rg -Fq -- '| Google Cloud services | Cloud Run; Firestore; BigQuery |' devpost-submission.md; then
  fail "form packet treats BigQuery as a selectable Google Cloud dropdown option"
fi

python3 - <<'PY'
import hashlib
from pathlib import Path
import re
import struct

def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"Submission packet check failed: {path} is not a PNG")
    return struct.unpack(">II", data[16:24])


for path in Path("submission/assets").glob("decision-twin-*-final.png"):
    png_dimensions(path)


expected_dimensions = {
    Path("submission/assets/driftline-decision-twin-architecture.png"): (1600, 900),
    Path("submission/assets/driftline-decision-twin-candidate-architecture.png"): (1600, 900),
    Path("submission/assets/decision-twin-generation-1-final.png"): (1600, 900),
    Path("submission/assets/decision-twin-generation-2-final.png"): (1600, 900),
    Path("submission/assets/decision-twin-generation-2-receipt-final.png"): (1600, 900),
    Path("submission/assets/decision-twin-mobile-hero-final.png"): (390, 844),
    Path("submission/assets/decision-twin-mobile-result-final.png"): (390, 844),
    Path("submission/assets/decision-twin-mobile-result-candidate.png"): (390, 844),
    Path("submission/assets/driftline-final-slide.png"): (1440, 810),
}
for path, expected_size in expected_dimensions.items():
    if not path.is_file():
        raise SystemExit(f"Submission packet check failed: {path} is missing")
    actual_size = png_dimensions(path)
    if actual_size != expected_size:
        raise SystemExit(
            f"Submission packet check failed: {path} is "
            f"{actual_size[0]}x{actual_size[1]}, expected "
            f"{expected_size[0]}x{expected_size[1]}"
        )

reviewed_assets = {
    Path("submission/assets/driftline-decision-twin-architecture.png"): "fe68de40fc7d07e29a5b55c9af425c2e2517f0e6c4fd9c3b65a6df31685486c4",
    Path("submission/assets/driftline-decision-twin-candidate-architecture.png"): "b439c5eb3062d89384dc0cc7046578b8d73b9c738c737e0b6e4e999d781d631e",
    Path("submission/assets/decision-twin-generation-1-final.png"): "b5bef1a0ac833a145784d8c60cdd83c89fc8c15b850011b7aee1e4cfaae93ab9",
    Path("submission/assets/decision-twin-generation-2-final.png"): "d0aaaa42995fbcb0fee961fb2d849f341e817396f0cef7ca4ff3919b190e2158",
    Path("submission/assets/decision-twin-generation-2-receipt-final.png"): "476ad1e87466d758ab7bc1ce26b0bb51a91de8e60d258f73da9d0d834620c2dd",
    Path("submission/assets/decision-twin-mobile-hero-final.png"): "14641f53460b068a457e9070e502b538d201498d71004f257c85dc88e2c74096",
    Path("submission/assets/decision-twin-mobile-result-final.png"): "886b04a6ce35de033453e282631cd2c17d94ba3c664c48adabf5a9617f050255",
    Path("submission/assets/decision-twin-mobile-result-candidate.png"): "aec229829e2d2800375f0195e2810e06a1e9423b2dc3bf25be750c5ea097ff22",
}
for path, expected in reviewed_assets.items():
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(
            f"Submission packet check failed: {path} does not match its reviewed "
            "full-frame asset; inspect the replacement before deliberately "
            f"updating the checksum (actual {actual})"
        )

link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
for document in (
    Path("README.md"),
    Path("devpost-submission.md"),
    Path("submission/DEVPOST.md"),
):
    for target in link_pattern.findall(document.read_text()):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        resolved = (document.parent / target_path).resolve()
        if not resolved.exists():
            raise SystemExit(
                f"Submission packet check failed: {document} links to missing {target}"
            )

timestamp_pattern = re.compile(
    r"(?P<sh>\d{2}):(?P<sm>\d{2}):(?P<ss>\d{2}),(?P<sms>\d{3})\s+-->\s+"
    r"(?P<eh>\d{2}):(?P<em>\d{2}):(?P<es>\d{2}),(?P<ems>\d{3})"
)


def srt_seconds(match: re.Match[str], prefix: str) -> float:
    return (
        int(match[f"{prefix}h"]) * 3600
        + int(match[f"{prefix}m"]) * 60
        + int(match[f"{prefix}s"])
        + int(match[f"{prefix}ms"]) / 1000
    )


for caption_path in (
    Path("submission/assets/driftline-final-rehearsal.srt"),
    Path("submission/assets/driftline-final-take.srt"),
):
    cues = [
        (srt_seconds(match, "s"), srt_seconds(match, "e"))
        for match in timestamp_pattern.finditer(caption_path.read_text())
    ]
    if len(cues) != 15 or cues[0][0] != 0 or cues[-1][1] != 178:
        raise SystemExit(
            f"Submission packet check failed: {caption_path} must contain "
            "15 cues covering exactly 0-178 seconds"
        )
    previous_end = 0.0
    for start, end in cues:
        if start < previous_end or end <= start:
            raise SystemExit(
                f"Submission packet check failed: {caption_path} has "
                "overlapping or invalid caption timings"
            )
        previous_end = end
PY

todo_lines="$(rg -n -i 'todo|placeholder|tbd|fixme|lorem' \
  devpost-submission.md submission/DEVPOST.md || true)"
unexpected_todo_lines="$(printf '%s\n' "$todo_lines" | rg -v \
  '(public YouTube or Vimeo URL|publish an approved draft from `submission/SOCIAL_POST_DRAFTS\.md`)' || true)"
[[ -z "$unexpected_todo_lines" ]] || \
  fail "unexpected placeholder text exists in the canonical submission copy"
[[ "$(printf '%s\n' "$todo_lines" | rg -c '.' || true)" == "3" ]] || \
  fail "the submission packet must contain exactly the three approved owner-only placeholders"

printf 'Submission packet checks passed.\n'
