# Final demo video production runbook

Status: exact-release frames, captions, architecture, and a three-minute 1080p
reference cut are ready. The existing 43-second MP4 is historical and must not
be submitted. Prefer one continuous native browser take for the final upload;
nothing has been published.

Brutal QA note: `driftline-final-demo-candidate.mp4` is a technically clean
fallback, not the winning final. It is 3:40, 1920×1080 at 30 fps, has integrated
audio near -16.3 LUFS with -4.5 dB true peak, and contains no detected black
frames. It is nevertheless built mostly from long static browser frames and
mixes candidate screens with pre-candidate release narration. Do not submit it.

`scripts/build_candidate_rehearsal.sh` produces a 52-second local-only review
artifact from the continuous candidate proof. It is permanently watermarked
**UNRELEASED LOCAL CANDIDATE · NOT PRODUCTION**, ends on the pending release
identity gate, and validates format, duration, loudness, and black intervals.
It is a rehearsal template, not the final upload.

`CAPTURE_PRESENTATION_MODE=true` plus
`scripts/build_final_demo_rehearsal.sh` now produces a 2:58 long-form local
rehearsal from the real browser state machine. It preserves all eight visible
clicks, including deliberate focus of the named-approver field, keeps the
approval-to-reopen path continuous, uses the candidate
architecture only after the browser proof, burns judge-critical captions into
the picture, embeds the matching English caption track, and holds -16 LUFS
reference narration with no detected four-second silence or black interval.
It is permanently watermarked **UNRELEASED LOCAL CANDIDATE · NOT PRODUCTION**.
This is the edit blueprint to reproduce against the released exact SHA, not an
uploadable proof artifact.

The repository includes `scripts/capture_decision_twin_candidate.mjs` as a
local-only continuity rehearsal. With the local API on port 8080 and the Vite
frontend on port 5173, it drives a fresh headless Chrome session through the
actual generation-1 council, response comparison, named approval, measured
outcome, internal-action rollback, and generation-2 reopen. The script fails
unless generation 2 is present, rollback is selected, the approver is cleared,
external writes remain none, and the action is visibly rolled back. It emits a
silent 1280 × 720 H.264 proof clip with a visible pointer and click pulse. Every
captured control is activated through Chrome's mouse-input protocol rather than
a direct DOM `.click()`. The recorded sequence now centers the complete action
and learning receipt before returning to the generation-2 choice, so the video
itself—not a DOM assertion—contains the decisive state change. That clip is
candidate QA and must not be described as deployed or used as the entrant's
final narrated take.

## Capture setup

- 1920×1080, 30 fps, browser zoom 100%, notifications off.
- Use a fresh logged-out window for the public lane.
- Preload `/health` and either the Cloud Run service/revision console or the
  live `*.run.app` backend URL in separate tabs; verify there are no
  tokens, tenant names, private records, or editable secret fields on screen.
- Use the serving release only. Record the release SHA and build ID in the take
  log before capture.
- Do not record the candidate-only action narration until the serving release
  visibly contains the bounded allocation card and passes fresh release proof.
- Rehearse the no-sign-in **Decision Twin** path twice without recording.
- Optionally run the deterministic local continuity check twice before the
  native take:
  `node scripts/capture_decision_twin_candidate.mjs /tmp/driftline-proof.mp4`.
  Inspect the result at 1×; passing state assertions do not prove legibility.
- For a serving-release capture, also set `CAPTURE_EXPECT_RELEASE_SHA` and
  `CAPTURE_EXPECT_BUILD_ID`. The capture must verify `/health` before its first
  click and fail if either identity differs.
- For a local-only rehearsal, set
  `DECISION_TWIN_AUTONOMOUS_MONITOR=true` while leaving Cloud Tasks disabled so
  the bounded background fallback exercises the same no-second-click timing.
  This is not production proof. If the release cannot enqueue Cloud Tasks, the
  UI must immediately show **Run demo measurement fallback** and must not claim
  **Autonomous monitor active**.

## Single-take product sequence

1. Show `https://driftline-ops.web.app/`, the no-sign-in judge lane, and **Run
   the decision workflow**.
2. Start generation 1 and show the council recommendation, five cited signals,
   five independent agents, competing responses, and BigQuery-vector precedent.
3. Open the evidence/council disclosure and preserve one visible dissenting
   position.
4. Compare ship, rollback, segment, and defer; return to the recommended
   segmented experiment.
5. Show the disabled approval, enter the named reviewer, and click **Approve
   segmented experiment** in-frame.
6. If present on the verified release, show **Bounded internal action
   executed**, generation 1, decision-state-only scope, and **External writes:
   none**.
7. Stop clicking. Keep the autonomous-monitor state visible while Cloud Tasks
   processes the bounded measurement.
8. Show the action marked rolled back and generation 2 reopening automatically
   with **Roll back globally** both
   recommended and selected.
9. Show the cleared approver, disabled new action, 7/7 policy checks, measured
   invalidation, evidence/synthesis hashes, and preserved generation-1 lineage.
10. Show the Cloud Run console or live `*.run.app` backend URL in-frame, then
    finish on `/health`, the exact serving application SHA preserved at the
    public `main` tip, and the Google architecture diagram. The architecture is
    explanation; it is not a substitute for visible deployment proof.

Do not splice across the approval click and receipt. A judge should be able to
see that the result came from the visible action in the same workflow.

## B-roll inserts

- `/health`: model, persistence, tasks, serving SHA, Cloud Build ID.
- Cloud Run revision and one redacted request log.
- Decision Twin receipt: generation, evidence hash, synthesis hash, measured
  outcome, and prior-approval lineage.
- `driftline-decision-twin-architecture.png` for the closing 20–25 seconds on
  the currently verified release.
- Replace it with `driftline-decision-twin-candidate-architecture.png` only
  after the candidate's exact commit, Cloud Run revision, Cloud Build ID, image
  digest, live ADK trace, and desktop/mobile journeys have all been reverified.
  Do not show the candidate asset while its **UNRELEASED CANDIDATE** badge is
  still true.

## Edit and QA

- Target 2:50–3:20; hard reject at 3:56 to protect the four-minute rule. The
  current 2:58 blueprint proves the complete loop without spending the extra
  minute on static holds.
- Remove waits, not policy steps. Never accelerate narration beyond clarity.
- Burn in English captions and attach
  `submission/assets/driftline-final-take.srt`.
- Normalize speech, remove long silences, and confirm no music masks narration.
- Watch once at 1× without pausing, once muted for caption comprehension, and
  once at 720p for small-text legibility.
- Confirm the first 30 seconds shows the live URL and the last frame contains
  project name, URL, repository, category, and Google technology.
- Record the exact timestamp where the Cloud Run console or live `*.run.app`
  backend first becomes visible. The final manifest must name which proof type
  was used and bind it to the same release identity.
- Record the exact timestamps where the named-human approval completes, the
  bounded action receipt becomes visible, and generation 2 reopens. Scrub those
  frames before accepting the take: approval must show a non-empty named human
  and successful authorization; the receipt must visibly follow it; and
  generation 2 must show the cleared approver plus preserved generation-1
  lineage. Narration or captions are not substitutes for visible state.
- Copy `submission/final-demo-manifest.template.json`, replace every placeholder
  from the exact released take, hash the final MP4 and SRT, and run:
  `scripts/verify_final_demo_package.sh VIDEO.mp4 CAPTIONS.srt MANIFEST.json`.
  Reject the package unless release, `/health`, and public-main SHAs match; the
  approval-to-reopen core is continuous; the external-write boundary and Cloud
  proof are visible; captions cover every judge-critical claim; and media,
  loudness, silence, black-frame, duration, and checksum gates pass.
- Generate the timestamp-bound visual audit with
  `scripts/render_final_demo_review_sheet.sh VIDEO.mp4 MANIFEST.json REVIEW.png`.
  Inspect the 1920×1080 sheet at original resolution. Its fixed order is named
  approval, action receipt, generation-2 reopen, and visible Google Cloud
  proof. The renderer rejects zeroed, out-of-order, late, or out-of-bounds
  manifest timestamps and burns each proof label into the image. Reject the
  take if any panel fails its label.

## Take log

| Take | Release SHA | Duration | Approval continuous | Secrets clean | Notes |
| --- | --- | ---: | --- | --- | --- |
| Browser QA | `03ec8f12fc23d265c89b462a345a5b599a6411e8` | Continuous live workflow verified; final recording open | Yes | Yes | Desktop and 390px journeys passed; console clean. |

## Entrant-owned final actions

The entrant records the narration/on-screen take, approves the final edit, and
uploads it publicly to YouTube or Vimeo. Those actions require identity,
voice/likeness, and public-publishing decisions and are intentionally not
performed by automation.
