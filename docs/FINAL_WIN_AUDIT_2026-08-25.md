# Driftline final win audit — August 25, 2026

This is a release-candidate audit against the official All Things Agentic
Hackathon Stage Two rubric. The live rules and submission form prevail over
this document. Source of truth: the [official rules](https://allthingsagentichackathon.devpost.com/rules)
and [official FAQ](https://allthingsagentichackathon.devpost.com/details/faqs).

## Executive verdict

Driftline is a serious **Taskmaster** and **Best Architectural Design**
contender. It has a more complete learning loop, stronger safety boundaries,
and better release evidence than most hackathon demos. It is not yet a safe
bet for the Grand Prize because the strongest path is still a pinned public
case, no genuine PM validation is recorded, the final video is not uploaded,
and Devpost registration/submission are unfinished.

| Score | Current verified production | Defensible target after remaining gates |
| --- | ---: | ---: |
| Innovation & Operational Utility | 36/40 | 38/40 |
| Architectural Discipline & Tech Stack | 29/30 | 30/30 |
| Demo & Production Readiness | 26/30 | 29/30 |
| **Total** | **91/100** | **97/100** |

The current product can place. A strong public video supports roughly 94/100.
Releasing and re-proving the local bounded-action candidate can support roughly
95/100. The 96–97 range additionally requires genuine independent PM evidence,
not more screens or stronger adjectives. A guaranteed 100 is not an honest
forecast because judges award subjective 1–5 criterion scores.

## 1. Innovation & Operational Utility — 40%

### What judges can verify

- One contested product commitment moves through evidence detection, five
  independent Google ADK positions, visible dissent, four counterfactuals,
  named-human approval, a falsifiable experiment, a measured outcome, and a
  generation-2 reopen.
- The system produces PM-ready artifacts: a decision brief, cited evidence,
  explicit guardrail, rollback path, owner actions, and learning receipt.
- The live BigQuery projection is aggregate-only and privacy-thresholded.
- Agents perform bounded analysis before the human approval gate; they do not
  merely rewrite a prompt.

### What holds the score below 40

- The public Decision Twin uses one pinned, redacted onboarding case. This is
  excellent demo control but weak evidence of general PM utility.
- The serving public path prepares owner work rather than executing a real
  downstream product-system mutation. The unreleased candidate now executes a
  reversible internal allocation tied to the approval and automatically rolls
  it back on invalidation, while explicitly disclosing that it performs no
  external write. It also accepts a real PM's primary and risk aggregates after
  the review window, retains them as unverified, and requires both success and
  safety before completing the action. This improves Taskmaster legibility and
  closes the custom-decision learning loop. An opaque, explicitly non-secret
  return link restores that same case for the later measurement. None of this is
  live proof yet.
- No genuine PM interviews, time saved, decision-quality comparison, adoption,
  or willingness-to-pay evidence exists. Never imply otherwise.
- The full council recommendation is still model prose; the UI must foreground
  what was autonomously completed and what changed the decision.

### Winning polish

1. Keep the new “completed before human approval” proof immediately beneath
   the recommendation: cited signals, independent agents, competing responses,
   and the reversible plan.
2. In the video, say “without a prompt loop” and show the autonomous proof
   before opening technical detail.
3. Run at least three short PM validation sessions before submission. Record
   only observed task comprehension, time-to-decision, and usefulness; do not
   invent ROI. Six to eight sessions would materially strengthen the claim.
4. Release and re-prove the completed bounded internal-allocation candidate only
   after the demo narrative, mobile state, and exact-SHA release gates agree.

## 2. Architectural Discipline & Tech Stack — 30%

### What judges can verify

- Google ADK agents are role-isolated and tool-free; synthesis is a separate,
  bounded turn.
- Gemini 3.5 Flash returns schema-constrained outputs and cited evidence IDs.
- Cloud Run, Firestore, BigQuery, Cloud Tasks, Scheduler, Build, Artifact
  Registry, Storage, Secret Manager, and Monitoring have distinct roles.
- State transitions use generation and synthesis-hash compare-and-set checks.
- Evidence manifests, approvals, outcomes, and prior generations remain linked.
- Anonymous and signed tenant lanes are separate. External writes require a
  signed operator; credentials remain tenant-bound and least-privilege.
- The model can recommend, but deterministic policy checks and a named human
  retain authority.

### What holds the score below 30

- The architecture is sophisticated enough that a four-minute demo can feel
  like infrastructure theater unless every service is tied to one user value.
- Release telemetry is append-only and the canonical verifier now refreshes the
  live trace before checking the serving release.
- The repository contains extensive historical evidence that can obscure the
  canonical current-release path.

### Winning polish

1. Use `scripts/release_and_verify.sh` for the final candidate. It deploys one
   clean SHA, refreshes the live ADK evaluation, verifies Decision Twin, then
   runs the production gate. The judge disclosure must show a release-bound
   verified trace before recording.
2. In the architecture diagram and narration, use one sentence per boundary:
   “ADK reasons; deterministic policy gates; a human authorizes; Firestore
   preserves lineage; BigQuery supplies bounded aggregates.”
3. Freeze one canonical SHA and stop proof-only redeploys after the recording.
4. Keep the architecture diagram readable at 1080p and show the serving SHA,
   Cloud Run revision/build, ADK model, trace checks, and BigQuery source.

### Failure-tolerance proof judges should hear

- Each role is isolated, schema constrained, and allowed to cite only supplied
  evidence IDs.
- Invalid identity, unknown citations, malformed structured output, lost
  disagreement, or unavailable live output fails closed into an honestly
  labeled deterministic demo fallback.
- Approval uses generation and synthesis-hash compare-and-set checks; a stale
  or conflicting actor cannot silently overwrite the active decision.

## 3. Demo & Production Readiness — 30%

### What judges can verify

- The public URL works without sign-in and reaches the core value quickly.
- The complete journey passes live: council mode `google_adk`, BigQuery evidence,
  human approval, reversible experiment, measured outcome, and generation-2
  reopen.
- Cloud Build deploys immutable, clean commits and the health endpoint exposes
  release identity.
- Tests cover backend policy/state logic, frontend contracts, trace evaluation,
  dependencies, and production smoke checks.
- The UI labels fixtures and separates judge telemetry from customer ROI.

### What holds the score below 30

- No final public YouTube/Vimeo video has been uploaded and checked under the
  four-minute limit.
- The entrant is not registered for this hackathon in Devpost and the project
  has not been submitted.
- Final release screenshots and captions must be regenerated from the exact
  serving SHA after the last deploy.
- Any future candidate must refresh and verify the release-bound trace before
  recording; local passing tests are not a substitute for that proof.
- In a fresh 1453 × 726 Chrome viewport, the live primary workflow CTA began
  31 pixels below the fold. The unreleased candidate moves both workflow
  actions directly beneath the value proposition and keeps the primary CTA
  fully visible on desktop and at 390 × 844. This is not live proof yet.

### Winning polish

1. Record the 3:48 script with the council → approval → outcome → reopen path
   continuous. Cut setup/loading only.
2. Show the product in the first 10 seconds, the autonomous proof by 0:30, the
   generation-2 reopen by 3:05, and exact Google Cloud/release proof at the end.
3. Upload an unlisted/public English-captioned video, then watch it once at
   1080p with sound off and once on a phone.
4. Register on Devpost, select Taskmaster, complete every required field,
   attach the architecture image, and submit only after the entrant personally
   accepts the rules.
5. Freeze repo, hosted build, video, and linked evidence after the deadline.

## Stage One and optional score gates

The weighted score is irrelevant if the submission fails Stage One. Before the
deadline, verify the hosted URL, English write-up, repository and spin-up guide,
architecture diagram, public YouTube/Vimeo video, category selection, required
Gemini/agent-framework/Google Cloud disclosures, and all entrant eligibility
fields.

After the candidate is frozen, capture the low-risk optional points:

1. Publish one concise build article using the required statement that it was
   created for the purpose of entering the hackathon. Reuse the architecture
   and failure-tolerance story; do not invent customer outcomes.
2. Publish one accurate LinkedIn or X post with `#AllThingsAgenticHackathon` and
   link the live demo/video. The rules list a maximum 0.2-point social bonus.
3. Do **not** bolt on Gemma, Veo, or Lyria unless the integration materially
   improves the core journey and can be demonstrated. A fragile bonus model is
   more likely to reduce the main 30% production-readiness score than help it.

## Verification evidence for this audit

- Frontend production build: pass.
- Frontend judge-surface contract: pass.
- Backend Ruff gate: pass.
- Backend tests: 432 passed, 2 dependency deprecation warnings.
- Trace evaluation: 14/14 checks, overall 1.0, safety 1.0, usefulness 1.0.
- Frontend production dependency audit: 0 vulnerabilities reported offline.
- Python dependency audit could not be rerun in the restricted audit sandbox;
  the final CI/release environment must run the repository's canonical gate.

## Prize-lane fit

| Prize lane | Fit | Honest assessment |
| --- | --- | --- |
| Grand Prize | Medium-high | Possible if the video makes the learning-loop insight unforgettable and validation is added. |
| Taskmaster | High | Strong multi-step autonomous analysis with durable action preparation and human authority. |
| Best Architectural Design | Very high | Driftline's clearest competitive advantage. |
| Individual/Hobbyist | High if eligible | Strong production depth for a solo/independent build. |
| Best Multimodal UX | Medium-low | One Gemini Vision evidence node is not enough to center this lane. Do not dilute the entry. |

## Live journey audit

| Step | Result | Health |
| --- | --- | --- |
| First viewport | Decision, urgency, and PM utility are immediately legible; the live CTA starts just below one tested desktop fold. Candidate fix is locally verified. | Pass with local fix pending release |
| Council run | Live ADK mode, BigQuery aggregate, five cited perspectives, and real dissent appear. | Pass |
| Option comparison | Four bounded choices expose guardrail, mind-change condition, rollback, and risk. | Pass |
| Human approval | Human authority is explicit and creates a measurable, reversible plan. | Pass |
| Bounded internal action | Local candidate creates, completes, or rolls back a decision-state allocation and discloses external writes as none. | Local only; release proof required |
| Outcome | Pinned aggregate measurement is honestly disclosed. | Pass |
| Generation-2 reopen | Guardrail breach reopens the same case and preserves prior lineage. | Pass |
| Architecture proof | Serving release, release-bound trace, and monitors are healthy for the current immutable production identity. | Pass |
| Browser console | No application-origin errors observed; cloud-browser extension metadata errors are environment noise. | Pass with note |

## Release-blocking checklist

- [ ] Candidate branch is clean and all local gates pass.
- [ ] Final SHA is pushed and CI is green.
- [ ] `scripts/release_and_verify.sh` passes against production.
- [ ] Architecture disclosure says the trace is verified for the serving SHA.
- [ ] Fresh desktop and phone screenshots are captured.
- [ ] Final 3:48 video is uploaded and QA'd.
- [ ] At least three honest PM validation notes are recorded, or all customer
  outcome claims remain “not measured.”
- [ ] Devpost registration, category, form, architecture, disclosure, video,
  and submission are completed by the entrant.

## Bottom line

Do not add another dashboard, connector, or generic AI feature. The winning
story is already here: **new evidence invalidates a product commitment;
independent agents expose the conflict; a human approves the smallest safe
test; reality reopens the decision with the full lineage intact.** Polish and
prove that loop, then stop.
