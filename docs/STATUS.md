# Driftline current status

This is the single source of truth for the current product state. It separates
implemented code, deployed proof, externally verified behavior, and customer
evidence. Historical release notes remain in `docs/RESOURCE_INVENTORY.md`.

Updated: 2026-08-23 (America/Chicago)

## Product contract

Driftline turns an allowlisted market or product change into an evidence-bound
work package:

`source change -> evidence/hash -> impact map -> owner work -> human approval -> reversible action -> audit`

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
| Cloud Run production service | **Deployed and live** | `driftline-00286-plm`, 100% traffic; `/health` returns release SHA `e38facc` | Isolated `driftline-hackathon-2026` project |
| Firebase Hosting public facade | **Live verified** | `driftline-ops.web.app` rewrites to Cloud Run; `/health` and the browser console load over HTTPS | Firebase is linked to the same isolated project; Google Analytics disabled |
| Firestore workflow/audit persistence | **Live verified** | Production verifier and live workflow records | 30-day default retention; tenant policy can narrow/extend within bounds |
| Google ADK + Gemini | **Live verified** | Current facade proof: `job-987fd00ebd03`, `eval-716c031352d6`, 14/14 trace gate | Public runs are fixed, bounded scenarios |
| Deterministic approval gate | **Live verified** | High-risk actions stop at `needs_approval` | The model cannot approve itself |
| Reversible Driftline packet/owner action | **Live verified** | Current facade proof: `job-ca3895116dad`, workflow `90bbba3d-2941-48a6-9cb9-f18579eaf290`; completed then reversed | Public lane writes only Driftline-owned packet artifacts |
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

- Repository: `main` (documentation-only commits after the runtime candidate);
  working tree is clean and matches `origin/main`. Verify the exact current
  source SHA from the repository before a future code release.
- Serving runtime: `e38facc43745eab267eacd2da4aa28914dff383b`.
- Cloud Run revision: `driftline-00286-plm` (same immutable image; CORS allowlist now includes the Firebase facade).
- Cloud Build: `96dbf2d7-7ee3-490a-a854-bef5c9615efc`.
- Image digest: `sha256:19980ec57ed89d34f62474ef5b043fd9ce47f0e815650d09b04152fa3e6114f4`.

The serving candidate is `e38facc`; the later `00286` promotion changed only
the runtime CORS allowlist so browser actions from the Firebase facade are
accepted. Repository changes after the candidate are documentation/config
only; no unverified application code was introduced.

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
