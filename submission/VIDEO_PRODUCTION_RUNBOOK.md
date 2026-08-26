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
rehearsal from the real browser state machine. In autonomous-monitor mode it
preserves all seven visible clicks, including deliberate focus of the
named-approver field, keeps the
approval-to-reopen path continuous, uses the candidate
architecture only after the browser proof, burns judge-critical captions into
the picture, embeds the matching English caption track, and holds -16 LUFS
reference narration with no detected four-second silence or black interval.
The opening frames now expose the ten-stage continuous PM operating loop, and
the post-council hold shows what the agents completed before human approval.
It is permanently watermarked **UNRELEASED LOCAL CANDIDATE · NOT PRODUCTION**.
This is the edit blueprint to reproduce against the released exact SHA, not an
uploadable proof artifact.

The fallback-mode capture has eight visible clicks because it additionally
activates **Run demo measurement fallback**. Keep the two click counts tied to
their modes; do not describe the seven-click autonomous presentation as an
eight-click run.

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
- From the repository root, start the local autonomous rehearsal exactly as
  follows; Vite's checked-in proxy targets port 8080:

  ```sh
  DECISION_TWIN_AUTONOMOUS_MONITOR=true uv run --project backend \
    uvicorn app.api:app --host 127.0.0.1 --port 8080
  npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173
  CAPTURE_PRESENTATION_MODE=true node \
    scripts/capture_decision_twin_candidate.mjs /tmp/driftline-presentation.mp4
  ```

  Run the servers in separate terminals. A backend on port 8000 is not a valid
  default rehearsal setup unless `VITE_DEV_API_TARGET` is explicitly changed.
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
- For the final release gallery, set a 1600×900 viewport and provide all four
  custody paths together:

  ```sh
  CAPTURE_WIDTH=1600 CAPTURE_HEIGHT=900 \
  CAPTURE_EXPECT_RELEASE_SHA="$RELEASE_SHA" \
  CAPTURE_EXPECT_BUILD_ID="$BUILD_ID" \
  CAPTURE_HERO_SCREENSHOT=/tmp/driftline-release-hero.png \
  CAPTURE_GENERATION_1_SCREENSHOT=/tmp/driftline-release-generation-1.png \
  CAPTURE_FINAL_SCREENSHOT=/tmp/driftline-release-generation-2.png \
  CAPTURE_GALLERY_MANIFEST=/tmp/driftline-release-gallery.json \
    node scripts/capture_decision_twin_candidate.mjs \
      /tmp/driftline-release-continuous-proof.mp4
  ```

  The manifest is emitted only after the identity preflight, all real clicks,
  all three screenshots, the bounded receipt, generation-2 assertions, and
  continuous proof-video encoding pass in one browser session. It binds each
  absolute source path, dimensions, and SHA-256. Do not rename or modify an
  image between capture and final rendering.
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
9. Show the cleared approver, disabled new action, 10/10 evaluation checks, measured
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
- Confirm the live URL is visible immediately and the first real agent action
  occurs within 15 seconds; show no sign-up, setup, loading, or title-card wait.
  The last frame must contain project name, URL, repository, category, and
  Google technology.
- Record the exact timestamp where the Cloud Run console or live `*.run.app`
  backend first becomes visible. The final manifest must name which proof type
  was used and bind it to the same release identity.
- Record the exact timestamps where the named-human approval completes, the
  bounded action receipt becomes visible, and generation 2 reopens. Scrub those
  frames before accepting the take: approval must show a non-empty named human
  and successful authorization; the receipt must visibly follow it; and
  generation 2 must show the cleared approver plus preserved generation-1
  lineage. Narration or captions are not substitutes for visible state.
- Record the first real agent-action timestamp and affirm that the entire take
  is one continuous native recording with setup and loading omitted. The final
  package gate rejects an action later than 15 seconds or a manifest that does
  not affirm those visible conditions.
- Copy `submission/final-demo-manifest.template.json`, replace every placeholder
  from the exact released take, hash the final MP4 and SRT, and run:
  `scripts/verify_final_demo_package.sh VIDEO.mp4 CAPTIONS.srt MANIFEST.json`.
  Reject the package unless release, `/health`, and public-main SHAs match; the
  first action occurs within 15 seconds; the full take and approval-to-reopen
  core are continuous; the external-write boundary and Cloud proof are visible;
  captions cover every judge-critical claim; and media,
  loudness, silence, black-frame, duration, and checksum gates pass.
- Generate the timestamp-bound visual audit with
  `scripts/render_final_demo_review_sheet.sh VIDEO.mp4 MANIFEST.json REVIEW.png`.
  Inspect the 1920×1080 sheet at original resolution. Its fixed order is named
  approval, action receipt, generation-2 reopen, and visible Google Cloud
  proof. The renderer rejects zeroed, out-of-order, late, or out-of-bounds
  manifest timestamps and burns each proof label into the image. Reject the
  take if any panel fails its label.

## Release-bound submission render

After the authorized release, final native take, public video upload, and fresh
release screenshots all pass, run `scripts/render_release_submission.py` using
the final manifest. Its output directory must be outside the repository and
empty. The renderer copies the three gallery images, replaces the candidate
architecture badge with **RELEASE VERIFIED**, binds all copy to the exact SHA,
revision, build, image digest, video hash, and caption hash, and records hashes
for every emitted visual. It also requires the one-session gallery manifest to
match the final release, every supplied image byte-for-byte, and the encoded
complete-click capture proof by hash, then emits a portable normalized copy. It
stages atomically so a failed check cannot leave a half-valid packet at the
requested path.

Do not commit the rendered packet. A post-deploy commit containing release IDs
would move public `main` beyond the deployed SHA and invalidate the exact-SHA
gate. The renderer validates that the video URL names a specific YouTube or
Vimeo video, but it cannot prove public visibility; verify that separately in a
fresh logged-out browser before the entrant approves submission.

## Take log

| Take | Release SHA | Duration | Approval continuous | Secrets clean | Notes |
| --- | --- | ---: | --- | --- | --- |
| Browser QA | `03ec8f12fc23d265c89b462a345a5b599a6411e8` | Continuous live workflow verified; final recording open | Yes | Yes | Desktop and 390px journeys passed; console clean. |

## Entrant-owned final actions

The entrant records the narration/on-screen take, approves the final edit, and
uploads it publicly to YouTube or Vimeo. Those actions require identity,
voice/likeness, and public-publishing decisions and are intentionally not
performed by automation.
