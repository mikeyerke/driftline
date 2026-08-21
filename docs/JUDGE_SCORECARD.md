# Driftline judge scorecard

This is a claim-to-evidence map for the Google All Things Agentic judging
criteria. It describes the current serving release, not an aspirational SaaS
roadmap.

Current release: source `7747baa`, Cloud Run `driftline-00124-ln5`, Cloud Build
`ea1e7339-533b-4109-8128-7f166efd1603`, project
`driftline-hackathon-2026`, 100% traffic.

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

- Current-revision logged-out browser QA visibly showed Gemini structured
  impact analysis, four evidence-bound artifacts, two options, and the
  deterministic approval gate; the scripted live proof below records the
  durable job/workflow identifiers.
- `scripts/verify_live_agent.sh`: fresh job `job-19adf8d0c447`, workflow
  `4e2d3d26-db4d-48f9-ad59-52c102091877`, five audit events and four artifacts.
- `scripts/verify_public_approval_undo.sh`: fresh job `job-00a15eaba608`,
  workflow `adfb0073-5331-4796-8f54-7e27f66e189b`, packet persisted and
  reversed with both external-write flags false. The verifier now also fails
  closed unless the approval journey carries structured Gemini impact/Decision
  Copilot options, passing deterministic policy review, and matching evidence
  hashes.

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
  `sha256:86769ded2dd5d53d3ad585757c957471e53afdefeca0f3a0b0d6f64ec12ab84d`.
- Signed isolated connector probes are documented in
  [`RESOURCE_INVENTORY.md`](RESOURCE_INVENTORY.md); the anonymous lane remains
  packet-only by design.

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

- 248 backend tests, Ruff, frontend production build, standalone image build,
  and repository hygiene pass in GitHub Actions run `32500963459`.
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
- No Salesforce execution is claimed; the read-only OAuth lane awaits final
  tenant consent.
- No anonymous third-party write is claimed; connector writes require a signed
  operator and remain isolated from judge traffic.
- No Fortified Enterprise Fleet or Startup Excellence eligibility is claimed.

## Suggested demo order

Run scan → evidence diff → Gemini/ADK trace → impact map → artifact details →
Decision Copilot → approve → packet/audit → undo → append-only history and
multimodal evidence → Cloud Run proof. Keep the video public and under four
minutes when it is finally uploaded.
