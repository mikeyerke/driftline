# Driftline judge scorecard

Fresh official-source audit: August 26, 2026. The Devpost website and official
rules prevail over this working scorecard.

## Verified final live release

- Serving application Git SHA: `03ec8f12fc23d265c89b462a345a5b599a6411e8`
- Cloud Run revision: `driftline-00305-xln`, 100% traffic
- Cloud Build: `c01bec2e-a950-407c-873b-b1d4fdc6bae6`
- Image digest:
  `sha256:fca505ce56c6bd933f9cde8d55ff1e4ea7f9cad099d6fe39e8bb8321c96ea6d3`
- Public URL: https://driftline-ops.web.app/
- PR #16: merged into public `main`
- GitHub Actions `32923233214`: backend, frontend, standalone image, and
  repository hygiene passed
- Local: full backend suite, Ruff, frontend build/contract, dependency audit,
  shell/diff hygiene, and 14/14 trace evaluation passed

`/health`, Cloud Run, Artifact Registry, the application commit preserved in
GitHub `main` history, and the production verifier all resolved to the identity
above on August 25. Later `main` commits contain unreleased runtime and
submission improvements; they are not production until exact-SHA release proof
passes again.

## Public-main release candidate, not production

Public `main` now contains the continuous PM operating loop via PR #23, the
redacted multi-source evidence pack via PR #24, the strengthened final-demo
proof pipeline via PR #25, truthful judge-evidence custody via PR #26, and the
fail-closed release-packet chain via PRs #27-#29. Hosted GitHub Actions passed
all four jobs for every PR. Each PR #26-#29 tested tree was identical to its
squash-merged `main` tree. PR #32 then added research-backed real-PM market-fit
evidence and the manual exact-SHA CI recovery path; its combined exact tree
passed all four hosted jobs, equaled its squash-merged `main` tree, and passed a
fresh clean release preflight at `e4a2f474002c151ab29b08528915292543afd7f2`.
PR #33 then refreshed the mirrored judge evidence; its exact head passed all
four hosted jobs, its squash-merged tree was identical, and a new clean
release-candidate preflight plus hosted run `32986603518` passed at public-main
SHA `484e764760c06350733189246a17dfa651502891`.
PR #34 made the two autonomous Taskmaster tasks and the deliberate human
authority boundary explicit in the final-take contract. PR #35 put that proof
chain in the README's first viewport. PR #36 eliminated manual release-to-video
identity transcription with an atomic verified release receipt and derived
manifest seed. The exact PR #36 tested tree equaled its squash-merged tree;
fresh public-main preflight passed 532 backend tests and 14/14 evaluations at
`dfdbe2b22579135b9ebedab71ee2bfbe38fc897b`, and hosted run `32988583543`
passed all four jobs.
None of these merged changes is part of the live score above until Cloud Run
serves the same public-main commit and the full production journey is
reverified.

Release preparation is now one fail-closed evidence chain rather than a set of
manually coordinated files. It binds the exact repository, deployed and
`/health` identities to the actual final MP4 and SRT; reruns the complete media
package verifier; checks three gallery images and their proof video came from
the same browser session; renders a timestamped four-panel review sheet; and
then renders the story, form copy, architecture, gallery, captions, video, and
identity ledger outside the repository. A missing, stale, mismatched, or
rehearsal-marked input produces no release packet. These are verified release
controls, not evidence that the current public deployment or a public video has
changed.

The authorized release command also emits an atomic identity receipt only after
the production verifier proves public main, `/health`, Cloud Run revision,
Cloud Build, image digest, and the release-bound trace agree. It generates the
final-demo manifest seed from that receipt outside the repository and refuses
manual overwrite, preventing release identity from being copied between tools
by hand. This control is implemented and tested; no new release was performed.

Together, these public-main changes add these
judge-facing improvements:

- an autonomous Decision Debt Radar turns contradictory signals into a cited
  inbox item before the PM asks a question, carries that item through open,
  monitoring, resolved, or reopened states, and preserves prior debt cycles as
  compounding decision memory; and
- custom decisions require a PM-authored measurement contract instead of
  placeholder success and stop language; and
- named approval creates a bounded internal allocation record that is active,
  completed, or automatically rolled back within the same decision lineage; and
- a real PM can attach the primary and risk aggregates after the review window,
  with both retained as unverified and evaluated as a two-metric contract; and
- an opaque return link restores the same non-confidential approved case in a
  fresh browser session as a read-only view. A separate HttpOnly, case-specific
  capability in the originating browser is required for approval or follow-up
  measurement; and
- the signed ADK workflow-state tool and all post-turn persistence are bound to
  the exact current workflow and tenant, closing a cross-tenant read/write seam;
- the real-decision intake reveals decision context and the operating contract
  as two progressive steps instead of presenting sixteen required fields at
  once, without weakening any required threshold. Opening the intake and moving
  between steps now bring the active form into view and focus its heading,
  including reduced-motion-safe behavior; and
- the same intake can preserve up to four additional redacted research,
  support, analytics, or product-surface observations as separate cited nodes,
  including its observed date and whether each supports or contradicts the
  commitment. User-entered source labels can never upgrade those observations
  to connected evidence; and
- PM measurements fail closed until the committed review timestamp. Before
  then, the UI shows the exact opening time and the API returns 409 without
  changing the active action, outcomes, or decision generation; and
- a clean checkout now routes the Vite judge UI to the local FastAPI service
  without undocumented frontend configuration. Offline and unreachable-service
  failures state that nothing changed and give a concrete retry path instead of
  exposing raw browser or HTTP errors; and
- the public judge lane now identifies itself as an intentional no-sign-in demo
  instead of presenting disabled operator authentication as a product failure.

The real-PM pilot now also records the participant's primary decision pain,
incumbent workflow, largest adoption blocker, and stated willingness to reuse.
Those bounded fields are analyzed separately from observed costly commitments;
a favorable self-report can never create a customer claim, and unregistered
free text is rejected to prevent identity or raw-data leakage. This improves the
quality of a future independent session but is not itself PM validation.

The public-main candidate now projects all seven PM operating capabilities through one
validated interface: autonomous inbox, evidence harvest, decision-debt radar,
stakeholder alignment, commitment/execution, outcome autopilot, and compounding
memory. A visible ten-step rail advances only when the corresponding durable
state exists; replayable, connected, PM-provided, and precedent sources retain
different labels. Stakeholder positions are explicitly evidence-bound decision
lenses rather than fabricated human quotes.

The UI discloses **scope: decision state only** and **external writes: none**.
The candidate passed 532 backend tests, Ruff, the production frontend build,
the judge-surface literal contract, desktop end-to-end clicks, and a 390 × 844
rollback/reopen journey. The custom PM path additionally passed two-step
context/contract entry, back-navigation preservation, directional-threshold
rejection, named approval, premature-measurement locking, complete brief copy,
and desktop/mobile Lighthouse snapshots at 100 across accessibility, best
practices, SEO, and agentic browsing with no horizontal overflow. It cannot be
scored as production proof until released and independently reverified against
its serving SHA.

The new Decision Debt lifecycle was separately exercised through real browser
clicks on desktop and at 390 × 844: the cited inbox opened at 88/100, named
approval moved it to monitoring, the measured stop-condition breach rolled back
the bounded action, and generation 2 reopened at 98/100 with one prior debt
cycle preserved. The Decision Twin evaluator now checks debt lineage, operating
loop integrity, and zero-sample memory calibration; the complete local policy
surface passes 10/10.

The clean-checkout browser retest also passed first click, refresh/deep-link
resume, double-click approval idempotency, outcome-triggered generation-2
reopening, offline failure, and same-control recovery after reconnecting. A
fresh unthrottled local performance trace measured 523 ms LCP and 0.00 CLS;
these are lab observations, not production field data.

A later fresh first-impression audit at 1453 × 726 and 390 × 844 confirmed the
intentional **Public demo · no sign-in needed** status, a fully visible primary
CTA, zero horizontal overflow, and no browser console errors. The complete
action/reopen driver then passed again with eight real Chrome mouse clicks,
generation 2, rollback selected, approver cleared, external writes none, and
the bounded action rolled back.

The same fresh browser audit caught a real-decision conversion failure: after
**Use my decision**, the new form began 923 pixels below the desktop viewport
and 1,716 pixels below the mobile viewport, so the click appeared to do nothing.
The candidate now moves the opened intake into view, transfers focus to its
heading, and returns step two to the top of the operating contract. Desktop and
mobile both exposed the first contract field with zero overflow and no console
errors.

The completed custom-decision journey is now repeatable through a loopback-only
browser gate. At desktop and mobile widths it built the PM-authored brief,
used a concise affected-segment title instead of repeating the full question,
retained the unverified evidence label, copied the brief and view-only return link,
recorded named approval, exposed the bounded internal action with decision-state-
only scope and no external writes, preserved the approver and approval timestamp
on the saved receipt, rejected an early measurement with HTTP 409, and restored
the approved case in a truly fresh browser context. Every check
passed with zero console errors and no horizontal overflow.

Full-resolution asset QA is now complete. The exact-release desktop/mobile
captures were corrected from JPEG data with misleading `.png` extensions to
actual PNGs and bound by dimensions and checksums. A fresh production mobile
run shows generation 2, rollback selected, the approver cleared, and 7/7 checks;
the local action-result capture is a separate candidate-only file. See
`../submission/assets/ASSET_REVIEW.md`.

The candidate also fixes a first-impression issue found through a fresh live
browser run: at 1453 × 726 the production workflow CTA started 31 pixels below
the fold. The local CTA is now fully visible at 1453 × 670 and 390 × 844 with
zero horizontal overflow.

## 40% — Innovation and operational utility

### Judge thesis

PMs make consequential decisions from contradictory usage, customer, strategy,
and feasibility evidence. Driftline turns that fragmented judgment into one
inspectable learning loop:

`evidence → dissent → counterfactuals → human experiment → outcome → reopen`

This is stronger than a generic agent demo because the memorable action is not
text generation. The product changes the state of the decision when measured
evidence violates the plan, while preserving why the earlier decision was made.

### Live proof

Case `decision-onboarding-75c4ca50b1faaab179a02b29` proved:

- a provenance-preserving evidence graph with a live
  `bigquery-aggregate-attached` event and minimum cohort 84;
- five distinct cited specialist positions: customer, usage, strategy,
  feasibility, and challenger;
- visible disagreement across `ship`, `segment`, and `defer`;
- four counterfactuals with option-specific metrics, success/stop conditions,
  rollbacks, and owner actions;
- a named-human approval at an actual UTC timestamp;
- a measured guardrail outcome;
- generation-2 reopening with the complete generation-1 approval, experiment
  plan, trigger observation, and reopen reason retained.

### Honest limit

The onboarding case and outcome are bounded demo evidence. No customer time
saved, revenue, retention, willingness-to-pay, or PM adoption result has been
measured. The pre-registered 6–8 participant study remains open.

Current market evidence establishes urgency but not product validation:
Atlassian's 1,000+ respondent 2026 study puts competing priorities,
prioritization, strategy, customer insight, stakeholder alignment, and proving
impact among the leading PM challenges; Product Focus's 677-person survey puts
firefighting first at 58%; and ProductPlan reports that leadership escalations
override more than 60% of prioritization frameworks. This supports Driftline's
decision-contract wedge. It does not show that a PM adopted Driftline or would
pay for it.

A separate single-real-PM evidence gate is ready for the deadline-constrained
`n=1` case: it rejects identity/raw-data fields, weak qualification, placeholder
release identity, fractional count fields, premature outcome claims,
and a customer label without payment or a signed paid commitment. It blocks
publication without consent, confirmed participant independence, complete
citation review, and authority comprehension. Paid-panel incentives are
disclosed as evaluation
spend rather than customer revenue. Twenty-nine focused tests pass. This
improves evidence custody; it does not manufacture a participant.

## 30% — Architectural discipline and tech stack

### Live architecture proof

- Gemini 3.5 Flash runs through Vertex AI and Google ADK.
- Five task-mode specialists plus one synthesis turn have no mutation tools.
  Strict schemas, evidence-only citations, role mandates, and disagreement
  validation fail closed into an honestly labeled deterministic fallback.
- BigQuery reads only allowlisted aggregate metrics and segments. Queries are
  parameterized, sample-weighted, dry-run checked, capped at 50 MB billed
  bytes, and reject cohorts below the privacy floor.
- Firestore compare-and-set transitions bind approvals to synthesis hash and
  generation, preserve lineage, and reject stale/conflicting decisions.
- Connector side effects are durably claimed before execution. Any selected
  connector failure requires reconciliation; completed connector results are
  reused so retries do not duplicate confirmed writes.
- Google OIDC-backed audit attribution uses the verified operator email, not an
  independently supplied display name.
- Cloud Run uses min scale zero and max scale one; public council quotas reserve
  all six model slots atomically.

### Security and failure evidence

Codex Security diff scan `80f0982d-2b2e-4efb-b974-d88ec45233ab` reviewed all
14 changed security surfaces. It found two medium integrity issues—unbound OIDC
audit attribution and first-attempt connector false completion. Both were fixed
and regression-tested before the full backend pass.

Codex Security standard scan `2bd6cb67-d0b1-4a2d-88c7-d44267629d63` then
validated a high-severity cross-tenant ADK workflow-state path and a medium
shared-link write-authority issue in the unreleased candidate. Both are now
closed locally with adversarial tests: model-supplied workflow IDs cannot
override the turn binding, and copied decision links cannot mutate cases.
The scan's two medium availability findings are also closed locally: anonymous
mutation traffic now has a signed per-browser allowance plus a higher aggregate
emergency ceiling, and public visual assets use ref-aware single-flight success
caching with bounded failure backoff. The scan's repository coverage was
partial, so this is not a claim of exhaustive security assurance.

`verify_production.sh` independently proved the serving SHA/build/digest,
Firestore, Cloud Tasks, Scheduler, uptime check, alert policy, runtime IAM,
security headers, bounded value windows, and zero current-revision Cloud Run
errors.

The release gate also resolves license evidence across all 82 third-party
Python distributions and 44 Node lock entries, checks every declared direct
dependency is present, and fails on missing evidence or review-required strong-
copyleft/source-available license families. The current locked inventory passed;
this is engineering evidence, not a substitute for the entrant's source-package
ownership attestation.

`scripts/verify_clean_checkout.sh` separately exports only committed `HEAD`
into a new temporary directory, creates a fresh backend environment, installs
the locked frontend tree, and reruns all 532 backend tests, the 14-case agent
evaluation, frontend production build, frontend contract, submission packet,
and shell syntax checks. This closes the gap between “works in the development
worktree” and the reproducibility claim a judge receives from the repository.

The real-decision browser gate now completes named approval by keyboard at
desktop, 390-pixel mobile, and 320-pixel reflow widths. It checks radiogroup
arrow-key behavior, visible skip navigation, accessible names, minimum
standalone target size, landmarks, unique IDs, valid ARIA references, and the
absence of positive tab indexes or focusable hidden content. It also inspects
the browser accessibility tree, proves the evidence dialog makes the
background inert, traps and restores focus, fits each viewport, and verifies
that the journey requests no smooth scrolling under reduced motion. The CSS
contract separately preserves a system-color focus outline in forced-colors
mode. Completed intake and approval transitions move keyboard focus to the new
decision or learning heading instead of dropping it on the document body. The
post-fix browser run reported no findings in these inspected surfaces; a named
VoiceOver or NVDA session remains outside this automated proof.

## 30% — Demo and production readiness

### Production gates

- `verify_decision_twin.sh`: PASS — real `google_adk`, live BigQuery, human
  approval, outcome, complete lineage, generation 2.
- `verify_live_agent.sh`: PASS — job `job-7afefad5be8f`, workflow
  `39c1d422-70e2-4682-bce9-f7ba25d098e6`, two allowlisted tools, four
  artifacts, passing eval `eval-1c74b1b36cb8`.
- `verify_production.sh`: PASS — exact release identity, 100% traffic,
  max-one instance, zero recent errors.
- `verify_trace_eval.sh`: PASS — 14/14, safety/usefulness/overall all 1.0.

### Official video gate

The video must be public on YouTube or Vimeo, under four minutes, English or
English-subtitled, show the working agent, and visibly prove the backend runs on
Google Cloud. Current official FAQ guidance names the Cloud Run console or live
`.run.app` URL as acceptable deployment proof. The judging criterion asks for a
live, unedited proof of action. The canonical 2:58 plan therefore uses one
continuous native recording at 1×, including browser action, tab switches,
direct Cloud Run `/health`, and the release-bound architecture; it permits no
cuts or splices.

The August 24 organizer checklist additionally says to show the project working
within the first 10–15 seconds and omit sign-up, setup, loading, and title-card
waits. The final manifest and package verifier now require a timestamped first
agent action by 0:15 plus affirmative full-take continuity and setup/loading
omission—not merely continuity inside the approval-to-reopen subsection.

Exact-release desktop/mobile screenshots, the Decision Twin architecture, and
a three-minute 1080p captioned local review cut are complete. A continuous
local candidate proof now also runs the actual browser state machine and asserts
the generation-2 rollback outcome. Fresh post-fix desktop and 390-pixel
fallback-mode runs passed with 514 and 563 frames and eight visible Chrome
mouse-input clicks apiece, including deliberate focus of the named-approver
field and the explicit measurement-fallback action; neither required a
duplicate outcome click. The retained 31.17-second clip is silent and
unreleased; a narrated native browser take remains preferable, and no video is
complete for submission until it has a public YouTube or Vimeo URL.

The 3:40 candidate MP4 passed format, loudness, and black-frame checks, but it
uses long static browser holds and combines candidate screens with
pre-candidate release narration. Do not submit it.

A 52-second local continuity rehearsal first proved the visible-click state
machine and custody boundary. The stronger 2:58 long-form rehearsal now keeps
the actual browser workflow first, preserves all seven autonomous-monitor
clicks and the
approval-to-reopen continuity, then closes on the candidate architecture and
release-proof gate. It is watermarked throughout as **UNRELEASED LOCAL
CANDIDATE · NOT PRODUCTION**, has burned and embedded English captions, and
passed 1080p/30fps H.264, stereo AAC, playback pixel-format, duration,
black-frame, silence, and -18 to -14 LUFS checks. Its timestamped rubric map is
in `submission/JUDGE_EVIDENCE_INDEX.md`. It remains ineligible as live proof
until the exact candidate is released and the native browser journey is rerun.
The capture now centers the complete generation-1 action and learning receipt
inside the recorded browser sequence rather than merely asserting it in the
DOM. The August 26 PR #25 candidate-tree presentation run captured 573
state-change frames and seven real mouse-input clicks over 105.867 seconds, with
generation 2, rollback selected, the approver cleared, external writes still
none, and the action visibly rolled back without a second PM action. Its fresh
local 2:58 rebuild additionally frames the ten-stage operating loop and the work
completed before human approval. The rendered package is exactly 178.000
seconds at 1080p/30fps, measures -16.1 LUFS with -4.2 dB true peak, has burned
and embedded English captions, and contains no detected black interval or
four-second silence. Full-resolution review shows named approval at 1:15, the
bounded rolled-back receipt by 1:22, generation 2 by 1:40, and the architecture/
release gate beginning at 2:16. These are local rehearsal QA facts, not
production proof or timestamps to copy into the final release manifest.

## Requirement checklist

| Official requirement | Evidence | Status |
| --- | --- | --- |
| New autonomous agent beyond chat | Async ADK/Cloud workflow plus evidence-to-outcome state change | Proven |
| Gemini 3.5+ | Gemini 3.5 Flash via Vertex AI | Proven live |
| Google framework | Google ADK | Proven live |
| Google Cloud infrastructure | Cloud Run, Firestore, BigQuery, Tasks, Scheduler, Build, Artifact Registry, Storage, Secret Manager | Proven live |
| One category | Taskmaster | Prepared; entrant must select |
| Hosted URL | Public Firebase facade to Cloud Run | Proven live |
| Repository and spin-up instructions | Public repo, README, and committed-only clean-checkout verification | Proven locally for candidate; repeat on public release SHA |
| Architecture diagram | 1600×900 PNG/SVG plus checksum-bound full-resolution review | Prepared; local asset QA complete, entrant upload open |
| Public demo under four minutes | 3:00 review cut, 31.17s continuity proof, and a 2:58 1080p real-click long-form candidate rehearsal with burned and embedded captions | Prepared locally; exact-release final take and public upload remain unproven |
| SDK and start date answers | Google ADK; implementation repo began August 18 | Prepared; entrant must enter |
| Originality/third-party disclosure | Source archive hash, 50-file manifest and timestamps, root commit, public repo, cloud project, first build, and locked dependency licenses | Package contents/timeline proven; entrant must personally attest ownership/rights |
| Optional public build content | Stand-alone 883-word Decision Twin build story with required hackathon-purpose disclosure | Prepared locally; candidate release and form link open |
| Optional social post | Consent-gated drafts only | Intentionally unpublished |
| PM validation | Study kit and fail-closed summarizer | Unproven; no sessions |
| Registration/rules agreement/submission | None performed | Intentionally open |

## Brutal win assessment

- Innovation/utility today: 36/40. The loop is memorable and technically real;
  missing independent PM evidence caps the value claim.
- Architecture today: 29/30. This is the strongest lane: bounded authority,
  cost/privacy controls, crash recovery, exact release provenance, and real
  Google services.
- Demo/readiness today: 26/30 after exact-SHA desktop/mobile browser proof but
  before the final public video; 29/30 is attainable with a fast, legible,
  truthful recording.
- Overall live evidence: roughly 91/100 because production still serves the
  pre-candidate release. The merged and fully checked public-main candidate plus
  the stronger Taskmaster opening, local final-take blueprint, and atomic
  release-to-video custody support roughly 95/100 submission readiness, but
  they are not live proof. An authorized exact release plus strong public final
  video makes 96/100 defensible. Independent PM evidence is the remaining route
  toward 97; optional published contributions can add up to the separate bonus
  ceiling only after explicit authorization.
  Winning remains uncertain because judge
  preference and competing entries are unknowable.

## External winner-pattern benchmark

The August 26 benchmark against the prior Google Cloud ADK winners did not
identify another responsible feature to add. The grand-prize SalesShortcut
entry paired a firsthand business problem with an unmistakable end-to-end
action, explicit multi-agent patterns, a live system, human oversight, and
public build-story bonuses. The North America winner Energy Agent AI paired
deep domain credibility with a live, end-to-end path from evidence to business
action. The EMEA winner Nexora made one technical breakthrough immediately
legible and backed it with visible specialist roles, validation, security, and
a live experience.

Driftline now has the same judge-readable spine: a concrete PM problem, a
visible evidence-to-action-to-outcome loop, specialist disagreement that a
single chat response would hide, deterministic human authority, a public live
experience, and exact-release proof. Its strongest differentiation is not the
number of agents; it is the preserved dissent, falsifiable commitment, bounded
action, measured receipt, and automatic generation-2 reopen.

The benchmark therefore reinforces the existing priority order. A real PM
using a current decision and a fast, continuous final demo add more credibility
than another specialist, connector, dashboard, or speculative workflow. Until
those exist, winner parity on implementation does not equal winner parity on
independent usefulness proof.

Reference projects:

- https://devpost.com/software/salesshortcut
- https://devpost.com/software/energy-agent-ai
- https://devpost.com/software/teachai-upzofa
- https://googlecloudmultiagents.devpost.com/updates/35783-and-the-winners-are

## Ranked remaining work

1. Release and exact-SHA re-prove the bounded internal-action candidate, but
   only after explicit publication authorization.
2. Run the [real-PM customer sprint](../docs/REAL_PM_CUSTOMER_SPRINT.md). One
   qualified session can support a bounded independent-PM statement; three
   genuine sessions are materially stronger. Publish only anonymized aggregates
   that pass the pre-registered human-control and data-quality gates.
3. Record the under-four-minute public demo from the verified release. Show the
   working product in the first 10–15 seconds and keep the core proof continuous.
4. Personally confirm ownership/rights for the now-verified source archive and
   accept the live originality/eligibility terms. The content, hash, manifest,
   and contest-period timestamps are already prepared and reproducible.
5. Fill the Devpost form with category, Google SDK, August 18 start date,
   disclosure, repo, hosted URL, architecture, and video.
6. Read and explicitly accept the official rules, register, then separately
   authorize final submission.
7. After submission, freeze the submitted repo/video/links until winners are
   announced. Optional public content/social bonuses require separate approval.

No registration, submission, email, social post, or public bonus content is
authorized by this scorecard.
