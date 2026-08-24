# Driftline current status

This is the single source of truth for the current product state. It separates
implemented code, deployed proof, externally verified behavior, and customer
evidence. Historical release notes remain in `docs/RESOURCE_INVENTORY.md`.

Updated: 2026-08-24 (America/Chicago)

## Product contract

Driftline turns bounded evidence into an evidence-bound work package and closes
the product-decision learning loop:

`evidence -> independent council -> counterfactuals -> human experiment -> measured outcome -> reopen or close`

## Public access

The polished public entry point is **https://driftline-ops.web.app/**. Firebase
Hosting is a same-origin HTTPS facade in the isolated Driftline project and
rewrites every request to the Cloud Run `driftline` service in `us-central1`.
The generated Cloud Run URL remains available as the health/fallback origin:
`https://driftline-xvxczqg62a-uc.a.run.app/`. The facade does not introduce a
second backend, database, identity, or connector credential store.

The product wedge is one real operational handoff, not a chat assistant or an
unbounded crawler. The anonymous surface is a deterministic, packet-safe judge
lane. The signed operator surface is the production control plane for a real
tenant and its configured connectors.

## State matrix

| Capability | State | Evidence | Boundary |
| --- | --- | --- | --- |
| Cloud Run production service | **Deployed and live verified** | `driftline-00291-v89`, 100% traffic; `/health` returns full release SHA `1b8a8bfbcf2249136dbf08de54c0f7ee15f575d6` and build `154547e7-36ae-4eb2-a79a-35064e293191` | Isolated `driftline-hackathon-2026`; min 0/max 1 instance |
| Firebase Hosting public facade | **Live verified** | `driftline-ops.web.app` rewrites to Cloud Run; `/health` and the browser console load over HTTPS | Firebase is linked to the same isolated project; Google Analytics disabled |
| Firestore workflow/audit persistence | **Live verified** | Production verifier and live workflow records | 30-day default retention; tenant policy can narrow/extend within bounds |
| Google ADK + Gemini | **Live verified** | Fresh facade proof: `job-e253f458c786`, `eval-b00a339dfd10`, 14/14 trace gate | Public runs are fixed, bounded scenarios |
| Deterministic approval gate | **Live verified** | High-risk actions stop at `needs_approval` | The model cannot approve itself |
| Reversible Driftline packet/owner action | **Live verified** | Fresh facade proof: `job-0f7c269392a3`, workflow `ef53b1b0-8483-4114-acde-4424bf2c1ce7`; completed then reversed | Public lane writes only Driftline-owned packet artifacts |
| Bounded monitoring | **Live verified** | Five healthy pinned fixtures; scheduler and append-only observations | No universal crawling; tenant URLs require explicit registration |
| Interactive impact map | **Live verified** | Source, offering, impact, work-surface, and handoff node traversal | Evidence hash is inherited by every node |
| Jira context read | **Externally verified** | Isolated `KAN` project; aggregate open-work read succeeds | Fixed project scope; no user-supplied JQL |
| Jira create/reuse/reverse adapter | **Externally verified** | 2026-08-23: `KAN-20` created, idempotently reactivated, then reversed | Uses tenant Secret Manager binding; undo keeps the issue and changes only Driftline-owned labels/comment |
| Hosted signed Jira HTTP round trip | **Live verified** | 2026-08-23 signed Google OIDC browser run: workflow `a9bcf39c-c0ef-420c-8d66-964e35a9b93a`, job `job-d622d771fb7a`; approval HTTP 200 reactivated `KAN-19`, signed undo HTTP 200 reversed it | One tenant-scoped Task marker; anonymous/public lane remains packet-safe and reports `external_write=false` |
| Salesforce aggregate read | **Implemented, not verified** | OAuth/health lane returns reauthorization state | No object totals are claimed |
| Confluence / Slack / GitHub | **Adapters implemented; not current core path** | Connector contracts and historical proof exist | Keep out of the main claim unless rerun on the current candidate |
| Pilot measurement instrumentation | **Implemented and tested** | Paired baseline/Driftline validation and idempotent retries | Operator-reported until reconciled to evidence |
| Customer ROI / time saved / revenue / retention / WTP | **Not measured** | No customer pilot exists | Do not present deployment telemetry as customer outcomes |
| Decision Twin evidence/council/counterfactual loop | **Deployed and live verified** | Case `decision-onboarding-ca91c815d6629f4d5ff5acbd`: real `google_adk`, five cited roles, `ship`/`segment`/`defer` disagreement, named-human approval, measured outcome, generation-2 reopen, full prior approval/experiment lineage | The showcased case and outcome are bounded demo evidence, not customer research |
| BigQuery aggregate evidence adapter | **Provisioned and live verified** | `bigquery-aggregate-attached`, minimum cohort 84; sample-weighted, allowlisted, parameterized, dry-run checked, 50 MB billed-byte cap | Aggregate-only; privacy floor rejects cohorts below 25 |

## Current release custody

- Open PR branch: `codex/win-taskmaster-20260823`; PR #16 remains unmerged.
- Serving runtime: `1b8a8bfbcf2249136dbf08de54c0f7ee15f575d6`.
- Cloud Run revision: `driftline-00291-v89` at 100% traffic.
- Cloud Build: `154547e7-36ae-4eb2-a79a-35064e293191`.
- Image digest: `sha256:18d8e1f76dd3c2a305f6e76aacbbc75fe876a2028f6881e371f9d3b21e34d450`.
- GitHub Verify Driftline run `32757068133`: backend, frontend, standalone
  image, and repository hygiene all passed.

## What “real” means here

The following are real and directly testable today:

- the deployed ADK/Gemini workflow;
- evidence hashes, deterministic policy checks, and durable audit records;
- a real bounded Jira adapter using the tenant-scoped Secret Manager credential;
- a hosted signed-OIDC operator run that reactivated one Driftline-owned Jira
  marker and then reversed it, with Cloud Run logs showing the tenant-secret
  impersonation path and HTTP 200 responses for both approval and undo;
- Jira marker idempotency and reversible labels/comments;
- production health, persistence, queues, scheduler, and release gates.

The following are deliberately not claimed:

- universal competitor crawling;
- a Salesforce CRM read in the current release;
- customer ROI, revenue, retention, or willingness-to-pay;
- a public visitor writing to Jira or any other external system;
- a completed customer pilot.

## Definition of done for the remaining work

1. One current-candidate hosted signed Jira create/reuse/reverse proof —
   **complete** for the isolated `driftline-demo` tenant. The current proof is
   preserved in `docs/INTERNAL_PILOT_2026-08-23.md` and the resource inventory.
2. One small, real operator pilot with aggregate before/after measurements.
3. Immutable Decision Twin deployment, BigQuery provisioning, CI, and all
   production verification scripts — **complete** at the release above.
4. One release candidate with a single SHA and complete automated/live API
   proof — **complete**; final entrant-owned video/browser QA remains open.
5. Freeze scope, run real PM validation, record the demo, and submit. No additional connector or UI
   feature work after these gates unless a gate fails.
