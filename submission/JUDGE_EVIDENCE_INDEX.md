# Driftline judge evidence index

Status: local review map, August 26, 2026. It does not authorize release,
upload, registration, submission, or a production claim.

This index maps the strongest 2:58 candidate rehearsal to the official scoring
story. The rehearsal is permanently marked **UNRELEASED LOCAL CANDIDATE · NOT
PRODUCTION**. Its timestamps are an edit contract for the final exact-release
take, not evidence that the candidate is already live.

Post-rehearsal improvement: the current local candidate now opens the workflow
with a cited **Autonomous decision inbox** showing the affected commitment,
decision-debt score, missing evidence, and next bounded decision. Approval moves
that debt into monitoring; the demonstrated guardrail breach reopens it at a
higher score while preserving the prior debt cycle. This was real-click verified
on desktop and at 390 × 844, but it is not present in the 2:58 rehearsal and must
be captured in the exact-release final take before judges can score it.

## First-pass timeline

| Time | Visible proof | Judge question answered |
| --- | --- | --- |
| 0:00–0:11 | Final-take target: autonomous decision-inbox item and one contested roadmap commitment | What concrete PM problem is this solving, and why does it need attention now? |
| 0:11–0:27 | Five source-bound signals, including the privacy-thresholded BigQuery aggregate | Is the agent reasoning over evidence rather than a prompt-only toy? |
| 0:27–0:42 | Five independent Google ADK specialist positions | Is this actually an agent system, and are roles distinct? |
| 0:42–0:53 | Gemini synthesis retains citations and visible dissent | Does synthesis preserve disagreement rather than erase it? |
| 0:53–1:09 | Ship, rollback, segment, and defer with different tradeoffs | Is the output decision-useful rather than generic prose? |
| 1:09–1:22 | Disabled approval becomes a named-human authorization | Who has authority to act? |
| 1:22–1:32 | Bounded allocation receipt: decision state only; external writes none | What changed, and what did not? |
| 1:32–1:45 | Monitor begins after one approval, with no second PM prompt | Why does this qualify for Taskmaster? |
| 1:45–1:58 | Guardrail breach rolls back the allocation and opens generation 2 | Does the system autonomously complete a meaningful multistep task? |
| 1:58–2:10 | Prior evidence, dissent, approval, result, and lineage remain linked; approver is cleared | Is the autonomous loop inspectable and human-gated again? |
| 2:10–2:23 | Architecture: Firebase Hosting, Cloud Run, Firestore, Google ADK, Gemini, BigQuery, Cloud Tasks | Is the backend genuinely implemented on Google technology? |
| 2:23–2:36 | Seven deterministic policy checks | Are safety and correctness architectural rather than prompt promises? |
| 2:36–2:43 | Candidate custody warning and exact-release gate | Is the demo honest about what is and is not deployed? |
| 2:43–2:52 | Rehearsal release gate; final take must replace it with Cloud Run console or live `.run.app` backend plus health/build identity | Can a judge independently verify Google Cloud deployment? |
| 2:52–2:58 | Product name and public URL | Can the judge immediately continue testing? |

## Rubric map

### Innovation and operational utility — 40%

The video proves the uncommon product loop rather than claiming novelty:
contradictory evidence becomes competing reversible options; a named human
chooses; the system monitors the precommitted guardrail; a breach reverses the
bounded action and reopens the original decision with lineage intact. Strongest
window: **0:42–2:10**.

Not demonstrated by the video: independent PM adoption, customer ROI, revenue,
retention, willingness to pay, or a real customer. Those remain unmeasured and
must not be inferred from the workflow.

### Architectural discipline and Google stack — 30%

The visible architecture and captions identify Firebase Hosting, Cloud Run,
Firestore, Google ADK, Gemini, BigQuery, and Cloud Tasks. The browser workflow
shows that model recommendation and human authority are different states, and
that the autonomous monitor is constrained by deterministic checks. Strongest
window: **1:09–2:36**.

The final take must additionally show either the Cloud Run console or the live
`.run.app` backend URL, plus `/health`, the serving commit, Cloud Run revision,
Cloud Build ID, image digest, and public `main` equality. A diagram or caption
alone is supporting explanation, not deployment proof.

Read-only preflight on August 26 confirmed that both the Firebase facade and
`https://driftline-xvxczqg62a-uc.a.run.app/health` returned status `ok`, service
`driftline-agent`, Firestore persistence, asynchronous jobs enabled, release
`03ec8f12fc23d265c89b462a345a5b599a6411e8`, and build
`c01bec2e-a950-407c-873b-b1d4fdc6bae6`. That proves the current release has a
safe direct Cloud Run proof tab; it does not pre-prove the unreleased candidate.

### Demo and production readiness — 30%

The core approval-to-reopen path remains continuous, all seven interactions in
the autonomous-monitor presentation are real browser mouse inputs, the
approver clears on generation 2, and the closing verification frame gives the
judge a route to reproduce the result. The local fallback variant adds an
eighth browser click for **Run demo measurement fallback**; that extra click is
not part of the autonomous-monitor presentation. Strongest window:
**0:00–2:58**.

The August 26 current-HEAD autonomous local rehearsal at `a0b52f8` captured 536
state-change frames and seven real mouse-input clicks, with the bounded local
background monitor completing the outcome without a second PM action. A
separate fallback-mode run passed with 612 frames and eight clicks. Neither is
evidence of hosted Cloud Tasks execution. The labeled full-resolution audit shows the
named human at 1:08, the bounded and rolled-back action receipt at 1:15,
generation 2 with rollback selected at 1:30, and the candidate
architecture/Cloud-proof section at 2:15. This is local rehearsal evidence,
not production or upload proof.

The final package is unproven until it is captured against the exact serving
release, passes `scripts/verify_final_demo_package.sh`, receives entrant review,
and is uploaded to a public YouTube or Vimeo URL. The local rehearsal must
never be renamed or substituted for that package. The older three-minute review
cut is also ineligible: the strict package gate detects a 4.53-second narration
silence and its static sequence is weaker than the real-click blueprint.

## Final-take rejection conditions

Reject the take if any of these is true:

- the first visible agent action occurs after 0:15, or setup/loading/title-card
  waiting consumes the opening;
- the complete native take is not continuous, even if the approval-to-reopen
  subsection happens to be continuous;
- the browser sequence is not from the release identified by `/health`;
- public `main`, `/health`, and the manifest release SHA differ;
- the approval-to-reopen core is spliced or requires a hidden second action;
- the named-human approval is not visibly completed, even if narration or
  captions say it happened;
- the bounded action receipt is not visibly shown after that approval;
- generation 2 is shown without a cleared approver and visible generation-1
  lineage, making it indistinguishable from a reset or edited state;
- candidate-only behavior is described as live before release verification;
- a rehearsal custody watermark remains, even if the file was renamed;
- the video bytes match any known quarantined rehearsal or historical proof,
  even if the asset was copied under another filename;
- **External writes: none** is absent from the public-lane action proof;
- the architecture appears without observable product action;
- neither the Cloud Run console nor the live `.run.app` backend is visible;
- captions overlap, omit a critical Google/authority claim, or become unreadable
  at 720p;
- any secret, private customer record, tenant identifier, or editable credential
  appears; or
- the video is 3:56 or longer.
