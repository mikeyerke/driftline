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

For the fastest rubric-aligned review, see the [judge scorecard](submission/JUDGE_SCORECARD.md):
it maps the official 40/30/30 judging weights to the live journey, architecture,
and reproducible release checks.

The release also carries a fail-closed [trace-to-eval quality gate](docs/TRACE_EVAL.md):
the same bounded agent trace is scored for human gating, tool/evidence safety,
rollback, artifact coverage, decision usefulness, and audit provenance. CI blocks
critical safety regressions, and the deployed verifier persists a redacted live
report with a trend against the previous run. These are evaluation metrics, not
customer ROI or willingness-to-pay claims.

The default demonstration models a competitor price change from $49 to $59 per
seat per month, then traces the impact into a comparison map, pricing
battlecard, deal-desk guidance, and executive brief. The console can also run
bounded scenarios for own pricing and terms, competitor capabilities, and
competitor product blogs. Each scenario shows an offering impact graph, business
domains, owners, work surfaces, and prepared handoffs. The deployed
source adapter fetches explicitly registered public snapshots. Judge fixtures
remain pinned and deterministic; a signed operator can onboard additional
exact HTTPS HTML/text/RSS URLs through `/api/operator/sources`, with redirects,
query credentials, private DNS-resolved addresses, and bodies over 128KB
rejected. The anonymous judge lane is not connected to a customer's company
system; the separately authenticated tenant lane can use the configured
least-privilege connectors described below.

In production source mode, onboarding performs one bounded read immediately and
returns either `baseline_established` or an explicit fetch failure; the durable
scheduler then owns recurring observations and retry behavior. Local and public
synthetic demo modes stay metadata-only for deterministic evaluation.

The authenticated console uses the same production monitor lane for a registered
URL: after onboarding, selecting that source and pressing **Run scan** queues a
tenant-bound `monitor` job rather than the synthetic fixture lane. A registered
source therefore follows the real fetch, append-only baseline, ADK analysis, and
approval path from the product UI; pinned fixtures remain available separately
for deterministic judging. The onboarding form supports bounded HTML, plain
text, and RSS/Atom parsers and selects the newly registered source for the next
scan automatically.

Every scheduled monitor job also carries the exact registered source ID through
the durable job record, ADK turn, and append-only observation ledger.

Signed tenant operators can also pause and resume a registered source without
deleting its history. The lifecycle route requires a bounded reason, writes the
durable source state before returning, appends `source_paused` or
`source_resumed` audit metadata, and makes the scheduler skip paused sources.
The anonymous fixture lane remains immutable and continues to expose exactly
five public sources. The browser shows the pause reason and disables **Run
scan** while a custom source is paused; a fresh Google-OIDC identity is still
required for the live operator proof.

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
   scoped connector; the public evaluation lane is packet-safe.
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

### Operator access

The hosted console exposes the production operator lane directly. Choose
**Sign in with Google** to obtain a short-lived ID token in memory; Driftline
discovers only the active tenant memberships attached to that Google identity.
Selecting a tenant switches scans, approvals, action-item updates, and undo to
the same tenant-scoped OIDC boundary used by the API. The token is sent only in
an `Authorization` header, never duplicated into JSON or URLs; the browser
never sees a connector credential, stores the ID token, or receives raw
connector data. A logged-out visitor remains on the packet-safe public lane.

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
completion, owner-action cycle time, reversals, and source health are observable at
`/api/ops/value-proof`. Hours saved, revenue lift, retention impact, and
willingness-to-pay remain `not_measured` until a real pilot supplies aggregate
before/after evidence. See
[`docs/UTILITY_RESEARCH_2026-08-20.md`](docs/UTILITY_RESEARCH_2026-08-20.md)
for the research-backed scope and deferred work. The public console's **Value
proof** panel reads the same bounded endpoint, making observed deployment
utility and unmeasured customer outcomes visible without turning synthetic
activity into a business claim.

Authenticated tenant operators also get a bounded **Pilot measurement** panel
for recording aggregate before/after minutes and optional outcome evidence.
These records remain explicitly operator-reported and unverified until
reviewed; Driftline never accepts customer names, raw notes, or CRM records in
this lane.

For an authenticated operator, `POST /api/connectors/context/summary` adds a
bounded internal-workload view before approval: fixed-scope Jira, Confluence,
Slack, GitHub, and (after tenant OAuth) Salesforce connectors return aggregate
counts only. It is signed-only, request-scoped, and never exposes source text,
CRM records, or private credentials to the public console. A signed `live`,
`tenant_demo`, or `monitor` run can attach the same normalized aggregate result
to its Change Card, where the UI shows the verified connector count and the
workflow records an `internal_context_reader` audit event. Anonymous demo runs
never attach connector context. The authenticated console exposes the summary
as a deliberate **Refresh context** control beside the handoff destinations, so
an operator can verify connector health and aggregate workload before choosing
an action. Unconfigured integrations remain explicitly
`prepared_only`; Salesforce is shown as `not_configured` with
`authorization_required=true` until the tenant completes consent. After the
callback, Salesforce uses the same deterministic tenant binding
(`driftline-tenant-<tenant>-salesforce`) and contributes only allowlisted object
counts/field names. The owner-completed callback has been verified to persist a
read-only connection record, tenant-scoped Secret Manager pointer, and the
impersonated credential path. If Salesforce rejects the stored refresh token,
the health endpoint returns an explicit `reauthorization_required` state (not a
generic application outage) and the UI links directly back to owner consent.
Until a fresh probe returns object totals, no live CRM read is claimed here.
Jira,
Confluence, Slack, and GitHub remain aggregate-only connector evidence, not
customer-pilot outcomes.

The latest signed context read (2026-08-22 UTC) verified `18` open Jira issues,
`7` Confluence pages, `38` recent Slack messages, and `0` GitHub issues / PRs
for the isolated Driftline tenant. Salesforce remained explicitly
reauthorization-gated after its stored refresh token was rejected; no CRM
totals are inferred from that state.
The same authenticated console also completed a signed tenant scan from the
pinned `competitor/pricing` fixture; Firestore recorded job
`job-a33d07ac658c` / workflow `75da1f00-e657-4ba3-bba6-80c298b747be` at the
human approval gate with Google ADK + Gemini 3.5 Flash. No approval or external
write was attempted.

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
Firestore snapshot ledger. Each source's observation cadence is distinct from
its freshness SLA: the scheduler only spends a model call when the cadence is
due (or a baseline/failure needs recovery), then round-robins due tenant
buckets so one large registry cannot starve another tenant. Deferred sources
return their next due time and reason in the scheduler response. Cloud Run serves the API and web console in one
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
is still constrained by the same allowlist and ADK tool policy. Scheduler
delivery is at-least-once, so Driftline checks the in-flight durable job ledger
before enqueueing and reports deduplicated sources instead of launching a
second model call. The operator
console exposes `/api/monitor/registry` freshness state and `/api/ops/summary`
runtime/connector guardrails without exposing credentials. Both live and
identity-free public-demo mutations are query-capped and rate-limited to bound
demo spend. The shared public Gemini scan lane is capped at 20 calls per hour,
separately from the signed tenant allowance, so evaluator traffic cannot starve
an authenticated pilot. Public Gemini visual analysis is also capped at 10
calls per hour and returns a retry hint when the window is exhausted. Signed
agent calls and workflow mutations use separate per-tenant
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
count. A signed tenant operator can retry a terminally failed tenant job from
Run history through `POST /api/jobs/{job_id}/retry`; the endpoint preserves the
original source, query, tenant, and run mode, checks the source allowlist again,
and records `retry_of` so concurrent requests return one durable successor
instead of creating duplicate model work. Public/demo jobs remain rerunnable
only through the packet-safe public scan control.

The direct `POST /api/agent/run` route has an explicit two-lane contract. The
anonymous judge request is tenantless, limited to an allowlisted source, and
replaced with a fixed safe instruction so caller text never becomes a public
Gemini prompt or durable ledger field. A real operator can add `operator`,
`tenant_id`, and a Google OIDC approval token; Driftline then verifies
the principal, reserves that tenant's agent quota, and preserves the operator's
query in the signed tenant workflow. Partial identity or unallowlisted-source
requests fail before a model call.
The signed direct path resolves operator-registered public URLs inside the
authenticated tenant boundary as well as pinned fixtures; anonymous callers
cannot discover or execute those tenant sources.
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
bounded monitor job. A source that changes between scheduled reads creates a
new hash-bound Firestore observation and a tenant workflow; an unchanged source
advances source health without manufacturing an incident. It is an allowlist
of sources, not an arbitrary web crawler.

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
registry contains the five pinned fixtures above plus one verified
operator-registered own-product README source; a tenant operator must
explicitly register any additional exact HTTPS source. Driftline does not
claim that a vendor page change is ground truth for a customer's product.

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
project for a Driftline action marker before creating one `Task`. A public
evaluation-lane approval cannot invoke this path, even when credentials are
present. Undo is
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
same signed identity boundary; the public evaluation lane sees only tenantless synthetic
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

The verified local suite also runs Ruff lint and format checks. For dependency
security, run `./scripts/verify_dependencies.sh` with `uv` and `pip-audit`
installed; it exports the frozen backend lockfile and audits the complete
transitive resolution without changing application dependencies. The current
audit returned **No known vulnerabilities found**. If uv is not installed, a
standard Python virtual environment with the dependencies in
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
script refuses any active project other than `driftline-hackathon-2026`, refuses
a dirty or untracked release context, and explicitly selects the isolated
`driftline-build` Cloud Build service account;
it never falls back to the default Compute service account. The checked-in
`.gcloudignore` also excludes credentials, local environments, dependency
trees, generated bundles, and screenshots from the uploaded build context.

Cloud Build now has a post-deploy smoke gate: it requires 100% Cloud Run
traffic, verifies that the serving revision's image digest matches the exact
Artifact Registry image built for that Cloud Build, and verifies that the
public `/health` response carries the exact release SHA and build ID before
the build can succeed. The current serving release is source commit
`2bcd1fc0c86563a010364d202f9071dab5a1c52f`, Cloud Build
`17151a7f-5ccc-4639-b4d4-c3766b47ef5e`, and Cloud Run revision
`driftline-00198-gt8` at 100% traffic. Its immutable image digest is recorded
in [`docs/RESOURCE_INVENTORY.md`](docs/RESOURCE_INVENTORY.md).
The public `/health` probe reports the same full release SHA and Cloud Build ID,
so a reviewer can tie the serving revision to this exact repository commit.
GitHub Actions run `32565860581` passed the repository gates, including the
frozen dependency audit. This release adds
the explicit Salesforce `reauthorization_required` contract, durably records
bounded probe health so a rejected refresh token remains visible after reload,
and automatically refreshes metadata-only Salesforce status when the operator returns from the
consent tab, keeps the visible **Reauthorize read-only** recovery control, and
retains the tenant-scoped Secret Manager access path. The owner must still complete a fresh consent before a
live CRM read can be claimed; the Salesforce state is not silently relabeled
as proof by the fresh agent or approval/undo runs below. If a short-lived
Google operator ID token expires, a signed 401 now clears the in-memory tenant
session and returns the UI to an explicit sign-in-again state while preserving
the anonymous packet-safe lane; no token is persisted or copied into a body or
URL.
The latest console build also keeps the operator control in an explicit
loading state until `/api/auth/config` resolves, avoiding a false
"unavailable" flash on a cold production load.
The new trace-to-eval quality gate evaluates fourteen independent safety and
usefulness cases, including a critical aggregate-context boundary, persists
only a redacted report, and is checked against the live Google ADK/Gemini trace
before this release is considered healthy. The latest live report
`eval-4b79963dc5a8` remained stable against the prior report with 100% safety,
100% usefulness, 100% overall, and no case regressions; it is
evaluation telemetry, not a
customer-outcome claim.
The approval trace also records the deterministic red-team reviewer and
`red-team-v1` policy version, both bound to the current evidence hash; approval
rejects a missing, mismatched, or blocking policy review.
Direct live proofs on this exact revision verified Google ADK + Gemini 3.5
Flash, the allowlisted tool trace, the deterministic approval gate, persisted
packet/undo behavior, and the direct `/api/agent/run` path; the public lane
made no external connector writes. The impact map now exposes link counts,
focused evidence paths, and worklist handoffs, while the append-only source
registry visibly reports no-op checks as `unchanged`. The owner action queue
now filters all/open/closed work while keeping evidence hashes and idempotency
keys visible. Selecting a work-surface node in the map now scrolls to the
matching worklist row. At 1280px the map gets
the full control-plane width; a 390x844 check has no horizontal overflow. See
[`docs/RESOURCE_INVENTORY.md`](docs/RESOURCE_INVENTORY.md) for exact proof
identifiers and the remaining unmeasured customer outcomes.

This release also fixes source-context isolation in the public console: changing
the scenario selector invalidates in-flight polling, clears the prior workflow,
resets artifact decisions, and renders the selected source's own bounded
before/after preview until a new scan runs. A logged-out browser check verified
offering → blog switching after a completed workflow, with no stale live card or
approval state. Desktop and mobile Lighthouse both scored 100 across 53 audits,
with no console errors or horizontal overflow. The sidebar now reconciles deep
section navigation after deferred panels mount; a logged-out 500px browser
check landed all six navigation targets below the sticky header with one unique
Settings anchor and one unique deployment anchor.

The authenticated operator lane now preserves the short-lived Google token and
membership list when switching between permitted tenants. The selected tenant
changes without silently dropping into the anonymous packet-safe lane, and the
operator can switch back without re-authenticating. Crossing any identity
boundary (anonymous to signed-in, tenant to tenant, or signed-in to anonymous)
also clears the prior workflow, job, and artifact decisions before the new lane
starts, so a public packet cannot appear as tenant work.

The release proof also exercises the real background delivery path: Cloud
Scheduler sends an OIDC-authenticated HTTP 200 request to
`/api/scheduler/tick`, and cadence rules defer healthy sources that are not due.
Fresh repeatable proof identifiers on the current serving revision are
`job-48b697d7dfcd` / `d4d97a79-373f-4e19-87ef-6e0d5d25505f` for the live agent
and `job-53fcad9ed7e4` / `5742ef64-8863-4234-ba7b-efc6dead6907` for the paired
approval/undo run. The approval/undo path persisted and reversed the packet
with no external connector write. The prior job/workflow identifiers remain
in the append-only inventory as historical evidence.
`scripts/verify_production.sh` also passed with zero
recent Cloud Run errors. Artifact Registry retains the
newest ten images and the serving digest; older unreferenced builds were
removed from this isolated project. The signed browser client sends its
short-lived Google ID token only in the `Authorization` header, with a CI guard
against body or URL duplication. The Settings surface exposes the
tenant-scoped Salesforce read-only OAuth handoff, aggregate health probe, and
reauthorization recovery control. The owner-completed callback is persisted as
a read-only connection. When the stored refresh token is rejected, the current
release returns `reauthorization_required` rather than an application 503;
Driftline still does not claim a live CRM read until a fresh consent produces
object totals.

The cadence path was re-run against the same isolated deployment at
`2026-08-22T02:32:43Z`: the real Scheduler identity received an
OIDC-authenticated HTTP 200 on the new revision, and the registry reported
all five bounded sources healthy with no stale or failed entries. A post-deploy
log query found no Firestore positional-filter deprecation warning after the
FieldFilter fix. Sources not due at that moment were correctly deferred to
their cadence deadlines.

## Public links

- Live demo: https://driftline-xvxczqg62a-uc.a.run.app/
- GitHub: https://github.com/mikeyerke/driftline
- Demo video: held while the product is being pressure-tested; do not submit this draft yet
- Architecture: https://github.com/mikeyerke/driftline/blob/main/docs/architecture.md
- Judge scorecard: https://github.com/mikeyerke/driftline/blob/main/docs/JUDGE_SCORECARD.md
- Verified rules: https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md
- Cloud inventory: https://github.com/mikeyerke/driftline/blob/main/docs/RESOURCE_INVENTORY.md
- Pilot packet: https://github.com/mikeyerke/driftline/blob/main/docs/PILOT_PACKET.md

## Reproducible verification

~~~bash
BASE=https://driftline-xvxczqg62a-uc.a.run.app
curl -fsS "$BASE/health"
./scripts/verify_production.sh
./scripts/verify_live_agent.sh
./scripts/verify_public_approval_undo.sh
~~~

`verify_live_agent.sh` creates one bounded public workflow and waits for the
human approval gate. It fails closed unless the deployed response proves
`gemini-3.5-flash`, `google_adk`, a genuine structured impact pass, a genuine
structured decision-copilot pass with a passing deterministic policy review,
both allowlisted tool calls, four mapped artifacts, and durable audit events.
The identity-free
deterministic `/api/workflows/demo` endpoint remains the fallback for judging
when a live source or model quota is temporarily unavailable; the verifier
will retry that permitted fallback for up to three bounded runs, but never
reports success without a genuine Gemini structured turn.

`verify_public_approval_undo.sh` is the complementary packet-safety check. It
creates a fresh public evaluation workflow, requires the same live structured
Gemini/ADK and evidence-hash contract, exercises the deterministic approval
gate, verifies that the private Cloud Storage packet is persisted without an
external write, then reopens the decision and verifies a durable rollback
marker. It is safe to run repeatedly: the public lane cannot call Jira,
Confluence, Slack, GitHub, or Salesforce.

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
10%, 25%, 50%, 75%, 90%, and 100% current-spend thresholds. The Google Cloud free
trial started 2026-08-18 and ends 2026-11-17; the full paid-account activation
control is intentionally not enabled. See `docs/RESOURCE_INVENTORY.md` for
the complete cleanup inventory and exact image digest. Reapply the guardrail
with `./scripts/update_budget_guardrail.sh`; it refuses to target another
gcloud project.

Cloud Monitoring also owns the production liveness check: `driftline-health`
checks `/health` every five minutes from three regions and requires HTTP 200 plus
the `"status":"ok"` response marker. The enabled `Driftline health check
failing` alert policy auto-closes after 30 minutes and is intentionally scoped to
this project; no notification channel or external messaging destination is
configured by default. The check and policy are reproducible from
`infra/monitoring/driftline-health-alert.json` and the resource inventory.

The `Driftline production control plane` dashboard
(`9f00a615-b74c-4567-aae9-211cd66e97fc`) puts the health check, Cloud Run
request/instance telemetry, and Cloud Tasks dispatch pressure in one labeled
view. Its configuration is reproducible from
`infra/monitoring/driftline-production-dashboard.json`.

To reproduce the read-only release check locally, first select the isolated
project and run:

```bash
gcloud config set project driftline-hackathon-2026
./scripts/verify_production.sh
```

The script refuses to run if the active gcloud project is different. It checks
Cloud Run traffic, the Firestore-backed health response, Scheduler, Cloud
Tasks, Cloud Monitoring resources, and the recent Cloud Run error window; it
does not mutate infrastructure or read secrets.
