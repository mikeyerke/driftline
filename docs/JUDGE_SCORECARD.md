# Driftline judge scorecard

This is a claim-to-evidence map for the Google All Things Agentic judging
criteria. It describes the current serving release, not an aspirational SaaS
roadmap.

The exact serving release is verified at read time by
`./scripts/verify_production.sh` and the public `/health` contract; this
scorecard intentionally does not hardcode a revision ID that can go stale
after a later commit. Use the live check after every release. The
submission-facing scorecard is
kept in sync at [`submission/JUDGE_SCORECARD.md`](../submission/JUDGE_SCORECARD.md).

## Innovation and operational utility — 40%

### The judge should see

- One competitor pricing sentence becomes four named downstream surfaces:
  comparison map, pricing battlecard, deal-desk guidance, and executive brief.
- The workflow runs asynchronously through Cloud Tasks rather than waiting in
  a chat turn.
- Gemini produces an evidence-bound impact analysis and two decision options
  with citations, tradeoffs, and rollback.
- Deterministic policy stops high-risk work at a human gate. Approval creates a
  packet and owner work; undo appends a reversal marker.
- The append-only ledger and change memory show that a change is remembered,
  not merely alerted once.

### Live evidence

- The trace-to-eval gate (`scripts/verify_trace_eval.sh`) scores fourteen
  independent safety/usefulness cases. Critical safety must be 100%,
  usefulness at least 75%, overall at least 90%, and any regression against a
  prior report fails closed. The deployed live-agent verifier applies the same
  suite to a fresh Google ADK/Gemini trace and persists only a redacted report
  in `driftline_trace_evaluations`; the latest recorded live report snapshot is
  `eval-3781a961036e`, stable against the prior report with 100% safety,
  100% usefulness, 100% overall, and no case regressions. These are evaluation telemetry, not customer
  outcomes.

- Logged-out desktop and 390x844 mobile browser QA showed the interactive
  impact map before and after a scan: source -> offering -> impact area -> work
  surface -> handoff stages, directional node focus, readable sibling dimming,
  bounded inspector, and worklist handoff; mobile `scrollWidth` stayed equal to
  the viewport width.
- The current 500px logged-out browser check exercised all six sidebar actions
  after deferred panels mounted: each target landed below the sticky header,
  `settings-section` and `deployment-section` were each unique, and no console
  messages were emitted.
- A fresh logged-out browser check jumped directly to the bottom after load;
  Trace-to-eval, Value proof, and Change memory all hydrated instead of
  remaining behind an in-view placeholder. Desktop and 500px mobile widths had
  no horizontal overflow.
- `scripts/verify_live_agent.sh`: fresh job `job-17f83337c4b8`, workflow
  `0ac5d4f9-71cb-47ff-8c64-821e1f9ad71f`, five audit events, four artifacts,
  two decision options, a passing trace evaluation, and `needs_approval`.
- `scripts/verify_public_approval_undo.sh`: fresh job `job-8f08d64a2939`,
  workflow `a5ef3d5e-01d6-4a53-80ff-e81b0d2492b1` persisted, approved one
  owner action, recorded its completion, and then reversed it with
  `external_write=false` and `external_systems_changed=false`. The verifier
  fails closed unless the
  approval journey carries structured Gemini impact / Decision Copilot
  options, passes deterministic policy review, and matches evidence hashes.
  The resulting bounded value proof retains two historical owner completions
  and 3.7s owner-action cycle samples even though current completion returns
  to zero after intentional undo; this is operational evidence, not a
  customer-outcome claim. The logged-out browser also keeps the reversed
  owner-action queue visible after **Reopen decision**, with four `Reversed`
  rows and a clear append-only history explanation.
- The current public evaluation window reports 12 bounded workflows and 12
  source observations, with 7 historical owner-action closures, approval
  latency p50/p90 of 22.3s/132.9s, and owner-action cycle p50/p90 of
  2.8s/18.8s. These are isolated Driftline operational records; current
  completion is 0% after intentional undo, and none of these values is a
  customer time-saved, revenue, retention, or willingness-to-pay claim.
- A logged-out browser check on the current release changed the selector from
  a completed `competitor/offerings` workflow to `competitor/blog`. The old
  workflow and approval state disappeared immediately, the blog-specific
  preview appeared, and approval remained disabled until a fresh scan. This
  protects judges and operators from cross-scenario stale state.
- Durable run recovery: a fresh public reload exposed **Open run** on a
  workflow-linked history row; opening it restored evidence, approval state,
  and artifact decisions without starting another scan or emitting console
  errors.
- Source operations: the signed console now exposes **Check now** on each
  source-health card, with paused sources disabled and anonymous judging kept
  free of the operator mutation control.
- The authenticated operator session preserves its Google token and tenant
  membership list when changing the selected tenant, keeping every subsequent
  request signed and tenant-scoped.
- A manual run of the isolated `driftline-monitor` Scheduler job produced an
  OIDC-authenticated HTTP 200 `/api/scheduler/tick` request on the serving
  revision; healthy sources were correctly deferred until their cadence due
  time rather than spending another model call.
- An earlier direct Scheduler run at `2026-08-22T02:32:43Z` returned an
  OIDC-authenticated HTTP 200 on the then-serving `driftline-00162-nvm`; the registry then
  reported all five bounded sources healthy with zero stale or failed entries.
  Sources not due at that moment were deferred by cadence as designed.
- The latest production verifier found no `Detected filter using positional
  arguments` warning after the Firestore `FieldFilter` cleanup; the only
  recent warning was the known ADK response-part diagnostic, with zero
  application errors.
- The same deployed agent handled three additional bounded source families:
  competitor offerings (`job-82ac284398b6`, workflow
  `a1190503-0c2f-4182-83c9-22e4879fc6e1`), competitor narrative/blog
  (`job-b8a7d0ebcf6d`, workflow `7a63eea4-7dec-4626-8b2b-1834a4542716`), and
  own terms (`job-ee66d880b4eb`, workflow
  `d5f75932-3a41-48a8-8765-d629abae9441`). Each reached `needs_approval` with
  Gemini structured analysis, four mapped impacts, and five audit events.
- Operator source onboarding is bounded to 25 enabled custom sources per
  tenant, with updates allowed for existing IDs at the limit and fail-closed
  persistence errors. This is independently tested from the deployment-wide
  25-source scheduler cap, preventing one tenant from consuming the whole
  registry.

## Architectural discipline and technology — 30%

### The judge should see

- Gemini 3.5 Flash is used through Vertex AI and Google ADK, not mentioned only
  in documentation. The persisted trace records both allowlisted tool calls.
- Firestore restores durable workflow, source-history, tenant, and audit state.
- Cloud Tasks provides OIDC-authenticated asynchronous dispatch and bounded
  retries; Cloud Scheduler drives the bounded monitor cycle.
- The model cannot approve itself. Pydantic schema validation, evidence hashes,
  artifact allowlists, deterministic policy, idempotency, and reversal state
  sit outside model output.
- Public and signed tenant lanes are separate. Tenant connector credentials
  resolve through tenant-specific Secret Manager namespaces and are not sent to
  the browser or logs.
- Signed tenant `live`, `tenant_demo`, and `monitor` runs can attach a second,
  normalized aggregate connector read to the Change Card. Only fixed scopes,
  bounded counts, and allowlisted Salesforce object metadata survive; an
  `internal_context_reader` audit event records the attachment. Both the
  impact analyst and Decision Copilot receive a guarded aggregate-only prompt
  projection, while the redacted trace records only context provenance. The
  anonymous judge lane never calls this seam.
- Cloud Run is isolated to `driftline-hackathon-2026`, scale-to-zero, and
  max-one instance; the runtime has no project-level Secret Manager access.

### Live evidence

- `scripts/verify_production.sh`: Firestore, Tasks, Scheduler, uptime, alerting,
  IAM, Artifact Registry retention, zero recent Cloud Run errors, OIDC tenant
  membership, and the no-project-wide-secret-reader boundary all pass.
- Cloud Build's post-deploy smoke gate compares the serving revision digest
  with the exact Artifact Registry image tag and verifies the public health
  SHA/build contract before declaring the build successful.
- Latest recorded immutable image digest snapshot:
  `sha256:2a9b6ce237a1b5f9ee6bc3c9436b2a2b23a112f28c5fb8d3db6e501976951d1b`.
- Public `/health` reports the same full release SHA as the source commit and
  the Cloud Build ID, making the serving revision independently traceable.
- Signed isolated connector probes are documented in
  [`RESOURCE_INVENTORY.md`](RESOURCE_INVENTORY.md); the anonymous lane remains
  packet-only by design. Salesforce has a durable read-only OAuth callback
  record, but the last direct health probe returned `invalid_grant`, so no CRM
  object totals are claimed until the owner completes fresh consent.
- The authenticated tenant **Refresh context** read verified aggregate-only
  Jira, Confluence, Slack, and GitHub reads (`18` / `7` / `38` / `0` issues and
  PRs respectively) while keeping Salesforce explicitly authorization-gated.
- A signed tenant scan then persisted job `job-a33d07ac658c` / workflow
  `75da1f00-e657-4ba3-bba6-80c298b747be` at `needs_approval` through Google ADK
  + Gemini 3.5 Flash; no connector write was attempted.

## Demo and production readiness — 30%

### The judge should see

- The public URL loads without credentials and labels synthetic data.
- The live scan shows the source diff, hash, model/tool trace, impact map,
  Decision Copilot, human gate, approval packet, audit timeline, and undo.
- The lower panels load their bounded reads on approach, keeping first paint
  small while preserving inspectability.
- The repository contains the architecture diagram, setup/deploy commands,
  rules record, verification scripts, and resource inventory.

### Live evidence

- 291 backend tests, Ruff, frontend production build, standalone image build,
  and repository hygiene pass in GitHub Actions run `32572937856`; the frozen
  dependency export separately passes `pip-audit` with no known vulnerabilities.
- Desktop and mobile Lighthouse navigation both score 100 for accessibility,
  best practices, SEO, and agentic browsing (53/53 checks, zero failures).
- At 390×844, body and document widths equal the viewport and the browser has no
  application console messages.
- Public `/health` returns Firestore persistence and async-jobs status with
  `Cache-Control: no-store`.

## Claims deliberately not made

- No customer revenue lift, time saved, retention impact, or willingness-to-pay
  is claimed; the value panel is deployment telemetry, not ROI.
- No arbitrary competitor crawl is claimed; the public lane uses five pinned
  fixtures and bounded operator-registered URLs.
- No Salesforce object read is claimed; the read-only OAuth lane requires fresh
  tenant consent after the stored refresh token returned `invalid_grant`.
- No anonymous third-party write is claimed; connector writes require a signed
  operator and remain isolated from judge traffic.
- No Fortified Enterprise Fleet or Startup Excellence eligibility is claimed.

## Suggested demo order

Run scan → evidence diff → Gemini/ADK trace → impact map → artifact details →
Decision Copilot → approve → packet/audit → undo → append-only history and
multimodal evidence → Cloud Run proof. Keep the video public and under four
minutes when it is finally uploaded.
