# Driftline Decision Twin demo — 2:58 target

Record one continuous native screen capture at 1080p and 1× speed. Do not cut,
splice, reorder, or replace any portion of the take. Switching among preloaded
browser tabs is allowed because the screen recording itself remains continuous.
The official limit is four minutes, and the judging criterion specifically asks
for live, unedited proof of action.

Use `submission/assets/driftline-final-take.srt` as the final English caption
master. The local 2:58 rehearsal follows the same pacing but has a permanent
candidate watermark and different custody captions; it is not substitutable.

Candidate-only recording gate: include the bounded internal allocation only
after the exact candidate is public `main`, deployed, and independently bound to
`/health`, Cloud Run, Cloud Build, the image digest, live trace, and fresh
desktop/mobile browser proof. Otherwise do not show or narrate that action.

## Preload before recording

Open these tabs without exposing account identity, credentials, private records,
tenant names, or editable secret fields:

1. `https://driftline-ops.web.app/`
2. `https://driftline-xvxczqg62a-uc.a.run.app/health`
3. the public repository at the exact `main` commit
4. the release-bound architecture diagram

The direct `*.run.app/health` tab is the preferred visual Google Cloud proof. It
shows the Cloud Run hostname and the same release SHA/build as the Firebase
judge URL without exposing the signed Cloud Console.

## 0:00–0:11 — Personal friction and product

**Screen:** Deployed Decision Room URL and pinned onboarding decision.

**Narration:** “I kept making roadmap calls whose evidence changed after the
commitment. Driftline catches that drift, compares the safest responses, and
keeps the measured outcome attached to the original call.”

## 0:11–0:27 — Evidence with provenance

**Screen:** Start the workflow; show the five signals and BigQuery aggregate.

**Narration:** “Without a prompt loop, Driftline attaches five cited signals,
including a privacy-thresholded BigQuery aggregate. The claims keep their source
and customer segment, so contradictory evidence stays inspectable.”

## 0:27–0:53 — Independent Google ADK council

**Screen:** Show customer, usage, strategy, feasibility, and challenger agents;
pause on dissent and synthesis.

**Narration:** “Five independent Google ADK agents inspect bounded projections.
They cannot approve or write anywhere. Gemini preserves citations and
disagreement instead of averaging it away. Here the council rejects a universal
rollout.”

## 0:53–1:09 — Decision alternatives

**Screen:** Compare ship, rollback, segment, and defer.

**Narration:** “Shipping protects momentum but risks enterprise conversion.
Rolling back loses small-team gains. Deferring misses the window. Segmentation
preserves upside while containing the observed failure mode.”

## 1:09–1:32 — Human authority and bounded action

**Screen:** Show disabled approval, enter the reviewer, approve once, and reveal
the receipt.

**Narration:** “The model recommends; a named human authorizes. Approval freezes
one falsifiable experiment and creates a bounded internal allocation in
Driftline's own decision state. The receipt states external writes: none.”

## 1:32–2:10 — Continuous autonomous outcome

**Screen:** Stop clicking. Keep the monitor visible through guardrail breach,
rollback, learning receipt, and generation-2 reopen. Show the cleared approver
and preserved generation-1 lineage.

**Narration:** “One approval starts the monitor; there is no second prompt or PM
action. The measurement is evaluated against the thresholds committed at
approval. When the enterprise guardrail breaks, Driftline rolls the allocation
back, writes a learning receipt, and reopens generation two. Evidence, dissent,
approval, result, and council remain linked. A fresh human approval is required.”

## 2:10–2:36 — Architecture and deterministic boundaries

**Screen:** Switch to the release-bound architecture and ten-check evaluation.

**Narration:** “Firebase Hosting rewrites to Cloud Run. Firestore stores cases
and lineage. Google ADK and Gemini power the council. BigQuery supplies bounded
aggregates and precedent memory. Cloud Tasks runs the outcome loop. Ten
deterministic checks cover provenance, independence, citations, falsifiability,
human authority, debt lineage, the full operating loop, and calibrated memory.”

## 2:36–2:52 — Visible Google Cloud and release proof

**Screen:** Switch to the direct `*.run.app/health` tab, then the exact public
repository commit. Keep the Cloud Run hostname, release SHA, and build visible.

**Narration:** “This is the live Cloud Run backend. Its health response matches
the serving release and public main. The repository, build, architecture, and
working screen can be compared instead of trusting a claim.”

## 2:52–2:58 — Close

**Screen:** Return to the Decision Room receipt with product name and URL.

**Narration:** “Driftline turns product judgment into an auditable learning
loop: evidence, dissent, decision, outcome.”

## Recording gates

- Current verified production is public-main history commit
  `03ec8f12fc23d265c89b462a345a5b599a6411e8`, Cloud Run revision
  `driftline-00305-xln`, and Cloud Build
  `c01bec2e-a950-407c-873b-b1d4fdc6bae6`. This is the pre-candidate release,
  not the identity to narrate for candidate-only action behavior.
- Replace those values only after the candidate is released. Reject the take unless public `main`,
  Firebase `/health`, direct Cloud Run `/health`, Cloud Run
  revision, Cloud Build, and image digest resolve to the exact same candidate.
- `./scripts/release_and_verify.sh` passes and refreshes the release-bound live
  trace before recording.
- The browser source visibly shows `google_adk` and `gemini-3.5-flash`; otherwise
  narrate the bounded fallback honestly.
- BigQuery is provisioned and the production workflow identifies the aggregate
  source before narration claims it.
- No invented PM, customer, ROI, retention, revenue, or willingness-to-pay
  result appears.
- The action receipt visibly states **External writes: none** and is called an
  internal decision-state allocation.
- The take is one continuous recording. No cut occurs anywhere, especially from
  approval through outcome and reopen.
- The first visible agent action occurs within 15 seconds, and the final
  manifest records its timestamp plus affirmative continuous-take and
  setup/loading-omitted gates.
- The final manifest records `google_cloud_proof_type=cloud_run_url` and the
  exact timestamp at which the `*.run.app` backend becomes visible.
- The public YouTube/Vimeo result is under four minutes, English or English-
  subtitled, and passes `scripts/verify_final_demo_package.sh`.
- Submission copy preserves Google ADK, the August 18 implementation start, and
  the pre-existing ideation/source-package disclosure.
