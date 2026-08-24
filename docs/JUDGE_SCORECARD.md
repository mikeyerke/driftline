# Driftline judge scorecard

Fresh official-source audit: August 24, 2026. The Devpost website and official
rules prevail over this working scorecard.

## Verified baseline live release

- Git SHA: `1b8a8bfbcf2249136dbf08de54c0f7ee15f575d6`
- Cloud Run revision: `driftline-00291-v89`, 100% traffic
- Cloud Build: `154547e7-36ae-4eb2-a79a-35064e293191`
- Image digest:
  `sha256:18d8e1f76dd3c2a305f6e76aacbbc75fe876a2028f6881e371f9d3b21e34d450`
- Public URL: https://driftline-ops.web.app/
- PR #16: open and unmerged
- GitHub Actions `32757068133`: backend, frontend, standalone image, and
  repository hygiene passed
- Local: 386 backend tests, Ruff, frontend build/contract, dependency audit,
  shell/diff hygiene, and 14/14 trace evaluation passed

Final submission metadata must use `/health` and
`./scripts/verify_production.sh` to capture the exact final candidate identity;
the values above are the last historical baseline, not a floating claim.

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

Case `decision-onboarding-ca91c815d6629f4d5ff5acbd` proved:

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
and regression-tested before the 386-test full pass.

`verify_production.sh` independently proved the serving SHA/build/digest,
Firestore, Cloud Tasks, Scheduler, uptime check, alert policy, runtime IAM,
security headers, bounded value windows, and zero current-revision Cloud Run
errors.

## 30% — Demo and production readiness

### Production gates

- `verify_decision_twin.sh`: PASS — real `google_adk`, live BigQuery, human
  approval, outcome, complete lineage, generation 2.
- `verify_live_agent.sh`: PASS — job `job-e253f458c786`, workflow
  `6a507a68-0a14-498e-a368-332ff5aef4ff`, two allowlisted tools, four
  artifacts, passing eval `eval-b00a339dfd10`.
- `verify_public_approval_undo.sh`: PASS — job `job-0f7c269392a3`, workflow
  `ef53b1b0-8483-4114-acde-4424bf2c1ce7`, owner action completed then
  reversed, no external system changed.
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

The final video, screenshots, and rendered Devpost form are not complete and
must not be claimed as complete.

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
| Public demo under four minutes | Script/runbook/captions | Unproven until recorded and uploaded |
| SDK and start date answers | Google ADK; implementation repo began August 18 | Prepared; entrant must enter |
| Originality/third-party disclosure | Earlier ideation/source package and dependencies disclosed | Prepared; entrant must confirm |
| PM validation | Study kit and fail-closed summarizer | Unproven; no sessions |
| Registration/rules agreement/submission | None performed | Intentionally open |

## Brutal win assessment

- Innovation/utility today: 34/40. The loop is memorable and technically real;
  missing independent PM evidence caps the value claim.
- Architecture today: 29/30. This is the strongest lane: bounded authority,
  cost/privacy controls, crash recovery, exact release provenance, and real
  Google services.
- Demo/readiness today: 23/30 before the final video and screenshots; 28–30 is
  attainable with a fast, legible, truthful recording.
- Overall current evidence: roughly 86/100. With a strong final video and honest
  PM validation, 93–97 is defensible. Winning remains uncertain because judge
  preference and competing entries are unknowable.

## Ranked remaining work

1. Run 6–8 genuine PM sessions; publish only anonymized aggregates that pass the
   pre-registered human-control and data-quality gates.
2. Record the under-four-minute public demo from this verified release. Show the
   working product in the first 10–15 seconds and keep the core proof continuous.
3. Capture final screenshots and confirm architecture/text remain legible.
4. Fill the Devpost form with category, Google SDK, August 18 start date,
   disclosure, repo, hosted URL, architecture, and video.
5. Read and explicitly accept the official rules, register, then separately
   authorize final submission.
6. After submission, freeze the submitted repo/video/links until winners are
   announced. Optional public content/social bonuses require separate approval.

No registration, submission, email, social post, or public bonus content is
authorized by this scorecard.
