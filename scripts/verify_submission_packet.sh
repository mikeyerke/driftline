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
  grep -Fq -- "$text" "$file" || fail "$file is missing required text: $text"
}

for file in \
  devpost-submission.md \
  submission/DEVPOST.md \
  submission/DEMO_SCRIPT.md \
  submission/REMOTE_CHECKLIST.md \
  submission/GITHUB_REPOSITORY_METADATA.md \
  submission/DEVPOST_FORM_AUDIT.md \
  submission/JUDGE_EVIDENCE_INDEX.md \
  submission/judge-evidence-manifest.json \
  submission/entrant-attestations.template.json \
  submission/ORIGINALITY_PROVENANCE.md \
  submission/THIRD_PARTY_DISCLOSURE.md \
  submission/SOCIAL_POST_DRAFTS.md \
  submission/BONUS_PUBLICATION_CHECKLIST.md \
  submission/JUDGE_SCORECARD.md \
  submission/final-demo-manifest.template.json \
  docs/JUDGE_SCORECARD.md \
  scripts/build_final_demo_rehearsal.sh \
  scripts/build_candidate_rehearsal.sh \
  scripts/verify_final_demo_package.sh \
  scripts/prepare_final_demo_manifest.py \
  scripts/verify_judge_evidence.py \
  scripts/verify_submission_readiness.py \
  scripts/render_release_submission.py \
  scripts/render_final_demo_review_sheet.sh \
  scripts/verify_contest_provenance.sh \
  scripts/verify_third_party_licenses.py \
  scripts/summarize_real_pm_pilot.py \
  scripts/verify_clean_checkout.sh \
  scripts/verify_release_candidate_local.sh \
  docs/REAL_PM_CUSTOMER_SPRINT.md \
  docs/validation/real-pm-pilot-template.json \
  submission/assets/driftline-candidate-rehearsal-narration.txt \
  submission/assets/driftline-candidate-rehearsal-overlays.svg \
  submission/assets/driftline-final-rehearsal-narration.txt \
  submission/assets/driftline-final-rehearsal.srt \
  submission/assets/driftline-final-take.srt \
  submission/assets/driftline-final-rehearsal-watermark.svg \
  submission/assets/final-demo-review-sheet-labels.svg \
  submission/assets/driftline-final-rehearsal-caption-overlays.svg \
  submission/assets/ASSET_REVIEW.md \
  submission/assets/driftline-decision-twin-final.srt \
  submission/assets/driftline-decision-twin-candidate-architecture.svg \
  submission/assets/driftline-decision-twin-candidate-architecture.png; do
  [[ -s "$file" ]] || fail "$file is missing or empty"
done

cmp -s docs/JUDGE_SCORECARD.md submission/JUDGE_SCORECARD.md || \
  fail "judge scorecards have diverged"

if grep -Fq -- 'Final candidate identity is public `main`' submission/DEMO_SCRIPT.md; then
  fail "demo script mislabels the pre-candidate production release as the final candidate"
fi
if grep -Fq -- '1b8a8bfbcf2249136dbf08de54c0f7ee15f575d6' README.md; then
  fail "README release truth still carries the superseded August 24 identity"
fi
require_text submission/DEMO_SCRIPT.md 'This is the pre-candidate release,'
require_text submission/DEMO_SCRIPT.md 'Reject the take unless public `main`,'
require_text scripts/release_and_verify.sh './scripts/verify_release_candidate_local.sh --release-candidate'
require_text scripts/release_and_verify.sh 'DRIFTLINE_RELEASE_IDENTITY_OUT'
require_text scripts/release_and_verify.sh 'prepare_final_demo_manifest.py'
require_text scripts/verify_production.sh 'Release identity receipt:'
require_text scripts/verify_production.sh 'public main %s does not equal serving SHA %s'
require_text scripts/verify_production.sh 'refuses unexpected origin'
require_text scripts/release_and_verify.sh 'requires the canonical Firebase judge URL'
require_text scripts/prepare_final_demo_manifest.py 'release, health, public-main, and trace SHAs must match'
require_text scripts/prepare_final_demo_manifest.py 'manifest seed output must be outside the repository'
require_text scripts/verify_release_candidate_local.sh 'expected mikeyerke/driftline'
require_text scripts/verify_release_candidate_local.sh 'refs/heads/$release_ref'
require_text scripts/verify_final_demo_package.sh 'approval_to_reopen_continuous'
require_text scripts/verify_final_demo_package.sh 'first_agent_action_timestamp_seconds'
require_text scripts/verify_final_demo_package.sh 'the first visible agent action must occur within the first 15 seconds'
require_text scripts/verify_final_demo_package.sh 'preapproval_background_workflow_visible'
require_text scripts/verify_final_demo_package.sh 'release identity receipt hash is missing or invalid'
require_text scripts/verify_final_demo_package.sh 'continuous_native_take'
require_text scripts/verify_final_demo_package.sh 'setup_and_loading_omitted'
require_text scripts/verify_final_demo_package.sh 'named_human_approval_visible'
require_text scripts/verify_final_demo_package.sh 'bounded_action_receipt_timestamp_seconds'
require_text scripts/verify_final_demo_package.sh 'generation_2_reopen_visible'
require_text scripts/verify_final_demo_package.sh 'generation_1_lineage_visible'
require_text scripts/render_final_demo_review_sheet.sh 'NAMED HUMAN APPROVAL'
require_text scripts/render_final_demo_review_sheet.sh 'BOUNDED ACTION RECEIPT'
require_text scripts/render_final_demo_review_sheet.sh 'GENERATION 2 REOPEN'
require_text scripts/render_final_demo_review_sheet.sh 'VISIBLE GOOGLE CLOUD PROOF'
require_text scripts/capture_decision_twin_candidate.mjs 'Could not show the generation-2 learning receipt in the capture'
require_text scripts/render_final_demo_review_sheet.sh 'approval must be between 60 and 100 seconds'
require_text scripts/render_final_demo_review_sheet.sh 'generation 2 must follow receipt by 140 seconds'
require_text submission/assets/final-demo-review-sheet-labels.svg 'NAMED HUMAN APPROVAL'
require_text submission/assets/final-demo-review-sheet-labels.svg 'BOUNDED ACTION RECEIPT'
require_text submission/assets/final-demo-review-sheet-labels.svg 'GENERATION 2 REOPEN'
require_text submission/assets/final-demo-review-sheet-labels.svg 'VISIBLE GOOGLE CLOUD PROOF'
require_text scripts/verify_final_demo_package.sh 'External writes: none'
require_text scripts/verify_final_demo_package.sh 'google_cloud_proof_type'
require_text scripts/verify_final_demo_package.sh 'Google Cloud proof must begin at least ten seconds before the video ends'
require_text scripts/verify_final_demo_package.sh 'quarantined rehearsal or historical proof asset'
require_text scripts/verify_final_demo_package.sh 'driftline-final-demo-rehearsal.mp4'
require_text scripts/verify_final_demo_package.sh 'persistent red top-band custody watermark detected'
require_text scripts/render_release_submission.py 'release-bound output directory must be outside the repository'
require_text scripts/render_release_submission.py 'candidate_watermark_absent'
require_text scripts/render_release_submission.py 'public_main_sha'
require_text scripts/render_release_submission.py 'continuous_browser_session'
require_text scripts/render_release_submission.py 'gallery proof-video hash does not match'
require_text scripts/render_release_submission.py 'actual final video hash does not match the manifest'
require_text scripts/render_release_submission.py 'render_final_demo_review_sheet.sh'
require_text scripts/render_release_submission.py 'final demo review sheet must be 1920x1080'
require_text scripts/render_release_submission.py 'RELEASE VERIFIED'
require_text scripts/render_release_submission.py '10/10 policy checks'
require_text scripts/verify_final_demo_package.sh 'video content matches a quarantined rehearsal or historical proof asset'
require_text submission/JUDGE_EVIDENCE_INDEX.md '0:00–0:11'
require_text submission/JUDGE_EVIDENCE_INDEX.md 'Not demonstrated by the video'
require_text submission/JUDGE_EVIDENCE_INDEX.md 'the first visible agent action occurs after 0:15'
require_text submission/JUDGE_EVIDENCE_INDEX.md 'completes a multi-step background workflow without human intervention'
require_text submission/JUDGE_EVIDENCE_INDEX.md 'Before any human action'
require_text submission/JUDGE_SCORECARD.md 'require a timestamped first'
require_text submission/JUDGE_SCORECARD.md 'agent action by 0:15'
require_text submission/JUDGE_SCORECARD.md '`scripts/verify_clean_checkout.sh` separately exports only committed `HEAD`'
require_text submission/JUDGE_SCORECARD.md 'redacted multi-source evidence pack via PR #24'
require_text submission/JUDGE_SCORECARD.md 'fail-closed release-packet chain via PRs #27-#29'
require_text submission/JUDGE_SCORECARD.md 'Each PR #26-#29 tested tree was identical'
require_text submission/JUDGE_SCORECARD.md 'e4a2f474002c151ab29b08528915292543afd7f2'
require_text submission/JUDGE_SCORECARD.md '484e764760c06350733189246a17dfa651502891'
require_text submission/JUDGE_SCORECARD.md '32986603518'
require_text submission/JUDGE_SCORECARD.md 'a favorable self-report can never create a customer claim'
require_text submission/JUDGE_SCORECARD.md 'captured 573'
require_text submission/JUDGE_SCORECARD.md 'exactly 178.000'
require_text submission/JUDGE_SCORECARD.md 'roughly 95/100 submission readiness'
require_text submission/JUDGE_SCORECARD.md 'dfdbe2b22579135b9ebedab71ee2bfbe38fc897b'
require_text submission/JUDGE_SCORECARD.md '32988583543'
require_text submission/assets/README.md 'detects a 4.53-second narration silence'
require_text submission/VIDEO_PRODUCTION_RUNBOOK.md 'verify_final_demo_package.sh'
require_text submission/VIDEO_PRODUCTION_RUNBOOK.md 'it is not a substitute for visible deployment proof'
require_text submission/VIDEO_PRODUCTION_RUNBOOK.md 'driftline-final-take.srt'
require_text submission/assets/ASSET_REVIEW.md 'inspected at original resolution'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_EXPECT_ACTION'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_FINAL_SCREENSHOT'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_HERO_SCREENSHOT'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_GENERATION_1_SCREENSHOT'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_GALLERY_MANIFEST'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_EXPECT_RELEASE_SHA'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_EXPECT_BUILD_ID'
require_text scripts/capture_decision_twin_candidate.mjs 'CAPTURE_PRESENTATION_MODE'
require_text scripts/capture_decision_twin_candidate.mjs 'current-release decision-loop proof'
require_text scripts/build_final_demo_rehearsal.sh 'continuous browser proof'
require_text submission/assets/driftline-final-rehearsal-watermark.svg 'UNRELEASED LOCAL CANDIDATE'
require_text scripts/summarize_real_pm_pilot.py 'unexpected fields are forbidden to reduce identity/raw-data risk'
require_text scripts/summarize_real_pm_pilot.py 'not a customer'
require_text scripts/summarize_real_pm_pilot.py 'No public pilot statement is authorized.'
require_text scripts/summarize_real_pm_pilot.py 'participant independence not confirmed'
require_text scripts/summarize_real_pm_pilot.py 'not every citation was reviewed'
require_text docs/validation/real-pm-pilot-template.json '"participant_independent": false'
require_text docs/validation/real-pm-pilot-template.json '"all_citations_reviewed": false'
require_text scripts/summarize_real_pm_pilot.py 'evaluation spend, not customer revenue'
require_text scripts/summarize_real_pm_pilot.py 'product-bound private starter verified'
require_text scripts/summarize_real_pm_pilot.py 'product-bound field changed after export'
require_text scripts/summarize_real_pm_pilot.py 'starter citation review binding is inconsistent'
require_text scripts/summarize_real_pm_pilot.py 'Product-observed citation review:'
require_text scripts/summarize_real_pm_pilot.py '"--starter"'
require_text submission/REAL_PM_PILOT.md 'Download private pilot starter'
require_text submission/REAL_PM_PILOT.md 'Mark source reviewed'
require_text submission/PILOT_SESSION_WORKSHEET.md 'not product-bound'
require_text docs/validation/real-pm-pilot-template.json '"participant_recruitment_channel": "organic_opt_in"'
require_text docs/REAL_PM_CUSTOMER_SPRINT.md 'A paid'
require_text docs/REAL_PM_CUSTOMER_SPRINT.md 'It should never send a message'
require_text submission/PILOT_PROSPECT_PIPELINE.md 'driftline-pm-prospect-watch'
require_text submission/PAID_PM_RECRUIT_PACKET.md 'Compensation is for the participant'
require_text submission/PAID_PM_RECRUIT_PACKET.md 'not revenue'
require_text submission/PAID_PM_RECRUIT_PACKET.md 'Do not create an account'
require_text submission/DEVPOST.md '532 backend tests'
require_text scripts/verify_custom_decision_browser.mjs 'Custom-decision browser verification is loopback-only'
require_text scripts/verify_custom_decision_browser.mjs 'freshContextRestored'
require_text scripts/verify_custom_decision_browser.mjs 'namedApproverVisible'
require_text scripts/verify_custom_decision_browser.mjs 'keyboardRadioRoving'
require_text scripts/verify_custom_decision_browser.mjs 'minimumControlTargets'
require_text scripts/verify_custom_decision_browser.mjs 'validAriaReferences'
require_text submission/PILOT_PROSPECT_PIPELINE.md 'The watch is a discovery aid, not a sales agent.'
require_text README.md 'exactly equals the'
require_text docs/STATUS.md '## Unreleased public-main candidate custody'
require_text submission/REMOTE_CHECKLIST.md 'Nothing here authorizes a push, merge, Cloud'
require_text submission/GITHUB_REPOSITORY_METADATA.md 'requires explicit publication authorization'
require_text submission/GITHUB_REPOSITORY_METADATA.md 'google-adk'
require_text submission/DEVPOST_FORM_AUDIT.md "Devpost's authenticated MCP returned the live submission requirements"
require_text submission/DEVPOST_FORM_AUDIT.md 'No registration, project'
require_text submission/DEVPOST_FORM_AUDIT.md 'maximum size is 36,700,160 bytes (35 MiB)'
require_text submission/DEVPOST_FORM_AUDIT.md 'This audit proves the live field schema and the local packet'
for field_id in \
  28083 28084 28085 28086 28087 28141 28089 28088 28090 \
  28091 28142 28092 28093 28101 28143 28106 28107; do
  require_text submission/DEVPOST_FORM_AUDIT.md "| $field_id |"
done
require_text README.md '## Judge it in 60 seconds'
require_text README.md 'python3 scripts/verify_judge_evidence.py --live'
require_text scripts/verify_judge_evidence.py 'rubric weights do not match the official 40/30/30 criteria'
require_text scripts/verify_judge_evidence.py 'submission is not ready; open gates:'
require_text scripts/verify_submission_readiness.py 'release evidence inputs are all-or-none'
require_text scripts/verify_submission_readiness.py 'release packet must remain outside the repository'
require_text scripts/verify_submission_readiness.py 'not ready to submit; open gates:'
require_text submission/judge-evidence-manifest.json '"taskmaster_preapproval_workflow"'
require_text submission/judge-evidence-manifest.json '"record_and_publish_exact_release_video"'
require_text submission/judge-evidence-manifest.json '"phase": "ready_to_submit"'
require_text submission/judge-evidence-manifest.json '"score_gates"'
require_text submission/entrant-attestations.template.json '"submission_authorized": false'
require_text submission/REMOTE_CHECKLIST.md 'python3 scripts/verify_submission_readiness.py'
require_text README.md '**Taskmaster proof:** before the named approval'
require_text README.md 'without a prompt loop or human'
require_text README.md './scripts/verify_clean_checkout.sh'
require_text scripts/verify_clean_checkout.sh 'git archive --format=tar "$candidate_sha"'
require_text scripts/verify_clean_checkout.sh 'Clean-checkout verification: PASS'
require_text README.md 'The local candidate is **not deployed**.'
require_text README.md '03ec8f12fc23d265c89b462a345a5b599a6411e8'
require_text README.md 'c01bec2e-a950-407c-873b-b1d4fdc6bae6'
require_text submission/DEVPOST.md 'unreleased local candidate'
require_text submission/DEVPOST.md '9026ee2eccc94fd925ec00a54228c8b858442baaf8ac695e2ca56f54bbce37b0'
require_text submission/DEVPOST.md 'Its 50 regular files are timestamped August 18, 2026'
require_text submission/DEVPOST.md '**Taskmaster proof:** before any human action'
require_text submission/DEVPOST.md 'The approval is a deliberate authority boundary'
require_text submission/DEVPOST.md '**Firebase Hosting** for the stable public judge URL'
require_text devpost-submission.md 'Status: live-field-schema-ready, not release-ready, publish-ready, or'
require_text devpost-submission.md "Devpost's authenticated MCP verified all 17 custom fields"
require_text devpost-submission.md '| Submitter type | Individuals |'
require_text devpost-submission.md '| Project start date | 08-18-26 |'
require_text devpost-submission.md '| Originality disclosure | Driftline continued earlier product ideation.'
require_text devpost-submission.md '**PERSONAL ATTESTATION:** entrant must confirm ownership/rights'
require_text devpost-submission.md '| Google SDK | Agent Development Kit (ADK) |'
require_text devpost-submission.md '| Built with tags | Gemini 3.5 Flash; Vertex AI; Google Agent Development Kit;'
require_text devpost-submission.md '| Google Cloud service selections | Cloud Run; Firestore |'
require_text devpost-submission.md '| Additional Google Cloud services described in entry | Firebase Hosting; BigQuery; Vertex AI;'
require_text devpost-submission.md '| Google AI model | Gemini 3.5 Flash via Vertex AI (global endpoint) |'
require_text devpost-submission.md '| Private testing instructions | Open https://driftline-ops.web.app/'
require_text devpost-submission.md '| Architecture upload | `submission/assets/driftline-decision-twin-architecture.png` |'
require_text devpost-submission.md '| Image gallery order | 1. `submission/assets/decision-twin-hero-final.png`;'
require_text submission/DEMO_SCRIPT.md 'I kept making roadmap calls whose evidence changed after the'
require_text submission/DEMO_SCRIPT.md 'driftline-final-take.srt'
require_text submission/DEMO_SCRIPT.md 'one continuous native screen capture'
require_text submission/DEMO_SCRIPT.md 'driftline-xvxczqg62a-uc.a.run.app/health'
require_text submission/DEMO_SCRIPT.md 'complete autonomous background'
require_text submission/assets/driftline-final-take.srt 'External writes: none'
require_text submission/assets/driftline-final-take.srt 'No prompt loop or human intervention'
require_text submission/assets/driftline-final-take.srt 'LIVE GOOGLE CLOUD PROOF'
require_text submission/assets/driftline-final-take.srt 'Ten deterministic checks'
require_text submission/BUILD_STORY.md 'for the purpose of entering the Google All Things'
require_text submission/BUILD_STORY.md 'evidence → dissent → counterfactuals → human experiment → outcome → reopen'
require_text submission/BUILD_STORY.md 'It does not yet prove independent PM adoption'
require_text submission/ORIGINALITY_PROVENANCE.md '## Exact supplied-package boundary'
require_text submission/ORIGINALITY_PROVENANCE.md '## Remaining personal attestation'
require_text submission/ORIGINALITY_PROVENANCE.md '2026-08-18 13:57:39Z'
require_text scripts/verify_contest_provenance.sh 'EXPECTED_ROOT="b7a45f1b456f8e5e8cb630574b6e829bd4f575c4"'
require_text scripts/verify_contest_provenance.sh 'EXPECTED_SOURCE_ARCHIVE_SHA256="9026ee2eccc94fd925ec00a54228c8b858442baaf8ac695e2ca56f54bbce37b0"'
require_text scripts/verify_contest_provenance.sh '--source-archive'
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

for stale_claim in \
  'remains a separate PR candidate' \
  'current-HEAD local autonomous presentation run at `a0b52f8`' \
  'captured 536 state-change frames' \
  'reruns all 481 backend tests'; do
  if grep -Fq -- "$stale_claim" submission/JUDGE_SCORECARD.md; then
    fail "judge scorecard contains stale candidate evidence: $stale_claim"
  fi
done

if grep -Fq -- 'submission/assets/driftline-architecture.png' devpost-submission.md; then
  fail "form packet still points at the historical architecture diagram"
fi

if grep -Fq -- '| Google Cloud services | Cloud Run; Firestore; BigQuery |' devpost-submission.md; then
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
    Path("submission/assets/decision-twin-hero-final.png"): (1600, 900),
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

architecture_path = Path("submission/assets/driftline-decision-twin-architecture.png")
architecture_max_bytes = 36_700_160
if architecture_path.stat().st_size > architecture_max_bytes:
    raise SystemExit(
        "Submission packet check failed: architecture upload exceeds the live "
        f"Devpost 35 MiB limit ({architecture_path.stat().st_size} bytes)"
    )

reviewed_assets = {
    Path("submission/assets/decision-twin-hero-final.png"): "1434148fe26f9b271c3a56d46b231a2a4774b693eb8623a454e6c2298d3cf111",
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

devpost_first_300 = " ".join(Path("submission/DEVPOST.md").read_text().split()[:300])
for required_phrase in (
    "Taskmaster proof",
    "Gemini 3.5 Flash",
    "Google ADK",
    "Cloud Run",
    "named human",
    "Jira marker",
    "not customer ROI",
):
    if required_phrase not in devpost_first_300:
        raise SystemExit(
            "Submission packet check failed: the first 300 words of "
            f"submission/DEVPOST.md do not contain {required_phrase!r}"
        )

social_drafts = Path("submission/SOCIAL_POST_DRAFTS.md").read_text()
try:
    x_post = social_drafts.split("## X\n\n", 1)[1].strip()
except IndexError as exc:
    raise SystemExit(
        "Submission packet check failed: X social draft is missing"
    ) from exc
if len(x_post) > 280:
    raise SystemExit(
        "Submission packet check failed: X social draft is "
        f"{len(x_post)} characters, expected at most 280"
    )

tagline = (
    "Contradictory evidence becomes a reversible experiment—and the outcome "
    "can reopen the decision."
)
if len(tagline) > 140:
    raise SystemExit(
        "Submission packet check failed: Devpost tagline is "
        f"{len(tagline)} characters, expected at most 140"
    )

built_with = (
    "Gemini 3.5 Flash; Vertex AI; Google Agent Development Kit; Cloud Run; "
    "Firestore; BigQuery; Cloud Tasks; Cloud Scheduler; Firebase Hosting; "
    "Cloud Build; Artifact Registry; Cloud Storage; Secret Manager; React; "
    "FastAPI; Python"
)
if len(built_with.split("; ")) > 25:
    raise SystemExit(
        "Submission packet check failed: Built with exceeds Devpost's "
        "25-tag generic limit"
    )
PY

todo_lines="$(grep -HniE 'todo|placeholder|tbd|fixme|lorem' \
  devpost-submission.md submission/DEVPOST.md || true)"
unexpected_todo_lines="$(printf '%s\n' "$todo_lines" | grep -Ev \
  '(public YouTube or Vimeo URL|publish the reviewed Decision Twin story|publish an approved draft from `submission/SOCIAL_POST_DRAFTS\.md`)' || true)"
[[ -z "$unexpected_todo_lines" ]] || \
  fail "unexpected placeholder text exists in the canonical submission copy"
[[ "$(printf '%s\n' "$todo_lines" | grep -c '.' || true)" == "4" ]] || \
  fail "the submission packet must contain exactly the four approved owner-only placeholders"

python3 scripts/verify_judge_evidence.py >/dev/null || \
  fail "machine-readable judge evidence audit failed"

printf 'Submission packet checks passed.\n'
