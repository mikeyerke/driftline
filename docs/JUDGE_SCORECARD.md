# Driftline judge scorecard

This is a claim-to-evidence map for the Google All Things Agentic judging
criteria. It describes the current serving release, not an aspirational SaaS
roadmap.

Current release: source `6215311`, Cloud Run `driftline-00156-k4k`, Cloud Build
`ddbb1aea-fa8c-4618-bda4-bba1468f852c`, project
`driftline-hackathon-2026`, 100% traffic. The submission-facing scorecard is
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

- Logged-out desktop and 390x844 mobile browser QA showed the interactive
  impact map before and after a scan: source -> offering -> impact area -> work
  surface -> handoff stages, directional node focus, readable sibling dimming,
  bounded inspector, and worklist handoff; mobile `scrollWidth` stayed equal to
  the viewport width.
- `scripts/verify_live_agent.sh`: fresh job `job-aafdfe5bf8c6`, workflow
  `f14f7e58-99f4-4600-8b3a-f6aafa98e9e0`, five audit events, four artifacts,
  two decision options, and `needs_approval`.
- `scripts/verify_public_approval_undo.sh`: fresh job `job-020b2051e844`,
  workflow `3f505405-9a7e-44a3-afe2-29db425bdce5`; the packet persisted and
  was reversed with `external_write=false` and
  `external_systems_changed=false`. The verifier fails closed unless the
  approval journey carries structured Gemini impact / Decision Copilot
  options, passes deterministic policy review, and matches evidence hashes.
- A manual run of the isolated `driftline-monitor` Scheduler job produced an
  OIDC-authenticated HTTP 200 `/api/scheduler/tick` request on the serving
  revision; healthy sources were correctly deferred until their cadence due
  time rather than spending another model call.
- A second direct Scheduler run at `2026-08-21T20:31:32Z` selected only the two
  due sources, completed monitor jobs `job-ab0c901478e7` and
  `job-5b317c2f1c7d`, advanced their Firestore observation timestamps, and
  left the other three sources deferred. The run recorded zero dead-lettered
  tasks and zero Cloud Run `ERROR` logs.
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
- Cloud Run is isolated to `driftline-hackathon-2026`, scale-to-zero, and
  max-one instance; the runtime has no project-level Secret Manager access.

### Live evidence

- `scripts/verify_production.sh`: Firestore, Tasks, Scheduler, uptime, alerting,
  IAM, Artifact Registry retention, zero recent Cloud Run errors, OIDC tenant
  membership, and the no-project-wide-secret-reader boundary all pass.
- Current immutable image digest:
  `sha256:2e2fd930a57591c99f99d2e084bd6e6dcd7dc923d778c97357596760b89372d1`.
- Signed isolated connector probes are documented in
  [`RESOURCE_INVENTORY.md`](RESOURCE_INVENTORY.md); the anonymous lane remains
  packet-only by design. Salesforce has a durable read-only OAuth callback
  record, but the last direct health probe returned `invalid_grant`, so no CRM
  object totals are claimed until the owner completes fresh consent.
- The authenticated tenant **Refresh context** read verified aggregate-only
  Jira, Confluence, Slack, and GitHub reads (`18` / `7` / `38` / `0` issues and
  PRs respectively) while keeping Salesforce explicitly authorization-gated.

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

- 264 backend tests, Ruff, frontend production build, standalone image build,
  and repository hygiene pass in GitHub Actions run `32541414000`; the frozen
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
