# Driftline

Driftline is a change-to-action agent for Product Marketing and adjacent
operators. It monitors explicitly allowlisted public signals — own pricing and
terms plus competitor pricing, offerings, and product narratives — verifies a
material change, maps the affected offering and downstream work surfaces, and
pauses when a consequential human decision is required. The hosted service has
two explicit lanes: the anonymous judge console is packet-safe, while the
Google-OIDC tenant operator lane uses the same durable Firestore workflow to
execute least-privilege, idempotent, reversible connector actions. This is a
real deployed control plane with a deliberately safe public surface, not a
claim that an unauthenticated visitor can mutate a customer's systems.

The demonstration models a pricing-page change from unlimited audit-log
retention to 365-day retention, then traces the impact into a pricing
battlecard, renewal playbook, enterprise FAQ, and CRM guidance. The console can
also run bounded scenarios for competitor pricing, competitor capabilities,
and competitor product blogs. Each scenario shows an offering impact graph,
business domains, owners, work surfaces, and prepared handoffs. The deployed
source adapter fetches explicitly registered public snapshots. Judge fixtures
remain pinned and deterministic; a signed operator can onboard additional
exact HTTPS HTML/text/RSS URLs through `/api/operator/sources`, with redirects,
query credentials, private DNS-resolved addresses, and bodies over 128KB
rejected. It is not connected to a real company system.

In production source mode, onboarding performs one bounded read immediately and
returns either `baseline_established` or an explicit fetch failure; the durable
scheduler then owns recurring observations and retry behavior. Local and public
synthetic demo modes stay metadata-only for deterministic evaluation.

## Why it is agentic

Driftline is a complete resumable workflow rather than a chat interface:

1. Monitor source snapshots and detect semantic changes across own and competitor surfaces.
2. Verify the evidence and classify its operational risk.
3. Map the change to downstream artifacts and owners.
4. Draft bounded updates with evidence attached.
5. Interrupt the workflow for high-risk human decisions.
6. Resume from the decision and create a reversible packet, owner-review item,
   or queued item for each artifact.
7. Let a named human claim and complete each bounded owner action, with
   idempotency keys and evidence hashes carried through the lifecycle.
8. Prepare reversible, target-specific handoff packets for Product Marketing's
   Jira, Confluence, Slack, or GitHub workflow. Only the separately
   authenticated signed-operator lane may write through an explicitly enabled,
   scoped connector; the public demo is packet-only.
9. Preserve an auditable event trail for every action.

The decision surface is intentionally richer than a single model answer. The
Evidence-bound Decision Copilot presents two or three cited options with
tradeoffs, affected artifacts, and rollback plans; an independent deterministic
red-team reviewer blocks unsupported, over-broad, or non-reversible options.
The console also compares allowlisted pricing visuals with Gemini vision,
previews approve/grandfather/defer counterfactuals without writes, and keeps an
append-only change genome of recurring source transitions and unresolved work.

If a reviewer changes an artifact route after selecting a copilot option,
Driftline keeps the original option ID and records an explicit override reason.
The API rechecks the reviewed workflow decision, requires a complete route for
every mapped artifact, rejects unknown actions, and prevents high-risk work
from being silently queued. The approval record and audit event distinguish a
copilot recommendation from a deliberate human adjustment.

### The utility wedge: a Change Card, not an alert

Every verified signal becomes a deterministic **Change Card**. It answers four
operator questions in one place: what changed (hash-bound before/after
evidence), why it matters now (materiality and decision window), which role
owns the next move (PMM, Sales/RevOps, Product, CS, Support, or Legal), and
whether the resulting work actually closed. The card produces role-specific
packets from one evidence set and carries the same evidence hash into action
items and rollback markers. Approved owner actions receive deterministic,
risk-based due dates and priority so the queue measures overdue work instead of
stopping at “packet created.” In the synthetic demo, CRM opportunity and renewal
counts are intentionally shown as unavailable; once a permissioned Salesforce
read-only connection is verified, those fields can be populated without
changing the policy gate or exposing raw records to the public console.
Each verified source transition also receives a stable Change Card identity
derived from its allowlisted source and evidence hash. Re-running the same
snapshot therefore reuses the same action/idempotency identity instead of
creating duplicate downstream work.

The product deliberately measures operational proof rather than inventing ROI:
workflow throughput, approval latency, source observations, owner-action
completion, reversals, and source health are observable at
`/api/ops/value-proof`. Hours saved, revenue lift, retention impact, and
willingness-to-pay remain `not_measured` until a real pilot supplies aggregate
before/after evidence. See
[`docs/UTILITY_RESEARCH_2026-08-20.md`](docs/UTILITY_RESEARCH_2026-08-20.md)
for the research-backed scope and deferred work. The public console's **Value
proof** panel reads the same bounded endpoint, making observed deployment
utility and unmeasured customer outcomes visible without turning synthetic
activity into a business claim.

For an authenticated operator, `POST /api/connectors/context/summary` adds a
bounded internal-workload view before approval: fixed-scope Jira, Confluence,
Slack, and GitHub connectors return aggregate counts only. It is signed-only,
request-scoped, and never exposes source text or private records to the public
console. Unconfigured integrations remain explicitly `prepared_only`;
Salesforce is a read-only OAuth lane pending real tenant consent, and its
refresh token follows the same deterministic tenant binding
(`driftline-tenant-<tenant>-salesforce`) after the callback.
The latest deployed signed probe returned HTTP 200 for all four configured
connectors (Jira 18 sampled issues, Confluence 5 pages, Slack 27 recent
messages, GitHub 0 open issues/0 open pull requests) with aggregate-only
redaction; this is live runtime-read evidence, not a customer-pilot outcome.

External connector credentials are tenant-bound. An owner provisions the
deterministic Secret Manager secret and activates its metadata-only binding via
`POST /api/connectors/{connector}/binding`; signed workflow actions then read
only that tenant's secret. Global connector secrets are disabled in the hosted
runtime, and `GET /api/connectors/bindings` never returns credential values.
For SaaS-style onboarding, an owner can start a 15-minute, secret-free handoff
with `POST /api/connectors/{connector}/credential-enrollment`. Driftline returns
only the tenant-scoped secret reference and an explicit operation scope. New
enrollments default to the concrete `read_context` scope only; write and
reversal scopes are requested explicitly by the corresponding adapter. After
infrastructure adds
the provider version out of band, the owner completes the session at
`POST /api/connectors/{connector}/credential-enrollment/{id}/complete`; the
runtime verifies the secret, pins its version, activates the binding, and marks
the enrollment complete. Expired sessions fail closed, and both lifecycle
events are append-only metadata with no token values.
If an older binding omits `allowed_operations`, resolution also fails closed to
`read_context`; it never silently authorizes a downstream write.
Tenant and role metadata is durable in the isolated Firestore control plane;
signed `GET /api/tenants` exposes only the caller's tenant, while the
owner-only `GET /api/tenants/members` route exposes role metadata without
tokens. Owners can provision or update role metadata with
`POST /api/tenants/members`; unprovisioned OIDC identities fail closed instead
of inheriting the default tenant. `GET /api/tenants/available` is the
identity-only tenant switcher contract: it lists only the authenticated Google
identity's active memberships, implicitly selects a single tenant, and
requires an explicit tenant selector when the identity belongs to more than
one. Tenant control-plane records are retained
until explicit deprovisioning rather than expiring with content records. An
owner can soft-deprovision a tenant through `POST /api/tenants/deprovision`
with an exact tenant-ID confirmation; this disables memberships and revokes
bindings while preserving metadata for audit. Secret deletion and
provider-token revocation remain explicit infrastructure offboarding steps.
Owner-managed `POST /api/connectors/{connector}/profile` stores only
connector-specific non-secret targets in the durable
`driftline_tenant_connector_profiles` collection. Adapters prefer those
profiles and validate every URL and destination. The older operator-owned
`DRIFTLINE_TENANT_CONNECTOR_CONFIG` profile is local-development compatibility
only; hosted Firestore signed requests fail closed until a durable tenant
profile exists. Credentials still resolve only from the deterministic tenant
Secret Manager binding. Salesforce health also requires an active tenant
binding, not just an OAuth client configuration. The current demo deployment
has one verified tenant;
a second tenant has not been provisioned or live-verified.

Signals do not have to become work. A named reviewer can dismiss a
needs-approval signal as non-material with a required reason; Driftline records
that intentional no-op in the workflow, Change Card, packet, and append-only
audit trail without creating packets, owner tasks, or connector writes. This
keeps monitoring useful when a source changes but the business decision is
“not for us right now,” instead of silently losing the rationale.

The Google ADK coordinator is configured for the Gemini 3.5 Flash model and a
strictly allowlisted read/inspect tool set for reasoning. A second ADK task
performs structured, evidence-hash-bound impact analysis; its JSON is validated
again by Driftline before it can replace draft artifacts. Cloud Tasks starts
the live run asynchronously, so the browser is not holding a model request
open. A separate deterministic API gate owns high-risk approval; the model is
not given an approval tool. Before source text reaches the coordinator,
structured analyst, decision copilot, or Gemini vision lane, Driftline creates
a bounded model-visible copy, removes instruction-like lines and control
characters, and labels the remaining text as quoted untrusted evidence. Raw
evidence stays unchanged for hashes, audit, and the UI. This is a deterministic
local guardrail, not a claim that Google Model Armor is configured. Cloud
Scheduler runs the historical monitor every
six hours and records `baseline_established`, `unchanged`, or `changed` in a
Firestore snapshot ledger. Cloud Run serves the API and web console in one
container, with Firestore as the durable workflow, job, source-history, and
audit store. Approved public-demo packets, one approved operational output, and
undo markers are also persisted as private, versioned Cloud Storage objects in
the isolated project. The
synthetic replay remains available for predictable judging. If a real Gemini
turn is temporarily quota-limited, only the anonymous synthetic judge lane
falls back to a clearly labelled deterministic replay; signed tenant and
monitor runs remain fail-closed. Cloud Scheduler
fans out one bounded monitor job per registered source (or a single canary when
`source_id` is supplied), capped by `DRIFTLINE_MONITOR_MAX_SOURCES`; each source
is still constrained by the same allowlist and ADK tool policy. The operator
console exposes `/api/monitor/registry` freshness state and `/api/ops/summary`
runtime/connector guardrails without exposing credentials. Both live and
identity-free public-demo mutations are query-capped and rate-limited to bound
demo spend. Public Gemini visual analysis is also capped at 10 calls per hour
and returns a retry hint when the window is exhausted. Signed agent calls and workflow mutations use separate per-tenant
budgets, so one tenant cannot consume another tenant's allowance. The signed
`GET /api/tenants/usage` endpoint also records durable monthly aggregates for
agent calls, workflow mutations, connector reads, and monitor jobs in Firestore. This is
control-plane metering for quota and pilot evidence only: billing is disabled,
content is not included, and the deployment still does not claim a hosted
subscription system.

For an authenticated pilot or connector rehearsal, `POST /api/jobs/demo` also
accepts `run_mode=tenant_demo`. This mode requires the tenant's signed operator
identity, uses only one of the five pinned fixtures, runs the real ADK/Gemini
coordinator, and labels the resulting Firestore workflow
`synthetic_tenant_demo`. It then follows the normal deterministic approval,
connector-write, and undo gates. It is a bounded pilot replay—not a claim that
the fixture is a customer's live source.

Tenant owners can read and tune bounded per-tenant allowances without a
redeploy through signed `GET/POST /api/tenants/policy`. The policy covers agent
calls, workflow mutations, connector reads, and `retention_days` for tenant-owned
source observations, workflow/job, failure, outcome, and credential-access
metadata. External connector context and health reads consume the connector
allowance.
Every field is clamped to a safe range and policy changes are metadata-only
audit history. Missing policy
metadata falls back to deployment defaults; a quota lookup failure fails
closed, while a retention lookup failure uses the bounded deployment default.
This is a real tenant control-plane privacy/quota policy, not a billing or
subscription claim.

Cloud Tasks retries failed jobs at most three times. A terminal failure also
creates a tenant-filtered metadata marker in `driftline_job_failures`, visible
to signed operators at `/api/ops/job-failures`; the marker contains no prompt,
source body, exception text, or credential and expires with the deployment
default or the tenant's bounded retention policy. The public console never exposes another tenant's failure
count.

The direct `POST /api/agent/run` route has an explicit two-lane contract. The
anonymous judge request is tenantless, limited to an allowlisted source, and
replaced with a fixed safe instruction so caller text never becomes a public
Gemini prompt or durable ledger field. A real operator can add `operator`,
`tenant_id`, and a Google OIDC approval token; Driftline then verifies
the principal, reserves that tenant's agent quota, and preserves the operator's
query in the signed tenant workflow. Partial identity or unallowlisted-source
requests fail before a model call.
In the Firestore deployment, signed tenant reservations use a transactional
window counter so concurrent Cloud Run instances cannot race past the same
limit; local development uses a process-local fallback.
Google OIDC is required for hosted operators. The deterministic
`driftline-tenant-operator-<tenant>` signer remains available only for explicit
local/bootstrap break-glass use; the hosted deployment rejects it.
The hosted runtime also checks the durable Firestore tenant directory, so an
active, provisioned tenant can be admitted without editing a deployment-wide
allowlist; disabled or unreadable tenant records fail closed.
Platform operators can bootstrap or reactivate tenant metadata through the
OIDC-only `POST /api/platform/tenants` route. It returns deterministic
Secret Manager references and owner metadata, never credential values; the
provider secrets still have to be created and populated out of band.

Operator source onboarding is a separate signed lane: it persists one exact
public URL in the isolated Firestore registry, then the bounded scheduler can
monitor it alongside the fixtures. Custom source definitions and snapshot
history are tenant-scoped; the public console exposes only the five pinned
fixtures. The internal scheduler carries each source's tenant ID into its
bounded monitor job. It is an allowlist of sources, not an arbitrary web
crawler.

Connector bindings have an explicit owner-only lifecycle: a binding is
activated only after the deterministic tenant Secret Manager secret exists, and
`POST /api/connectors/{connector}/binding/revoke` can disable it without
returning or deleting the secret. Connector resolution fails closed until a
replacement secret version is provisioned and the owner re-verifies the
binding. `POST /api/connectors/{connector}/binding/rotate` starts an audited
rotation, moves the binding to `rotation_pending`, and fails connector
resolution closed until that replacement version is verified. Activation,
rotation, and revocation append metadata-only records readable from the signed
`/api/tenants/audit` route; lifecycle records never contain the credential
value. Active bindings pin the concrete Secret Manager version resolved during
verification, so a later provider-token update cannot silently change a live
tenant. Bindings are stored canonically below the tenant document at
`driftline_tenants/{tenant}/credentials/{connector}` and carry a versioned
namespace record naming the exact project Secret Manager resource and tenant
service identity. The legacy flat collection is a migration artifact only;
hosted strict mode does not write or read it unless an operator explicitly
enables a short-lived compatibility window;
`scripts/migrate_tenant_credential_bindings.py` backfills this metadata without
reading or changing a credential value. The hosted runtime also derives a
collision-resistant per-tenant Google service identity and impersonates it for
Secret Manager access. The shared
Cloud Run identity has only narrowly scoped `Service Account Token Creator`
access to each tenant identity; each tenant identity can read only its own
deterministic secrets and can add Salesforce refresh-token versions only on
that tenant's Salesforce secret. This is a real tenant credential data-plane
foundation for this deployment, while customer-managed KMS keys, self-serve SSO, billing,
and per-tenant compute remain outside the hackathon release.
At runtime, adapters resolve credentials through one tenant credential broker:
the caller supplies only tenant, connector, and an allowlisted operation. The
broker rejects cross-tenant secret references, revoked/rotating bindings, and
unapproved operations, then reads the pinned Secret Manager version into a
short-lived in-process lease. It appends metadata-only lease records to
`driftline_credential_access_events`; values and provider response bodies never
enter the ledger. Hosted leases read through the derived tenant service identity
when `DRIFTLINE_TENANT_SECRET_IDENTITY_MODE=impersonated`; direct shared-runtime
secret reads are reserved for local compatibility. Signed owners can inspect the redacted inventory at
`/api/connectors/credentials` and access trail at
`/api/connectors/credentials/access`. This closes the runtime credential seam
for multiple tenants while leaving customer-managed encryption keys,
self-serve SSO/billing, and per-tenant worker IAM as explicit future SaaS
layers rather than implied functionality.
The signed `GET /api/connectors/bindings/health` probe reconciles every fixed
connector namespace against the exact Secret Manager binding and reports
`healthy`, `attention`, or `not_configured` without returning credential
values. This catches deleted, unreadable, mismatched, or mid-rotation secrets
before a downstream action is attempted.
Connector destination profiles are also constrained to HTTPS provider host
allowlists (Atlassian, Slack, GitHub, and Salesforce) and reject userinfo,
query credentials, fragments, and untrusted hosts before persistence or use.

The research notes reference public material from vendors such as Crayon,
Kompyte, and Visualping as examples of competitive-intelligence workflows.
Those pages are not registered live sources in this deployment. The deployed
registry currently contains only the five pinned fixtures above; a tenant
operator must explicitly register any additional exact HTTPS source. Driftline
does not claim that a vendor page change is ground truth for a customer's
product.

### Verified Jira connector

The isolated deployment includes one real, bounded Jira connector for the free
`Driftline` Team-managed project (`KAN`). It is restricted to the Atlassian
Jira gateway for this site and uses a Jira-scoped token with the classic
`read:jira-work`, `read:jira-user`, and `write:jira-work` scopes. Hosted
connector calls resolve only the tenant-bound Secret Manager binding
`driftline-tenant-driftline-demo-jira`; the older deployment-wide secret is
retained only for recoverable cleanup and is not mounted. No token is ever sent
to the browser or committed to this repository.

After a signed operator approves a packet, the adapter searches the current
project for a Driftline action marker before creating one `Task`. A public demo
approval cannot invoke this path, even when credentials are present. Undo is
reversible: it keeps the issue, removes only the Driftline active label, adds
`driftline-reversed`, and appends an audit comment. Confluence, Slack, and
GitHub use the same real adapter boundary, with Secret Manager-or-environment
credential resolution, HTTPS and scope validation, marker-based idempotency, and
reversible markers. GitHub is authenticated for the isolated `mikeyerke/driftline`
repository and was directly verified by creating and reversing issue #1. Slack is
authenticated for the isolated free `Driftline` workspace and `#new-channel`; the
bot has only `channels:history` and `chat:write` and is added only to that channel.
Confluence is provisioned on the free plan in the dedicated `DRIFT` space and is
authenticated through the Atlassian API gateway with a Confluence-scoped token.
Each connector can be enabled independently with its own project, space, channel,
or repository scope; a failed connector is recorded as `failed` and never turns
into a successful claim. Tenant-bound asynchronous jobs, workflows, packets,
action items, scenario previews, and operator summaries are filtered by the
same signed identity boundary; the public demo sees only tenantless synthetic
records and sends only a fixed allowlisted instruction to Gemini rather than
persisting arbitrary visitor text. Claim, complete, fail, retry, and reverse action-item calls use that
same boundary for tenant-bound workflows. Salesforce now has a deployed
read-only OAuth lane,
tenant-scoped Secret Manager storage, and an allowlist for product, pricebook,
and opportunity objects. It has no write path and remains disabled until a
real Salesforce org authorizes the isolated tenant. See
`docs/SALESFORCE_RUNBOOK.md` and `docs/CONNECTOR_SECURITY.md` for setup and
lane boundaries.

Pilot measurement is deliberately separate from synthetic demo telemetry. See
`docs/PILOT_PLAN.md` and the executable [`docs/PILOT_PACKET.md`](docs/PILOT_PACKET.md);
until real teams contribute aggregate evidence, Driftline
continues to report ROI, revenue, retention, and willingness-to-pay as
`not_measured`. Once signed records exist, tenant owners can use
`GET /api/ops/pilot-report` for a tenant-filtered, aggregate before/after delta;
the report remains `operator_reported_unverified` until its evidence is
reviewed.

| Connector | Enable flag | Required scope |
| --- | --- | --- |
| Jira | `DRIFTLINE_JIRA_ENABLED=true` | one Atlassian site/project |
| Confluence | `DRIFTLINE_CONFLUENCE_ENABLED=true` | one Atlassian space and optional parent page |
| Slack | `DRIFTLINE_SLACK_ENABLED=true` | one channel |
| GitHub | `DRIFTLINE_GITHUB_ENABLED=true` | one owner/repository |
| Salesforce context | `DRIFTLINE_SALESFORCE_ENABLED=true` | read-only OAuth context; no write path |

Every connector returns an explicit per-system status (`created`, `reused`,
`reversed`, `prepared_only`, `not_configured`, `not_eligible`,
`invalid_config`, or `failed`) in the action record.

## Repository layout

~~~text
frontend/        React + Vite operational console
backend/         FastAPI, Google ADK agent, and workflow engine
docs/            architecture, contest rules, inventory, and visual concepts
submission/      Devpost copy and four-minute demo script
~~~

## Run locally

### Frontend

~~~bash
cd frontend
npm install
npm run dev
~~~

### Backend

~~~bash
cd backend
uv sync --extra dev
uv run uvicorn app.api:app --reload --port 8080
~~~

Copy backend/.env.example to backend/.env and provide a Google Cloud project
when enabling the live Gemini path. Synthetic demo mode is the default.

## Test

~~~bash
cd frontend && npm run build
cd ../backend && uv run --extra dev pytest
~~~

The verified local suite also runs Ruff lint and format checks. If uv is not
installed, a standard Python virtual environment with the dependencies in
backend/pyproject.toml produces the same test result.

Every push to `main` and every pull request runs the backend lint/tests and
locked frontend production build in GitHub Actions. The workflow has
read-only repository permissions, does not require cloud credentials, and does
not deploy; deployment remains an explicit Cloud Build operation after the
verification gates pass.
Dependabot monitors the backend lockfile, frontend lockfile, and GitHub Actions
for reviewable weekly update PRs.

## Deploy to Google Cloud

The contest deployment is isolated in the driftline-hackathon-2026 project.
Create the dedicated resources and review docs/RESOURCE_INVENTORY.md before
submitting the included build:

~~~bash
gcloud config set project driftline-hackathon-2026
./scripts/deploy.sh
~~~

The root Dockerfile builds the React console and serves it from FastAPI. Cloud
Run uses the dedicated runtime service account for Vertex AI and Firestore; no
API key is embedded in the client. The production image installs the frozen
`backend/uv.lock` resolution with pinned `uv==0.8.17`; dependency ranges in
`pyproject.toml` cannot silently change a deployed build. Verify the lockfile
before a release with `uv lock --check --directory backend`. The deployment
script refuses any active project other than `driftline-hackathon-2026` and
explicitly selects the isolated `driftline-build` Cloud Build service account;
it never falls back to the default Compute service account. The checked-in
`.gcloudignore` also excludes credentials, local environments, dependency
trees, generated bundles, and screenshots from the uploaded build context.

## Public links

- Live demo: https://driftline-xvxczqg62a-uc.a.run.app/
- GitHub: https://github.com/mikeyerke/driftline
- Demo video: held while the product is being pressure-tested; do not submit this draft yet
- Architecture: https://github.com/mikeyerke/driftline/blob/main/docs/architecture.md
- Verified rules: https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md
- Cloud inventory: https://github.com/mikeyerke/driftline/blob/main/docs/RESOURCE_INVENTORY.md
- Pilot packet: https://github.com/mikeyerke/driftline/blob/main/docs/PILOT_PACKET.md

## Reproducible verification

~~~bash
BASE=https://driftline-xvxczqg62a-uc.a.run.app
curl -fsS "$BASE/health"
JOB=$(curl -fsS -X POST "$BASE/api/jobs/demo" -H 'content-type: application/json')
JOB_ID=$(printf '%s' "$JOB" | jq -r .job_id)
curl -fsS "$BASE/api/jobs/$JOB_ID"
~~~

The final release evidence in `docs/RESOURCE_INVENTORY.md` records the exact
Cloud Run revision, async job result, browser smoke test, Firestore documents,
and Cloud Run logs. A live ADK response is only claimed when those fields have
been observed directly; the identity-free deterministic `/api/workflows/demo`
endpoint is the fallback for evaluation.

## Safety model

- Synthetic or explicitly approved public data only in the demonstration.
- Every detected change carries hash-bound source evidence.
- High-risk actions stop at a human approval gate.
- Tools are allowlisted and the demonstration state transitions are bounded.
- The model proposes actions; deterministic policy code decides whether a
  bounded packet may be created.
- Generated packets explicitly state that no customer-facing system changed;
  the one verified Jira connector is limited to the isolated Driftline project.
- Approval publishes one low-risk, evidence-bound operational output into the
  isolated Driftline Cloud Storage lane. Approval may also create one
  project-scoped Jira Task after the deterministic gate; undo preserves the
  original object, reverses the Jira-owned labels, and writes durable markers.
- The public console remains identity-free for judging. The signed operator
  lane additionally accepts a Google OIDC token for the allowlisted operator
  email, so configured writes and source onboarding have verifiable identity.
- No real Salesforce, CRM, billing, customer, or private company data is used.

## Cost and isolation

The deployment is isolated in the new `driftline-hackathon-2026` Google Cloud
project. Cloud Run is configured with zero minimum instances and a revision
maximum of one instance. Cloud Tasks is limited to one concurrent dispatch and 0.2
dispatches per second. A $10 monthly billing budget is filtered to this project with
25%, 50%, 75%, 90%, and 100% current-spend thresholds. The Google Cloud free
trial started 2026-08-18 and ends 2026-11-17; the full paid-account activation
control is intentionally not enabled. See `docs/RESOURCE_INVENTORY.md` for
the complete cleanup inventory and exact image digest.
