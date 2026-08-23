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
| Cloud Run production service | **Deployed and live** | `driftline-00283-g9w`, 100% traffic; `/health` returns `ddf5a5b` | Isolated `driftline-hackathon-2026` project |
| Firestore workflow/audit persistence | **Live verified** | Production verifier and live workflow records | 30-day default retention; tenant policy can narrow/extend within bounds |
| Google ADK + Gemini | **Live verified** | `job-f4e0f0a0ae41`, `eval-665f410abf36`, 14/14 trace gate | Public runs are fixed, bounded scenarios |
| Deterministic approval gate | **Live verified** | High-risk actions stop at `needs_approval` | The model cannot approve itself |
| Reversible Driftline packet/owner action | **Live verified** | `job-2563a7cc5cbf`; completed then reversed | Public lane writes only Driftline-owned packet artifacts |
| Bounded monitoring | **Live verified** | Five healthy pinned fixtures; scheduler and append-only observations | No universal crawling; tenant URLs require explicit registration |
| Interactive impact map | **Live verified** | Source, offering, impact, work-surface, and handoff node traversal | Evidence hash is inherited by every node |
| Jira context read | **Externally verified** | Isolated `KAN` project; aggregate open-work read succeeds | Fixed project scope; no user-supplied JQL |
| Jira create/reuse/reverse adapter | **Externally verified** | 2026-08-23: `KAN-20` created, idempotently reactivated, then reversed | Uses tenant Secret Manager binding; undo keeps the issue and changes only Driftline-owned labels/comment |
| Hosted signed Jira HTTP round trip | **Historical live proof; rerun pending** | Prior OIDC canaries are archived in `RESOURCE_INVENTORY.md` | Current public lane intentionally reports `external_write=false` |
| Salesforce aggregate read | **Implemented, not verified** | OAuth/health lane returns reauthorization state | No object totals are claimed |
| Confluence / Slack / GitHub | **Adapters implemented; not current core path** | Connector contracts and historical proof exist | Keep out of the main claim unless rerun on the current candidate |
| Pilot measurement instrumentation | **Implemented and tested** | Paired baseline/Driftline validation and idempotent retries | Operator-reported until reconciled to evidence |
| Customer ROI / time saved / revenue / retention / WTP | **Not measured** | No customer pilot exists | Do not present deployment telemetry as customer outcomes |

## Current release custody

- Repository: `main` (documentation-only commits after the runtime candidate);
  working tree is clean and matches `origin/main`. Verify the exact current
  source SHA from the repository before a future code release.
- Serving runtime: `ddf5a5b2df731ad6ea451700c48ad9e9915df0db`.
- Cloud Run revision: `driftline-00283-g9w`.
- Cloud Build: `721e1bc2-f294-4366-b77e-dea29a4c10d5`.
- Image digest: `sha256:4b02f5d1b8432f5ce4a0055db1d4ad944606b4597d59386a421d981c27537ce3`.

The next release must either deploy the repository head or explicitly tag the
serving runtime. Do not create another documentation-only release record.

## What “real” means here

The following are real and directly testable today:

- the deployed ADK/Gemini workflow;
- evidence hashes, deterministic policy checks, and durable audit records;
- a real bounded Jira adapter using the tenant-scoped Secret Manager credential;
- Jira marker idempotency and reversible labels/comments;
- production health, persistence, queues, scheduler, and release gates.

The following are deliberately not claimed:

- universal competitor crawling;
- a Salesforce CRM read in the current release;
- customer ROI, revenue, retention, or willingness-to-pay;
- a public visitor writing to Jira or any other external system;
- a completed customer pilot.

## Definition of done for the remaining work

1. One current-candidate hosted signed Jira create/reuse/reverse proof, or an
   explicit decision to ship the documented adapter proof without making it part
   of the public smoke.
2. One small, real operator pilot with aggregate before/after measurements.
3. One release candidate with a single SHA, complete automated gates, live
   browser proof, and no stale claims in README/Devpost.
4. Freeze scope, record the demo, and submit. No additional connector or UI
   feature work after these gates unless a gate fails.
