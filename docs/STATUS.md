# Driftline current status

This is the single source of truth for the current product state. It separates
implemented code, deployed proof, externally verified behavior, and customer
evidence. Historical release notes remain in `docs/RESOURCE_INVENTORY.md`.

Updated: 2026-08-26 (America/Chicago)

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
| Cloud Run production service | **Deployed and live verified** | Final release: `driftline-00305-xln`, 100% traffic; `/health` returned serving application SHA `03ec8f12fc23d265c89b462a345a5b599a6411e8` and build `c01bec2e-a950-407c-873b-b1d4fdc6bae6` | Isolated `driftline-hackathon-2026`; min 0/max 1 instance |
| Firebase Hosting public facade | **Live verified** | `driftline-ops.web.app` rewrites to Cloud Run; `/health` and the browser console load over HTTPS | Firebase is linked to the same isolated project; Google Analytics disabled |
| Firestore workflow/audit persistence | **Live verified** | Production verifier and live workflow records | 30-day default retention; tenant policy can narrow/extend within bounds |
| Google ADK + Gemini | **Live verified** | Final facade proof: `job-7afefad5be8f`, `eval-1c74b1b36cb8`, 14/14 trace gate | Public runs are fixed, bounded scenarios |
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
| Decision Twin evidence/council/counterfactual loop | **Deployed and live verified** | Case `decision-onboarding-75c4ca50b1faaab179a02b29`: real `google_adk`, five cited roles, named-human approval, Cloud Tasks measurement, generation-2 rollback recommendation, and full prior approval/outcome lineage | The showcased case and outcome are bounded demo evidence, not customer research |
| BigQuery aggregate evidence adapter | **Provisioned and live verified** | `bigquery-aggregate-attached`, minimum cohort 84; sample-weighted, allowlisted, parameterized, dry-run checked, 50 MB billed-byte cap | Aggregate-only; privacy floor rejects cohorts below 25 |

## Verified final release custody

- PR #16 merged the serving application into public `main` as
  `03ec8f12fc23d265c89b462a345a5b599a6411e8`.
- Cloud Run revision: `driftline-00305-xln` at 100% traffic.
- Cloud Build: `c01bec2e-a950-407c-873b-b1d4fdc6bae6`.
- Image digest: `sha256:fca505ce56c6bd933f9cde8d55ff1e4ea7f9cad099d6fe39e8bb8321c96ea6d3`.
- GitHub Verify Driftline run `32923233214`: backend, frontend, standalone
  image, dependency audit, and repository hygiene all passed.
- `release_and_verify.sh` and a fresh desktop/mobile browser journey both passed
  on the same serving application SHA; the browser console was clean. Later
  `main` commits contain submission documents/media and do not change runtime.

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

## Unreleased public-main candidate custody

Public `main` now contains the PM-authored two-metric operating contract,
bounded internal allocation, real-measurement follow-up, opaque return link,
review-window lock, progressive custom-decision intake, clean-checkout API
routing, explicit retry recovery, tenant-bound agent tools, read-only shared
links, fair anonymous mutation quotas, bounded visual-asset fetches, the
continuous PM operating loop, and the redacted multi-source evidence pack
described in the judge scorecard. These merged runtime changes are not deployed.

The public-main candidate passed 525 backend tests, Ruff, the 14/14 trace
evaluation, the locked frontend build, dependency audit, frontend and
submission contracts, and shell/diff hygiene on August 26. PRs #23-#29 passed
all four hosted jobs. For PRs #26-#29, each tested tree was identical to its
squash-merged `main` tree, and the exact public-main release preflight passed
from a clean checkout at `08e7be09551aa833efd5ed93018cb6c32a8b3886`.
PR #32 then combined a manual exact-SHA verification trigger with the
research-backed real-PM market-fit record. Its exact head passed all four hosted
jobs, its squash-merged tree was identical, and the fresh exact public-main
preflight passed at `e4a2f474002c151ab29b08528915292543afd7f2` with 524 tests.
PR #33 refreshed the mirrored judge evidence against that tested state. Its
exact head passed all four hosted jobs, its squash-merged tree was identical,
and a new clean release-candidate preflight plus hosted run `32986603518` passed
at public-main SHA `484e764760c06350733189246a17dfa651502891`.

PRs #27-#29 also add a fail-closed external release renderer. It requires exact
repository/deployment/health identity, verifies the actual final MP4 and SRT,
binds the gallery to a same-session proof video, produces a timestamp review
sheet, and emits the complete packet outside the repository. It has correctly
rejected both non-canonical local capture identity and a rehearsal carrying a
red custody watermark. This proves the release controls, not a new deployment
or a public video.
That is repository and local candidate evidence only.
`scripts/verify_release_candidate_local.sh --release-candidate` now fails before
any Cloud mutation unless the tree is clean and its exact `HEAD` equals the
public `origin/main` tip. The gate passes; Cloud release remains intentionally
withheld because publication has not been authorized.

## Definition of done for the remaining work

1. One current-candidate hosted signed Jira create/reuse/reverse proof —
   **complete** for the isolated `driftline-demo` tenant. The current proof is
   preserved in `docs/INTERNAL_PILOT_2026-08-23.md` and the resource inventory.
2. One small, real operator pilot with aggregate before/after measurements.
3. Immutable Decision Twin baseline deployment, BigQuery provisioning, CI, and
   production verification scripts — **complete** at the serving release above.
4. The public-main candidate has complete local and hosted automated proof. Its
   immutable Cloud release, live API/browser proof, and final entrant-owned
   video remain **open** pending explicit publication approval.
5. Freeze scope, run real PM validation, record the demo, and submit. No additional connector or UI
   feature work after these gates unless a gate fails.
