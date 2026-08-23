# Driftline — when the market moves, the work moves

## Submission links

- Hosted application: https://driftline-xvxczqg62a-uc.a.run.app/
- Public source repository: https://github.com/mikeyerke/driftline
- Architecture diagram: https://github.com/mikeyerke/driftline/blob/main/docs/architecture.md
- Judge scorecard: https://github.com/mikeyerke/driftline/blob/main/docs/JUDGE_SCORECARD.md
- Cloud/resource evidence: https://github.com/mikeyerke/driftline/blob/main/docs/RESOURCE_INVENTORY.md
- Rules and eligibility evidence: https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md
- Trace-to-eval quality gate: https://github.com/mikeyerke/driftline/blob/main/docs/TRACE_EVAL.md
- Demonstration video: held for final owner review; no upload or submission has been made
- Pending-approval frame: [`live-pending-approval-2026-08-20.jpg`](assets/live-pending-approval-2026-08-20.jpg)
- Completed frame: [`live-completed-2026-08-20.jpg`](assets/live-completed-2026-08-20.jpg)

## Latest verified release

### Current exact proof — 2026-08-23

The current serving release is
`747e5b891fc01c6317666527ecfc8049f82be160` on Cloud Run revision
`driftline-00277-mrw`, built by Cloud Build
`a2240b63-2d17-4bea-af38-230e11e34c63` with image digest
`sha256:7d64754a1dd27a98f9e9286102560355dbe9e02695f1a40fafef27617a4fa0d7`.
It serves 100% of traffic in the isolated `driftline-hackathon-2026` project.
GitHub Actions run `32646428785`; the full local gate passed with 328 backend
tests, Ruff, frontend production build, frontend contract checks, and frozen
dependency audit.

Fresh live proof on that exact revision (rerun 2026-08-23):

- ADK/Gemini execution: job `job-4c1020718392`, workflow
  `8cdcdabf-954f-4af9-8d9e-3a0ce5e63731`, `needs_approval`,
  `gemini-3.5-flash`, two allowlisted tools, four artifacts, five audit events,
  two decision options, and trace evaluation `eval-4ef9e9424cac` at 100% /
  stable.
- Approval/undo: job `job-e632996e351d` persisted a packet, completed owner
  action `item-e57eb01b54ac`, and reversed it; `external_write=false` and
  `external_systems_changed=false` remained explicit.
- Production verification passed for Firestore, Cloud Tasks, Scheduler,
  uptime, alerting, IAM, Artifact Registry retention, security headers, OIDC
  tenant boundaries, and zero current-revision Cloud Run errors. The current
  revision's trace-to-eval record is `eval-9190838e7dc9` (stable), and the
  latest Scheduler attempt was `2026-08-23T15:00:33.563833Z`.

This hardening release stops Salesforce context reads from retrying a refresh
token after an explicit `reauthorization_required` marker. The metadata remains
repair-visible while CRM context fails closed; only the explicit operator
aggregate-read probe can establish a verified CRM read. Append-only source
history remains visible after no-op and baseline monitor outcomes, and the
public evaluation lane remains packet-safe with no third-party writes.

The remaining limits are intentional and evidence-gated: Salesforce aggregate
read is not verified (`external_read=false`, `aggregate_read_verified=false`,
no object totals); no real customer pilot has produced before/after time-saved,
revenue, win-rate, retention, or willingness-to-pay evidence; and monitoring is
bounded to five pinned fixtures plus exact operator-registered HTTPS URLs capped
at 25 per tenant, not universal competitor crawling.

### Historical exact proof — 2026-08-23 (superseded)

The serving release is `f28bc6e8bcfbf9651ce47f53dbbe8980e7376781` on Cloud
Run revision `driftline-00276-kwx`, built by Cloud Build
`7575e6f6-acaa-4e9f-ac8a-fba56b1549e9` with image digest
`sha256:3cba623b253abf5a617fbe10fada00c9f0b69b067cdd01ca5eeb8de983b89cc7`.
The revision serves 100% of traffic in the isolated
`driftline-hackathon-2026` project. GitHub Actions run `32645277490` and the
full local gate passed before deployment.

Fresh live proof on that exact revision:

- ADK/Gemini execution: job `job-cd8a7384e26d`, workflow
  `825bb0f1-0abf-467a-adad-57c5337e37ce`, `needs_approval`,
  `gemini-3.5-flash`, two allowlisted tools, four artifacts, five audit events,
  two decision options, and trace evaluation `eval-a253ca2ea043` at 100% / stable.
- Approval/undo: job `job-7792d964a34b` persisted a packet, completed one
  owner action, and reversed it; `external_write=false` and
  `external_systems_changed=false` remained explicit.
- Scheduler: a fresh manual run at `2026-08-23T14:28:49.246321Z` returned HTTP
  200 for `/api/scheduler/tick` on `driftline-00276-kwx`.
- Browser QA: the deployed public console reached the evidence-bound approval
  gate and Gemini Decision Copilot returned two bounded options for four mapped
  surfaces. Source evidence, map selection, artifact detail, and approval copy
  worked. Desktop and 390px mobile browser QA reported the current serving
  SHA/build, zero Driftline console errors, and no horizontal overflow; the
  390px mobile viewport retained the responsive console shell without
  horizontal overflow. The monitor pulse refreshes every minute and the source-history panel refreshes
  after no-op and baseline monitor outcomes.

This release makes bounded agent quotas recoverable: 429 responses carry a
machine-readable retry window and the console explains when the operator can
retry. It also fixes a consequential trust bug: approval/undo packets now
state the actual durable connector outcome and lane (configured connector vs
packet-safe public), and the workflow state is committed even if optional
artifact storage is unavailable. The monitor UI keeps append-only history
visible after a no-op or first baseline instead of leaving the operator with a
stale panel. The public evaluation lane remains packet-safe and writes no
third-party systems.

The following constraints remain explicit rather than inferred: Salesforce
aggregate read is not verified (`external_read=false`,
`aggregate_read_verified=false`, no object totals); signed tenant
`driftline-demo` still requires Salesforce reauthorization because an
independent refresh-token probe returned Salesforce `invalid_grant` / expired
access-refresh token; no real customer pilot has produced before/after
time-saved, revenue, retention, or willingness-to-pay evidence; and monitoring
is intentionally bounded to five pinned fixtures plus exact operator-registered
URLs capped at 25 per tenant, not universal competitor crawling.

The serving release is `c3f16cf3d2765f787cb245f5123dcee4e2c38e73` on Cloud Run
revision `driftline-00271-8vk`, built by Cloud Build
`75d20c28-4620-4633-b896-bba1b2c66822` with image digest
`sha256:205531846adbe53df8e40288504b8e5fe9c647bd56475e9b10eb6fcf421c994d`.
The revision serves 100% of traffic in the isolated
`driftline-hackathon-2026` project. GitHub Actions run `32609226525` and the
full local gate passed before deployment.

Fresh live proof on that exact revision:

- ADK/Gemini execution: job `job-acf236441f56`, workflow
  `61271451-309b-4e1e-acea-61f79f7ea964`, `needs_approval`,
  `gemini-3.5-flash`, two allowlisted tools, four artifacts, five audit events,
  two decision options, and trace evaluation `eval-1afb92d1b3cb` at 100% safety,
  100% usefulness, and 100% overall / stable.
- Approval/undo: the same durable workflow persisted a packet, completed one
  owner action, and reversed it; `external_write=false` and
  `external_systems_changed=false` remained explicit.
- Scheduler: `driftline-monitor` was manually triggered at
  `2026-08-23T01:03:57.392365Z`; Cloud Logging recorded HTTP 200 for
  `/api/scheduler/tick` on `driftline-00271-8vk`.
- Utility visibility: signed operational summaries retain paused sources and
  separate synthetic-only fixtures from sources that need attention. The
  signed browser scan reached the deterministic approval gate with aggregate
  Jira/Confluence/Slack/GitHub context and no CRM totals or external write.
- Operator lifecycle: the signed browser completed `Check now` on the public
  pricing source, then paused and resumed the registered README source. The
  UI showed the explicit pause reason, `Scheduler skips this source`, and the
  restored healthy state after resume; no third-party system was written.

These are deployment and evaluation records, not customer outcomes. Salesforce
aggregate read is not verified: the signed tenant is
`reauthorization_required` after Salesforce rejected its stored refresh token,
so no Salesforce object total is claimed. No real customer pilot has yet
produced before/after time-saved, revenue, retention, or willingness-to-pay
evidence. Monitoring is intentionally bounded to five pinned fixtures plus
exact operator-registered URLs capped at 25 per tenant; it is not universal
competitor crawling.

## Category

**Taskmaster.** Driftline turns a monitored change into a coordinated,
evidence-bound work package and pauses for a human decision before anything
can be published. It is a complete asynchronous workflow, not a chat surface.
It is not claiming Fortified Enterprise Fleet: the public build does not claim
that track's enterprise agent registry, Model Armor, or cross-department
production data plane.

## The problem

A competitor changes one pricing sentence. Product Marketing sees the alert,
but the comparison map, battlecard, deal-desk guidance, enablement notes, and
executive narrative drift out of sync. The expensive work is not detecting the
sentence; it is proving what changed, deciding what it means, coordinating the
owners, and making a reversible update without inventing a claim.

This is the BYOF friction behind Driftline: the recurring RevOps/Product
Marketing chore of reconciling competitive signals with the internal surfaces
that sellers and decision-makers actually use. An alert is not the deliverable;
an evidence-bound, owner-routed change package is.

## The solution

Driftline is a change-to-action control plane for Product Marketing and revenue
operations. It monitors a bounded set of own-product and competitor change
surfaces, creates an append-only evidence record, maps the affected offering
and business domains, and asks Gemini to propose owner-ready updates. A
deterministic policy engine—not Gemini—decides whether the workflow may cross
the human gate.

One observed price change produces four named surfaces in the demo:

1. Comparison map — Product Marketing — re-score price/value.
2. Pricing battlecard — Product Marketing — draft the response.
3. Deal-desk guidance — RevOps — review the discount guardrail.
4. Executive weekly brief — Product Marketing — add the market signal.

Each surface carries the source evidence hash, risk, owner, proposed text,
tradeoffs, citations, and rollback plan. The operator can approve a bounded
packet, claim/complete owner work, or reopen/undo. The public evaluation lane
is intentionally packet-safe; it never pretends that an anonymous judge wrote
to a third-party system.

## What the agent actually does

1. Cloud Tasks starts a durable asynchronous scan.
2. A Google ADK coordinator uses only `inspect_source_change` and
   `get_workflow_state` to verify the source and persist Firestore state.
3. Gemini 3.5 Flash returns a strict, evidence-hash-bound impact analysis for
   all four artifacts.
4. A second Gemini 3.5 Flash Decision Copilot returns two bounded options with
   tradeoffs, citations, rollback, and artifact decisions.
5. Deterministic policy checks the evidence hash, artifact allowlist, risk, and
   human-approval requirement. The model cannot approve itself.
6. Approval persists a versioned packet and append-only audit events. Undo
   appends a reversal marker and returns the workflow to the decision state.

In the signed tenant lane, both model turns also receive a guarded,
aggregate-only projection of verified Jira/Confluence/Slack/GitHub/Salesforce
context. Counts can qualify urgency or owner routing, but raw records,
credentials, and customer outcomes never enter the prompt or trace; the public
judge lane receives an explicit unavailable context shape.

The public fixture moves `Competitor Pro` from `$49` to `$59` per seat per
month. It is synthetic and visibly labelled as such. The console also exposes
the append-only source ledger, recurring change memory, a bounded Gemini vision
before/after pair, owner-action telemetry, and deployment health.

The release includes a deterministic trace-to-eval quality gate. It checks nine
critical safety invariants and five usefulness invariants against the bounded
workflow/ADK trace, fails closed on safety or score regressions, and persists a
redacted live report with release identity and trend. This proves the control
plane can get safer and more useful over time without pretending that synthetic
evaluation records are customer ROI.

## Google technology

- Gemini 3.5 Flash through Vertex AI for evidence-grounded analysis and
  Decision Copilot options.
- Google Agent Development Kit (ADK) for the coordinator, task-mode analysts,
  session runners, and allowlisted tools.
- Cloud Run for the FastAPI + React service, configured scale-to-zero and
  max-one instance for the isolated hackathon project.
- Firestore for durable workflows, source history, tenant state, and audit
  events.
- Cloud Tasks for asynchronous dispatch and bounded retries.
- Cloud Scheduler for the signed monitor cycle.
- Cloud Storage for private, versioned packets and reversal markers.
- Cloud Build and Artifact Registry for the reproducible container release.

## Architecture and safety

The React console and FastAPI API share one Cloud Run service. A scan creates a
Firestore job; Cloud Tasks sends an OIDC-authenticated request to the worker;
ADK records the model/tool trace; Firestore restores the workflow across
process restarts. The deterministic workflow engine owns approval, idempotency,
connector scope, and reversal state.

The public lane is anonymous, tenantless, and packet-only. Signed operator
requests are a separate tenant boundary. Connector credentials are held in
tenant-specific Secret Manager namespaces and are never returned to the
browser, source control, or logs. The isolated signed lane has been exercised
against Driftline-owned Jira, Confluence, Slack, and GitHub targets with
aggregate-only context reads and reversible marker operations. Those probes are
not customer data or customer ROI. Salesforce's owner-controlled callback has
been persisted as a read-only tenant connection, but the latest direct
aggregate probe returned `invalid_grant`; no Salesforce object totals or
successful CRM read are claimed until fresh consent succeeds.

The source adapter accepts pinned fixtures and exact operator-registered public
URLs only. It rejects redirects, query credentials, private addresses, and
unbounded bodies. Competitor content is an observed signal, not verified
product truth.

Signed tenant operators can pause a registered source with a bounded reason and
resume it later without deleting its append-only history. The lifecycle event
is tenant-scoped and audited, the scheduler skips paused sources, and the
anonymous five-fixture judge lane remains immutable. This control is deployed;
its final live proof requires an operator Google identity in the browser.

## Verified release evidence

The exact serving release is independently verifiable from the public
`/health` response and `./scripts/verify_production.sh`; release IDs are not
treated as permanently current just because they were copied into a document.
The public `/health` probe reports the full source SHA and Cloud Build ID, so a
reviewer can independently trace the serving revision; rerun the check after
any later documentation-only release. The exact current revision, image
digest, and build ID are intentionally read from `/health`,
`./scripts/verify_production.sh`, and Cloud Build rather than copied into this
document.
The Cloud Build `release-smoke` step also compared the serving revision's
image digest with the exact Artifact Registry image tag before marking the
build successful.

The exact current proof is the **Latest verified release** section near the
top of this document. The detailed bullet record below is retained as a
historical submission snapshot; it is not a second source of current serving
IDs. The latest code gate passed 326 backend tests (the 325-test count below
belongs to the earlier snapshot).

The current release includes the visible Salesforce reauthorization recovery
control and an explicit `reauthorization_required` health response when a
stored refresh token is rejected. That bounded health state is now durable
across page reloads; the callback metadata and tenant-scoped secret pointer are
durable as well, but no Salesforce object totals or successful CRM read are
claimed until fresh consent succeeds.

- Local gate for the current source: 325 backend tests passed, Ruff passed,
  the frontend production build and frontend contract passed, and the
  Salesforce aggregate-read boundary tests passed. The current serving image
  was built from this exact clean SHA; public CRM readiness now fails closed
  with `external_read=false`, `aggregate_read_verified=false`, and no exposed
  credential values until a tenant completes all three reads.
- CI: GitHub Actions run `32608006535` passed the backend suite, Ruff, frozen
  dependency audit, frontend build, standalone image build, and repository
  hygiene.
- Production check: `scripts/verify_production.sh` passed Firestore,
  Cloud Tasks, Scheduler, uptime, alerting, IAM, Artifact Registry retention,
  and zero recent Cloud Run errors.
- Live agent check: fresh job `job-d12b13245dc8` / workflow
  `3b23899c-e63e-4128-9ad9-e415ace0ac98` returned `needs_approval`,
  `public_source`, `gemini-3.5-flash`, `google_adk`, two allowlisted tools,
  four artifacts, five audit events, and two decision options.
- Current-revision logged-out browser QA visibly rendered
  `Impact analysis · gemini structured`, the Gemini summary/rationale, the
  Decision Copilot, and the approval gate; the scripted live proof above is
  the durable source of the current job/workflow identifiers.
- The paired current-revision approval/undo verifier created job
  `job-14446499342f` / workflow `39a6e84c-0c08-4732-ae30-c6ee5b3f8be4` and
  completed scan -> approval -> owner claim -> owner completion -> undo. The
  packet persisted and its operational output was reversed; Jira, Confluence,
  and Slack remained `external_write=false` in the public packet-safe lane.
  The bounded value proof retains two historical owner completions and 3.7s
  owner-action cycle samples after the reversal; current completion returns to
  zero because undo is intentionally reversible. These are deployment records,
  not customer outcome claims. The logged-out browser now keeps the reversed
  owner-action queue visible after undo, showing four `Reversed` rows and an
  explicit append-only history explanation.
- The current public evaluation window contains 10 bounded workflows and 12
  source observations, with 5 historical owner-action closures, approval
  latency p50/p90 of 23.9s/50.9s, and owner-action cycle p50/p90 of
  3.0s/3.2s. This is Driftline operational telemetry only; current completion
  is 0% after the intentional undo and no customer ROI or revenue claim is
  inferred.
- A current-revision logged-out browser check also switched from a completed
  `competitor/offerings` run to `competitor/blog`; the old workflow and approval
  state cleared immediately and the blog-specific evidence preview appeared.
- Durable recovery check: after a fresh public reload, the browser opened a
  workflow-linked `needs_approval` row from Run history and restored the
  evidence, impact, and human-gate state with no new scan and no console errors.
- Signed source-operations check: the new source-health card **Check now**
  control is available only in the authenticated operator lane; anonymous
  browser QA found zero such controls while retaining the public Run scan.
- Approval/undo check: the paired fresh run persisted the packet, reversed the
  operational output, and returned `external_write=false` and
  `external_systems_changed=false`.
- Trace-to-eval check: the production verifier reads the latest recorded live
  evaluation snapshot and currently confirms the 14-case `trace-eval-v1`
  suite at 100% safety, 100% usefulness, and 100% overall, remaining stable
  against the prior report with no case regressions. The exact evaluation ID
  is emitted by the verifier at release time; the report is redacted telemetry
  and explicitly does not claim customer outcomes.
- Background proof: the isolated `driftline-monitor` Cloud Scheduler job was
  manually triggered during the prior release and Cloud Logging recorded an
  OIDC-authenticated HTTP 200 request to `/api/scheduler/tick` on the then-serving
  `driftline-00162-nvm`. The registry reported five healthy bounded sources;
  cadence rules deferred healthy sources that were not due. A log search from
  that run found no Firestore positional-filter deprecation warning.
- Breadth check on the same serving revision: competitor offerings
  (`job-82ac284398b6`, workflow `a1190503-0c2f-4182-83c9-22e4879fc6e1`),
  competitor narrative/blog (`job-b8a7d0ebcf6d`, workflow
  `7a63eea4-7dec-4626-8b2b-1834a4542716`), and own terms
  (`job-ee66d880b4eb`, workflow `d5f75932-3a41-48a8-8765-d629abae9441`)
  each reached `needs_approval` with Gemini structured analysis, four mapped
  impacts, and five audit events.
- Browser QA: desktop and mobile Lighthouse navigation both scored 100 for
  accessibility, best practices, SEO, and agentic browsing (53/53 checks,
  zero failures). At 390×844, body and document widths equal the viewport and
  the console has no application messages. Below-fold ledger, monitor,
  multimodal, memory, value-proof, run-history, and telemetry reads load when
  their panels approach the viewport.
- Signed connector context proof: the authenticated tenant read returned `19`
  open Jira issues, `7` Confluence pages, `42` recent Slack messages, and `1`
  GitHub issue / `0` PRs. Salesforce remained explicitly authorization-gated
  after a rejected refresh token; no CRM totals or customer outcomes are
  claimed.
- Signed tenant workflow proof: workflow
  `c14ed5d6-fecb-4fc3-a40b-8567d5629ce9` ran the pinned
  `competitor/pricing` fixture through Firestore + Cloud Tasks + Google ADK.
  Approval reactivated only the Jira, Confluence, and Slack destinations shown
  in the impact map; GitHub was not silently fanned out. Reopening the decision
  reversed all three mapped connector markers. This is a reversible connector
  smoke, not customer-pilot evidence.

## Four-minute demo plan

1. State the problem: one competitor change creates multiple stale internal
   surfaces.
2. Click **Run scan** on the deployed URL.
3. Show the evidence diff, source hash, synthetic-data label, Gemini/ADK trace,
   four downstream owners, and the Gemini Decision Copilot options.
4. Open one artifact and the evidence modal; point out the citation and
   rollback.
5. Approve the bounded plan; show the persisted packet, owner work, timeline,
   and audit events.
6. Reopen/undo; show the reversal marker and the unchanged external-write
   flags. Scroll to the append-only history and multimodal evidence.
7. Briefly show Cloud Run/Firestore proof and the public repository.

The video must be public on YouTube or Vimeo and no longer than four minutes;
it is intentionally held until the final product review is complete.

## Findings, limitations, and honest claims

Driftline's strongest differentiated unit is not an alert. It is a
source-hash-bound Change Card that names the affected offering, owners, risk,
proposed update, citations, and rollback before anyone acts. The product has
real operational utility for a Product Marketing or competitive-intelligence
team that repeatedly reconciles public changes with internal enablement work.

What is proven: live Gemini/ADK execution, durable asynchronous state, strict
evidence binding, deterministic approval, append-only audit, reversible packet
behavior, isolated Cloud Run/Firestore architecture, and signed connector
boundaries.

What is not claimed: customer revenue lift, hours saved, retention impact,
willingness-to-pay, a multi-customer pilot, arbitrary competitor crawling,
Salesforce execution, self-serve enterprise billing/SSO, or an anonymous
third-party write. The public demo uses five pinned fixtures; a real pilot and
before/after business outcomes remain the highest-value commercial validation.

## Official links and eligibility

- [Hackathon overview](https://allthingsagentichackathon.devpost.com/)
- [Official rules](https://allthingsagentichackathon.devpost.com/rules)
- [Official judging criteria](https://allthingsagentichackathon.devpost.com/details/judging-criteria)
- [Official submission requirements](https://allthingsagentichackathon.devpost.com/details#what-to-submit)
- [Verified local rules record](https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md)

The current official deadline is **August 31, 2026 at 5:00 PM PDT** (September
1, 2026 at 00:00 UTC). The entry is designed around the Taskmaster track and
the official judging weights: operational utility 40%, architectural
discipline and technology 30%, and demo/production readiness 30%.

The project discloses that Driftline continues an earlier concept conversation
and incorporates the supplied source package; the current implementation,
deployment, verification, and documentation work was completed or materially
changed during the submission period. The public repository's first commit is
dated August 18, 2026, inside the August 3–31 submission period; that history
anchor does not misrepresent the earlier concept conversation as contest work.
