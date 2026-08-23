# Driftline current status

This is the single source of truth for the current product state. It separates
implemented code, deployed proof, externally verified behavior, and customer
evidence. Historical release notes remain in `docs/RESOURCE_INVENTORY.md`.

Updated: 2026-08-23 (America/Chicago)

## Product contract

Driftline turns an allowlisted market or product change into an evidence-bound
work package:

`source change -> evidence/hash -> impact map -> owner work -> human approval -> reversible action -> audit`

The product wedge is one real operational handoff, not a chat assistant or an
unbounded crawler. The anonymous surface is a deterministic, packet-safe judge
lane. The signed operator surface is the production control plane for a real
tenant and its configured connectors.

## State matrix

| Capability | State | Evidence | Boundary |
| --- | --- | --- | --- |
| Cloud Run production service | **Deployed and live** | `driftline-00284-5kd`, 100% traffic; `/health` returns release SHA `63d9699` | Isolated `driftline-hackathon-2026` project |
| Firestore workflow/audit persistence | **Live verified** | Production verifier and live workflow records | 30-day default retention; tenant policy can narrow/extend within bounds |
| Google ADK + Gemini | **Live verified** | Current revision: `job-8cf6826d7ceb`, `eval-aa793a59568d`, 14/14 trace gate | Public runs are fixed, bounded scenarios |
| Deterministic approval gate | **Live verified** | High-risk actions stop at `needs_approval` | The model cannot approve itself |
| Reversible Driftline packet/owner action | **Live verified** | Current revision: `job-8b45b24f28b4`, workflow `7799a5ee-5cc1-41c1-967c-8403d955bd4e`; completed then reversed | Public lane writes only Driftline-owned packet artifacts |
| Bounded monitoring | **Live verified** | Five healthy pinned fixtures; scheduler and append-only observations | No universal crawling; tenant URLs require explicit registration |
| Interactive impact map | **Live verified** | Source, offering, impact, work-surface, and handoff node traversal | Evidence hash is inherited by every node |
| Jira context read | **Externally verified** | Isolated `KAN` project; aggregate open-work read succeeds | Fixed project scope; no user-supplied JQL |
| Jira create/reuse/reverse adapter | **Externally verified** | 2026-08-23: `KAN-20` created, idempotently reactivated, then reversed | Uses tenant Secret Manager binding; undo keeps the issue and changes only Driftline-owned labels/comment |
| Hosted signed Jira HTTP round trip | **Live verified** | 2026-08-23 signed Google OIDC browser run: workflow `a9bcf39c-c0ef-420c-8d66-964e35a9b93a`, job `job-d622d771fb7a`; approval HTTP 200 reactivated `KAN-19`, signed undo HTTP 200 reversed it | One tenant-scoped Task marker; anonymous/public lane remains packet-safe and reports `external_write=false` |
| Salesforce aggregate read | **Implemented, not verified** | OAuth/health lane returns reauthorization state | No object totals are claimed |
| Confluence / Slack / GitHub | **Adapters implemented; not current core path** | Connector contracts and historical proof exist | Keep out of the main claim unless rerun on the current candidate |
| Pilot measurement instrumentation | **Implemented and tested** | Paired baseline/Driftline validation and idempotent retries | Operator-reported until reconciled to evidence |
| Customer ROI / time saved / revenue / retention / WTP | **Not measured** | No customer pilot exists | Do not present deployment telemetry as customer outcomes |

## Current release custody

- Repository head before the submission-package branch:
  `e38facc43745eab267eacd2da4aa28914dff383b` (release-ledger documentation
  over serving source `63d96995808c8b1a891abd16682d645db19986fb`).
- Serving runtime: `63d96995808c8b1a891abd16682d645db19986fb`.
- Cloud Run revision: `driftline-00284-5kd`.
- Cloud Build: `92a1fcac-7d63-4c73-8306-0dcbe18c2466`.
- Image digest: `sha256:832079417ab85423c7b8fdd4682aa29430e723ecf30344708a663f26eb1c69b7`.

The repository head is the serving candidate. The deployment was a deliberate
documentation-aligned promotion over the previously tested runtime; no
unverified code was introduced.

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
3. One release candidate with a single SHA, complete automated gates, live
   browser proof, and no stale claims in README/Devpost.
4. Freeze scope, record the demo, and submit. No additional connector or UI
   feature work after these gates unless a gate fails.
