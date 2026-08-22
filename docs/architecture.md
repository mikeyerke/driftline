# Architecture

```mermaid
flowchart TD
    S[Allowlisted public snapshot or synthetic replay] --> A[Google ADK coordinator]
    A --> M[ADK structured impact analyst]
    Q[/api/jobs/demo] --> TQ[Cloud Tasks queue]
    TQ --> A
    A --> T[Allowlisted inspect/state tools]
    T --> W
    M --> W
    W --> E[Evidence, impact map, draft state]
    E --> G{Deterministic policy gate}
    G --> H[Named human decision]
    H --> P[Bounded change packet + owner action items]
    E --> CC[Change Card: materiality, exposure, role packets, closure]
    CC --> H
    W --> F[(Firestore jobs, workflow + audit events)]
    P --> F
    P --> GCS[(Versioned Cloud Storage action artifacts)]
    P --> X[Target-specific handoff packets]
    X --> J[Jira adapter: KAN only]
    X --> C[Confluence draft]
    X --> SL[Slack notification]
    X --> GH[GitHub draft PR]
    F --> U[React operations console]
```

Gemini 3.5 Flash supplies the live ADK turns through Vertex AI. Google ADK owns
the coordinator and its two allowlisted inspect/state tools, then runs a
separate task-mode analyst with a strict JSON contract. Driftline validates the
analyst's artifact names, owners, risk values, and evidence hash before using
the proposals; invalid output fails closed, with a deterministic fallback kept
only for the explicitly labelled synthetic demo path. Cloud Tasks turns the scan into a durable
asynchronous job; the task carries an OIDC identity and the worker verifies
that identity before running. If Gemini is temporarily quota-limited, only the
anonymous synthetic judge lane uses a clearly labelled deterministic replay so
the approval/evidence journey remains reviewable; signed tenant and monitor
jobs remain fail-closed. The source adapter starts with five pinned judge
fixtures and can also read exact public HTTPS HTML/text/RSS URLs added by a signed
operator through `/api/operator/sources`. Those operator sources are bounded
to an 8-second fetch, 128KB body, no redirects, no query credentials, and no
private or reserved DNS-resolved addresses; each tenant is capped at 25 enabled
custom sources; this is an allowlist, not arbitrary competitor
crawling. Failed fixture fetches become an explicitly labelled synthetic
replay, while a failed operator source is reported unavailable rather than
fabricated. Common bot/challenge interstitials (Cloudflare/Akamai/captcha
pages) are rejected before they can become false source changes. Cloud Scheduler runs monitor mode every six hours, and a Firestore
snapshot ledger distinguishes a baseline, unchanged source, and a verified
change. Scheduler fan-out is capped at 25 sources; a signed canary can target
one source. A source's observation cadence is separate from its freshness SLA;
the scheduler skips healthy sources until their cadence is due, retries
baselines/failures, and round-robins due tenant buckets before applying the
global cap. Deferred sources return their next due time/reason. Scheduler
delivery is at-least-once, so the service checks the
durable in-flight job ledger before enqueueing a source and reports a
deduplicated no-op instead of launching duplicate model work. The deterministic
workflow engine—not
the model—creates the evidence, maps explicit offering impact profiles to
downstream work surfaces, applies the
approval policy, and records state transitions. Cloud Run hosts the API and
console; Firestore stores jobs, workflows, snapshot history, and immutable
audit-event documents. Failed jobs are retried by Cloud Tasks at most three
times with bounded backoff. When delivery exhausts that policy, Driftline also
writes a tenant-filtered, metadata-only terminal marker to
`driftline_job_failures`; signed operators can inspect those dead-letter-style
markers through `/api/ops/job-failures` without prompts, source bodies,
exception text, or credentials. Persisted jobs, workflows, source observations,
outcome measurements, and failure markers carry an explicit 30-day TTL by
default. Tenant owners can override the bounded retention window for
tenant-owned source observations, workflow/job, failure, outcome, and
credential-access metadata through the signed tenant policy route; provider
secrets remain in Secret Manager and require explicit offboarding.

Signed agent calls, workflow mutations, and connector reads reserve separate
tenant-scoped Firestore windows. Owners can read and tune bounded
`agent_calls_per_window`, `workflow_mutations_per_window`,
`connector_calls_per_window`, and `retention_days` allowances through
`GET/POST /api/tenants/policy` without a Cloud Run redeploy. External connector
context and health probes consume `connector_calls_per_window`.
Policy fields are allowlisted and clamped to safe bounds, changes append a
tenant audit event, and missing policy metadata falls back to deployment
defaults. A hosted quota lookup failure fails closed before work is reserved;
a retention lookup failure uses the bounded deployment default. This is tenant
control-plane policy and privacy/metering, not billing.

Terminal tenant failures remain operationally recoverable: a signed operator
can call `POST /api/jobs/{job_id}/retry` from Run history. Driftline rechecks
tenant membership and the source allowlist, preserves the failed job's
parameters, and stores a `retry_of` link. That durable link makes the endpoint
idempotent across Cloud Run instances; a racing request receives the existing
successor rather than launching another agent call. Anonymous jobs have no
mutation retry route and remain controlled by the public scan lane.

The public multimodal analysis route is a separate cost boundary: it accepts
only the fixed visual registry and is capped at 10 Gemini analyses per
3600-second process window. Exhaustion returns `429` with `Retry-After`, so a
client cannot accidentally retry-loop into Vertex spend. This public guard is
deliberately separate from tenant connector quotas because the judge-safe
visual fixture lane carries no tenant identity.

The direct `/api/agent/run` path preserves the same boundary in both modes:
the anonymous judge request is tenantless, packet-safe, and replaced with a
fixed allowlisted instruction before any model call or durable write, while a
signed operator request verifies its tenant principal before reserving quota
and passing the operator's query into ADK source inspection and Firestore
workflow persistence. A partial identity or non-allowlisted source is rejected
before the model is called.

Source bodies are untrusted data, even when fetched from an operator-registered
URL. Before a source snapshot crosses an ADK tool or Gemini prompt seam,
Driftline creates a bounded model-visible copy: control characters are
normalized, instruction-like lines and prompt-boundary markers are replaced,
and long content is truncated. Raw evidence remains unchanged in the
hash-bound workflow and operator UI. The coordinator, structured analyst,
decision copilot, and Gemini vision prompt all receive an explicit quoted-data
policy and never receive source credentials. This is a deterministic local
guardrail; it is not a claim that Google Model Armor is configured.

The policy gate is deliberately deterministic. A model cannot self-approve a
high-risk action, widen its own tool permissions, or call the approval and undo
endpoints. Approval creates a packet inside Driftline only; it never claims to
have updated Salesforce, a CRM, billing, support, or customer records. The
approval also creates one approved operational output inside the isolated
Driftline project and a reversible Firestore action record with its own ID,
evidence-bound owner action items, and target-specific Jira, Confluence, Slack,
and GitHub handoff manifests. A human can claim and complete an item
without granting the model any write authority; the lifecycle is
`queued → claimed → completed` and is compare-and-set protected. Undo changes
the action record and every item to `reversed` and reopens the gate. Each approved
change packet and the approved operational output are written to the isolated,
versioned Cloud Storage bucket; undo writes separate rollback markers. These
objects are private and are referenced by `gs://` URI in the action record.
Not every verified change should create downstream work. A named human can
dismiss a pending signal with a required reason; the deterministic engine moves
it to `dismissed`, clears packet/action-item candidates, and records the reason
and actor in the workflow, Change Card closure state, packet, and audit event.
Dismissal is an intentional no-op, not a hidden failure, and it leaves source
evidence available for later review.
Source observations use an append-only `observations` subcollection plus a
current pointer for comparison. `/api/monitor/registry` derives source
freshness, baseline, stale, and synthetic-only states from that ledger without
fetching or mutating a source. `/api/ops/summary` exposes bounded
job/workflow counts, connector enablement, model and call guardrails, and
source health for production operations; it never returns secret values.
Public summaries omit tenant policy, while signed summaries include only the
caller’s effective bounded quota/retention policy.
Hosted operator history, change memory, ops summary, and value-proof metrics
merge the disposable instance cache with bounded Firestore history on every
read. A warm Cloud Run instance therefore cannot under-report records created
by a previous instance. The public console's Value proof panel intentionally
uses the anonymous lane and shows only tenantless public-demo records; it does not
present those counts as customer traction. Signed tenant operators receive an
exact-tenant value-proof scope through the API, with deployment-wide fixtures
excluded from their metrics.
The signed-only `/api/connectors/context/summary` route closes the utility
loop without broadening the crawler: each configured adapter performs one
fixed, bounded read against its deployment scope and returns aggregate
metadata only. Jira is limited to open work in the configured project,
Confluence to page counts in the configured space, Slack to recent message
volume in the configured channel, and GitHub to open issue/PR counts in the
configured repository. Salesforce is a fifth tenant-bound lane: before OAuth
consent it reports authorization required; after consent it reads only
Product2, PricebookEntry, and Opportunity aggregate counts/field names. No
user-supplied query, object ID, page body, message text, CRM record, or
repository target is accepted. The result is request-scoped, not persisted,
and never becomes public demo context. A signed `live`, `tenant_demo`, or
`monitor` workflow may explicitly attach that same reader's normalized result
to its Change Card. Only connector status, fixed scope, bounded counts, and
allowlisted Salesforce object totals/field names survive; the workflow's
normal Firestore TTL applies, and an append-only `internal_context_reader`
event records the attachment. Anonymous demo runs never call this seam.
Reopening a decision restores the approval gate and is not an external undo.
Connector manifests are deliberately marked `external_write: false` in the
public demo. A configured connector is callable only after a separately signed
operator approval; a named public demo actor can never cross that boundary. The
hosted project has separately configured, least-privilege Jira, Confluence,
Slack, and GitHub connectors. Jira uses the
Atlassian `api.atlassian.com/ex/jira/<cloudId>` gateway and is restricted to the
free `KAN` / `Driftline` project. Confluence uses the scoped
`api.atlassian.com/ex/confluence/<cloudId>/wiki/api/v2` gateway and is restricted
to the dedicated `DRIFT` space. Slack is restricted to the isolated Driftline
workspace and one channel with `channels:history` and `chat:write`; GitHub is
restricted to `mikeyerke/driftline`. Each adapter uses marker idempotency and
Secret Manager credentials. Undo never deletes customer work: Jira changes only
Driftline-owned labels and adds a comment, Confluence appends a named-human
reversal note through a page version, Slack posts a reversal message, and GitHub
adds a reversal label/comment. The signed operator lane directly verifies
connector create/reversal while keeping tokens out of the browser and
repository. The public demo remains identity-free for judging, so the
displayed “Demo operator” is a named demo actor, not production authentication;
its connector statuses remain `prepared_only`. The signed operator lane
verifies a Google OIDC identity against the durable tenant membership directory
(with an isolated HMAC break-glass path) before any external write. The hosted
deployment does not carry a deployment-wide operator email allowlist, so adding
an active tenant membership does not require a Cloud Run redeploy. Salesforce has a
tenant-scoped OAuth callback and read-only REST query allowlist, but remains
disabled until a real org authorizes it. `/api/ops/value-proof` reports
observed deployment counts, approval latency, and action-item completion while
explicitly separating those observations from unmeasured customer ROI, time
saved, revenue lift, and willingness-to-pay.

Connector credentials are tenant-scoped rather than deployment-scoped. A
signed request resolves its tenant principal, looks up a metadata-only binding
in the canonical Firestore namespace
`driftline_tenants/{tenant}/credentials/{connector}`, and reads the
deterministic Secret Manager secret
`driftline-tenant-<tenant>-<connector>`. Each binding carries a versioned
namespace record naming the exact project resource and per-tenant service
identity; the legacy flat binding collection is a migration artifact and is
read-only unless an operator explicitly enables a short-lived write-through
window. Hosted strict namespace mode never reads it as an authorization
source. Only the owner binding route can
activate that reference; arbitrary secret names and raw credential values are
rejected. Each active binding pins the resolved Secret Manager version when
available, so adding a new version cannot silently change a live tenant until
an owner re-verifies the rotation. Cloud Run has no legacy global
connector-secret fallback. Owners can
start an audited rotation, which moves a binding to `rotation_pending` and
immediately fails connector calls closed until infrastructure adds a replacement
Secret Manager version and the owner re-verifies the binding. Soft
deprovisioning revokes every binding and disables memberships; provider-token
revocation and secret-version destruction remain explicit infrastructure
offboarding steps. This keeps two customer tenants from sharing a token even
when they use the same connector type, while preserving the public packet-only
lane. The hosted runtime also derives a collision-resistant Google service
identity per tenant and impersonates it for Secret Manager access. The shared
Cloud Run identity has only scoped `Service Account Token Creator` access to
each tenant identity; Secret Manager IAM grants the tenant identity access only
to that tenant's deterministic secrets. Together with durable membership
discovery, explicit tenant selection, owner/operator/viewer roles, version
pinning, rotation, revocation, and append-only lease auditing, this is a
production tenant-scoped credential data-plane foundation for a shared SaaS
deployment.
Customer-managed KMS keys, self-serve billing, and dedicated compute per tenant
remain optional commercial layers beyond the hackathon release. The
metadata-only migration is runnable with
`scripts/migrate_tenant_credential_bindings.py` and never reads or changes
provider credential values.
The credential broker is the runtime seam behind every tenant connector. It
accepts only `(tenant_id, connector, operation)`, derives the exact
`driftline-tenant-<tenant>-<connector>` Secret Manager reference, verifies the
active binding and operation scope, reads the pinned version, and returns a
short-lived in-process lease. A connector adapter cannot supply an arbitrary
secret name or bypass a revoked/rotating binding. Lease metadata (tenant,
connector, operation, credential ID, pinned version, and expiry) is appended to
`driftline_credential_access_events`; values, bearer tokens, source bodies, and
provider responses are excluded. Hosted leases use the derived tenant identity
when `DRIFTLINE_TENANT_SECRET_IDENTITY_MODE=impersonated`; direct shared-runtime
reads remain a local compatibility mode. Owners can inspect this inventory through the
signed `GET /api/connectors/credentials` and its append-only access trail at
`GET /api/connectors/credentials/access`. This is the same production
tenant-scoped credential data-plane foundation with least-privilege operation scopes;
customer-managed KMS keys, self-serve billing, and dedicated compute per tenant
remain optional commercial layers outside this hackathon release.
The signed `GET /api/connectors/bindings/health` route is a read-only
reconciliation probe across the fixed connector allowlist; it checks active
bindings against readable Secret Manager state and the tenant's bounded
non-secret destination profile. Missing, inactive, or malformed profiles are
surfaced as attention, and the response never returns a credential or target
value.

Profile URLs are validated against provider host allowlists at both the API
boundary and connector construction. HTTPS, no userinfo/query/fragment, and
Atlassian/Slack/GitHub/Salesforce host checks prevent a malformed tenant target
from becoming an SSRF or bearer-token exfiltration path.

The SaaS onboarding seam is a short-lived, tenant-namespaced enrollment session
stored at `driftline_tenants/{tenant}/credential_enrollments/{id}`. It carries
only the deterministic secret reference, expiry, requested connector
operations, and lifecycle metadata. New sessions default to the concrete
`read_context` scope only; an owner must explicitly grant a write operation. The provider
secret is added out of band, then the signed completion route verifies the
tenant's exact secret, pins the concrete version, activates the canonical
binding, and closes the session. Expired or cross-tenant sessions fail closed.
Bindings that predate the operation-scope field are treated as read-only at
lease time until an owner rotates them; omission never widens authority.
This makes onboarding self-service-ready without ever accepting a raw token in
the browser, API body, Firestore control plane, or audit ledger.

The Change Card is the product's decision unit. It is assembled from verified
source evidence, the deterministic impact graph, bounded aggregate connector
context when a signed tenant run supplies it, and action lifecycle state.
Its `change_card_id` is deterministic for an allowlisted source plus evidence
hash. That identity is carried into action records, owner-item idempotency keys,
private artifact paths, and connector markers so scheduler retries and repeated
observations converge on one reversible action rather than duplicating work.
Its internal-exposure block is deliberately capability-aware: synthetic runs
say “not CRM data” and show unavailable opportunity/renewal counts; only a
verified, permissioned Salesforce read lane may populate those fields. Role
packets are generated for the owners already named by the impact profile, not
for arbitrary recipients. This keeps the high-value change-to-work loop useful
before a customer connector exists and prevents a model from manufacturing
business exposure. Approval also assigns deterministic risk-based due dates to
owner actions; the closure card and `/api/ops/value-proof` expose overdue work
without claiming customer ROI.

The human may change an artifact-level route after choosing a Decision Copilot
option, but this is not an escape hatch from policy. The console keeps the
original option ID, requires an override reason, and sends an explicit custom
override marker. The API revalidates the reviewed workflow decision, requires
an exact decision for every mapped artifact, rejects unknown actions, and
blocks queuing a high-risk artifact. The approval and `approval_recorded` event
retain the original option ID, override marker, and reason so reviewers can
distinguish a copilot recommendation from a deliberate human adjustment.

The production container is reproducible by construction: Cloud Build copies
`backend/uv.lock`, installs the pinned `uv==0.8.17` bootstrap, and runs
`uv sync --frozen --no-dev`. A source-only change reuses the dependency layer;
an attempted dependency drift fails the build instead of silently resolving a
new runtime. Local release verification uses `uv lock --check` plus the full
test/lint suite.

## Trace-to-eval release gate

Every live workflow carries a bounded `agent_trace` beside its evidence,
impact, and append-only audit events. `backend/app/trace_eval.py` evaluates
that public contract with nine independent safety/usefulness cases and refuses
to pass when critical safety, minimum usefulness, overall score, or trend
thresholds regress. The evaluator is deterministic and independent from
Gemini; its golden fixture is synthetic and never becomes a customer metric.

`POST /api/evals/run` can score a known workflow or the bounded fixture without
invoking a connector. Only the redacted report is written append-only to
`driftline_trace_evaluations`, with a structural trace fingerprint rather than
prompts, source bodies, or credentials. `GET /api/evals/latest` is public only
for tenantless evaluation records and exact-tenant signed for operator records.
The CI job runs the same gate, while the live-agent verifier evaluates a fresh
Google ADK/Gemini trace after it reaches the deterministic human gate. This
creates a verifiable feedback loop: a future release can show `stable` or
`improved`, and a safety/usefulness regression blocks the release instead of
being hidden by a newer dashboard snapshot.
