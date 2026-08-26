# Driftline judge scorecard

Fresh official-source audit: August 25, 2026. The Devpost website and official
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
above on August 25. Later `main` commits update submission media only.

## Unreleased local candidate

The isolated candidate is not part of the live score above. It adds four
judge-facing improvements:

- custom decisions require a PM-authored measurement contract instead of
  placeholder success and stop language; and
- named approval creates a bounded internal allocation record that is active,
  completed, or automatically rolled back within the same decision lineage; and
- a real PM can attach the primary and risk aggregates after the review window,
  with both retained as unverified and evaluated as a two-metric contract; and
- an opaque return link restores the same non-confidential approved case in a
  fresh browser session for that follow-up measurement.

The UI discloses **scope: decision state only** and **external writes: none**.
The candidate passed the complete backend suite, Ruff, the production frontend build,
the judge-surface literal contract, desktop end-to-end clicks, and a 390 × 844
rollback/reopen journey. It cannot be scored as production proof until released
and independently reverified against its serving SHA.

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

`verify_production.sh` independently proved the serving SHA/build/digest,
Firestore, Cloud Tasks, Scheduler, uptime check, alert policy, runtime IAM,
security headers, bounded value windows, and zero current-revision Cloud Run
errors.

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
Google Cloud. The August 24 organizer checklist recommends trimming load time
and using jump cuts; the judging criterion asks for a live, unedited proof of
action. Safest execution: edit intros/waits, but keep one continuous visible
council → approval → outcome → reopen sequence tied to the same case.

Exact-release desktop/mobile screenshots, the Decision Twin architecture, and
a three-minute 1080p captioned local review cut are complete. A continuous
local candidate proof now also runs the actual browser state machine and asserts
the generation-2 rollback outcome. It is silent, cursor-free, and unreleased;
a narrated native browser take remains preferable, and no video is complete for
submission until it has a public YouTube or Vimeo URL.

The 3:40 candidate MP4 passed format, loudness, and black-frame checks, but it
uses long static browser holds. Treat it as an emergency fallback, not as the
rubric's strongest proof of a working agent.

## Requirement checklist

| Official requirement | Evidence | Status |
| --- | --- | --- |
| New autonomous agent beyond chat | Async ADK/Cloud workflow plus evidence-to-outcome state change | Proven |
| Gemini 3.5+ | Gemini 3.5 Flash via Vertex AI | Proven live |
| Google framework | Google ADK | Proven live |
| Google Cloud infrastructure | Cloud Run, Firestore, BigQuery, Tasks, Scheduler, Build, Artifact Registry, Storage, Secret Manager | Proven live |
| One category | Taskmaster | Prepared; entrant must select |
| Hosted URL | Public Firebase facade to Cloud Run | Proven live |
| Repository and spin-up instructions | Public repo and README | Proven |
| Architecture diagram | Submission PNG/SVG assets | Prepared; final upload QA open |
| Public demo under four minutes | 3:00 1080p review cut, 16.47s continuous candidate proof, script, captions, and native-take runbook | Prepared locally; unproven until publicly uploaded |
| SDK and start date answers | Google ADK; implementation repo began August 18 | Prepared; entrant must enter |
| Originality/third-party disclosure | Earlier ideation/source package and dependencies disclosed | Prepared; entrant must confirm |
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
- Overall current evidence: roughly 91/100. With a strong final video, 94/100 is
  defensible. If the local action candidate is released and re-proven, roughly
  95/100 is defensible because Taskmaster action becomes explicit without a
  false external-write claim. Independent PM evidence is the remaining route
  toward 96–97.
  Winning remains uncertain because judge
  preference and competing entries are unknowable.

## Ranked remaining work

1. Release and exact-SHA re-prove the bounded internal-action candidate, but
   only after explicit publication authorization.
2. Run at least three genuine PM sessions; six to eight is stronger. Publish
   only anonymized aggregates that pass the pre-registered human-control and
   data-quality gates.
3. Record the under-four-minute public demo from the verified release. Show the
   working product in the first 10–15 seconds and keep the core proof continuous.
4. Approve the captured desktop/mobile screenshots and architecture asset.
5. Fill the Devpost form with category, Google SDK, August 18 start date,
   disclosure, repo, hosted URL, architecture, and video.
6. Read and explicitly accept the official rules, register, then separately
   authorize final submission.
7. After submission, freeze the submitted repo/video/links until winners are
   announced. Optional public content/social bonuses require separate approval.

No registration, submission, email, social post, or public bonus content is
authorized by this scorecard.
