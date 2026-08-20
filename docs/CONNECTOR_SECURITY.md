# Connector security and approval lanes

Driftline has two deliberately separate approval lanes:

| Lane | Who can use it | Connector behavior | Purpose |
| --- | --- | --- | --- |
| Public demo | A named demo actor in the public console | Prepared-only packet; no external writes | Reliable judging and reproducible synthetic demonstration |
| Signed operator | An operator with a Google OIDC token or isolated approval secret | Configured, least-privilege connector handoffs and source onboarding may run | Authenticated production-style verification |

Connector environment variables do not authorize a public write by themselves. The API checks the approval identity scope before calling Jira, Confluence, Slack, or GitHub. A public demo approval is recorded with `scope=sandbox_packet_only`; a signed approval is recorded with `scope=configured`. Signed approvals use a Google OIDC token whose subject/email is resolved against the durable Firestore tenant membership directory; a static email mapping is retained only for local/bootstrap compatibility. The HMAC secret remains a break-glass isolated lane.

Undo follows the same boundary. A demo packet can be reopened without contacting an external system. A workflow that changed a configured connector requires a signed operator to reverse it. This prevents a public actor from creating or reversing customer-system work even if an isolated deployment happens to contain credentials.

## Current connector scope

- Jira: one configured project; idempotent marker; reversal uses Driftline-owned labels.
- Confluence: one configured space/page marker; reversal appends a note and preserves history.
- Slack: one configured channel; marker-based idempotency; reversal posts an audit message.
- GitHub: one configured repository; marker-based idempotency; reversal adds a label/comment.
- Internal context read lane: one fixed scope per configured connector. A signed
  operator can call `POST /api/connectors/context/summary` to retrieve Jira
  open-work counts, Confluence page counts, Slack recent-message volume, and
  GitHub issue/PR counts. The request accepts no JQL, page IDs, channel IDs,
  repository names, or source text; responses are aggregate metadata only and
  are not persisted or injected into public workflow state.
- Salesforce: tenant-scoped OAuth read-only context for `Product2`, `PricebookEntry`, and `Opportunity`; no write path. The OAuth lane uses a short-lived state record plus PKCE S256 and does not become connected until the real org callback succeeds.

Signed operator identities resolve to a tenant and role from the durable
Firestore membership directory. `DRIFTLINE_TENANT_MEMBERS` remains a local or
bootstrap compatibility mapping only. `viewer` identities can inspect status, while
`operator` and `owner` identities can start signed connector work; Salesforce
OAuth start, disconnect, and binding lifecycle operations require an `owner`.
The public demo has no tenant authority and
can only create sandbox packets. The HMAC break-glass path is additionally
restricted by the explicit `DRIFTLINE_HMAC_TENANTS` allowlist and returns a
forbidden response for unknown tenants; it is not a wildcard tenant selector.

Connector credentials are now tenant-bound for every external integration.
Each signed approval resolves a tenant principal first, then loads only the
deterministic Secret Manager name
`driftline-tenant-<tenant>-<connector>` from the canonical tenant credential
namespace (`driftline_tenants/{tenant}/credentials/{connector}`). The older
`driftline_connector_bindings` collection is a rolling-migration mirror, not a
second authority. Hosted strict namespace mode never reads that mirror as an
authorization source; a missing canonical record fails closed. Every migrated binding carries a versioned namespace record
with the exact Secret Manager resource, tenant service identity, connector, and
schema version. The runtime accepts neither a credential value nor an arbitrary
secret name. An owner activates a binding through
`POST /api/connectors/{connector}/binding` only after infrastructure has
provisioned the secret; missing, cross-tenant, cross-project, or mismatched
identity bindings fail closed. The binding records the resolved Secret Manager
version at verification time when the provider returns one, and connector
calls read that pinned version rather than silently following a later `latest`
value. Legacy bindings without a version remain compatible on `latest` until
their next owner verification. `scripts/migrate_tenant_credential_bindings.py`
adds the namespace metadata without reading or changing any credential value.
Rotation therefore has a hard cutover: the owner first moves the binding to
`rotation_pending`, connector calls fail closed, infrastructure adds the
replacement version, and the owner re-verifies to pin the new version. The
owner-only `POST /api/connectors/{connector}/binding/revoke` route marks a
binding revoked without deleting or returning the secret; connector resolution
then fails closed until a replacement version is provisioned and the binding is
re-verified. Secret deletion and provider-token revocation remain explicit
offboarding steps outside the runtime. The owner-only
`POST /api/connectors/{connector}/binding/rotate` route starts the same
two-step lifecycle: it records the reason and actor in the append-only audit
trail, marks the binding `rotation_pending`, and keeps connector calls disabled
until a replacement version is verified. The
legacy deployment-wide connector secret fallback is explicitly disabled in
Cloud Run. Salesforce refresh tokens use the same tenant boundary, while
Firestore stores only the tenant, instance URL, scopes, and health status—never
a token. Firestore job, workflow, outcome, source snapshot, and connector
binding records are separate control-plane data: tenant, membership, and
binding metadata intentionally do not carry the 30-day content TTL and remain
until an owner explicitly deprovisions them. `/api/tenants` exposes only the
caller's tenant metadata; `/api/tenants/members` is owner-only. Content records
continue to use bounded `expires_at` fields for TTL cleanup; the configured
deployment window is 30 days unless an operator changes it deliberately.
The signed `GET /api/connectors/bindings/health` route performs a bounded read-only
reconciliation of all five connector namespaces. It checks the deterministic
tenant secret and the tenant's non-secret destination profile; a binding is not
healthy when its target profile is missing, inactive, or malformed. Pending,
revoked, mismatched, or unreadable bindings are surfaced as attention, while
the response exposes only profile status and configured field names and never
includes a credential or target value.

Destination profiles are host-allowlisted before persistence and again at
connector construction: Jira and Confluence are limited to Atlassian Cloud or
the scoped Atlassian gateway, Slack to `slack.com`, GitHub to the public GitHub
API host family, and Salesforce to Salesforce/Force domains. URLs must be HTTPS
and cannot contain userinfo, query credentials, or fragments. This prevents a
tenant profile mistake from turning a bearer credential into an SSRF or
credential-exfiltration path.

New tenant onboarding uses the signed
`POST /api/connectors/{connector}/credential-enrollment` route. It creates a
15-minute enrollment under the tenant document, returns the exact secret
reference and requested operation scope, and defaults to read-only operations.
The provider value is still added out of band; the signed
`.../{enrollment_id}/complete` route verifies that value through the tenant
identity, pins its version, activates the binding, and records completion.
Enrollment state is tenant-namespaced, expires, and never stores a raw secret.

Non-secret connector targets are now owner-managed per tenant through
`POST /api/connectors/{connector}/profile` and the durable
`driftline_tenant_connector_profiles` collection. The profile accepts only the
small connector-specific allowlist (Jira project, Confluence space, Slack
channel, or GitHub repository plus required service URL fields); credentials,
arbitrary paths, query strings, and provider data are rejected. Connector
adapters prefer the durable profile and still validate every URL and target
before a request. The older operator-owned
`DRIFTLINE_TENANT_CONNECTOR_CONFIG` environment profile remains only as a
local-development compatibility fallback; hosted Firestore signed requests
fail closed with `tenant_connector_profile_missing` until the profile exists.
This keeps tenant target scope durable without putting credentials in
Firestore.
`POST /api/tenants/deprovision` is an owner-confirmed soft offboarding route:
it disables memberships and revokes connector bindings, but does not delete
secrets or provider-side data.
Binding activation, pending-secret verification, and revocation also append
metadata-only events to `driftline_tenant_audit_events`; signed owners can read
that tenant-filtered audit without receiving credentials or source content.

An owner can provision or update a member role through
`POST /api/tenants/members`. The request contains an email and one of
`viewer`, `operator`, or `owner`; it never accepts a connector credential,
access token, or arbitrary Secret Manager name. OIDC identities without an
explicit environment mapping or durable membership now fail closed with
`tenant_membership_required` rather than inheriting the default tenant.
When a durable membership exists, its role and `active`/`disabled` status take
precedence over bootstrap configuration; disabled identities fail closed with
`tenant_membership_inactive`.

Tenant identity also propagates through asynchronous monitor jobs and ADK
execution into the resulting workflow state. Signed approve, dismiss, and undo
operations require an exact workflow/tenant match. Tenant-bound job and
workflow reads (including packets, action items, and scenario previews) use the
same signed HMAC/OIDC boundary; unauthenticated public history filters those
records out. Append-only change memory and operator summary counts use the same
filter, so a public console cannot infer another tenant's workflow details.
The judge-facing synthetic workflow remains deliberately tenantless and
packet-only.

The action-item lifecycle is covered by the same rule: tenant-bound claim,
complete, fail, retry, and reverse calls require a signed operator for that
exact tenant. Public action calls are still available only for tenantless
synthetic demo packets.

Agent-call and workflow-mutation budgets are also tenant-scoped in the signed
lane. A noisy tenant cannot consume another tenant's in-process allowance; the
public demo and scheduler use separate buckets. The signed
`GET /api/tenants/usage` endpoint records durable monthly aggregates for
`agent_calls`, `workflow_mutations`, and `monitor_jobs` in
`driftline_tenant_usage`. The records contain tenant/period/counter metadata,
not source content or credentials. This is metering for quota and pilot
evidence only; billing is disabled and the in-process guardrails are not a
subscription billing system. The hosted Firestore deployment reserves signed
tenant slots with a transactional window counter in
`driftline_tenant_rate_limits`; local development uses the process-local
fallback.

The direct `POST /api/agent/run` endpoint has the same two lanes. The public
judge request may omit identity fields and runs only a tenantless synthetic or
allowlisted public-source turn. A real operator supplies `operator`,
`tenant_id`, and either the Google OIDC identity or the tenant-bound HMAC
approval token; the route verifies the principal, reserves the tenant's agent
quota, and passes that tenant into ADK source inspection and Firestore workflow
state. Supplying only a tenant ID or an unallowlisted source is rejected before
any model call. This keeps the fast direct ADK path from becoming a credential
or cross-tenant escape hatch while preserving a reliable public demo.

Source content is treated as untrusted even when its URL was explicitly
registered by an operator. The ADK tool seam and every Gemini text/vision
prompt receive a bounded model-visible copy with control-character cleanup,
instruction-like line redaction, length bounds, and an explicit quoted-data
policy. Raw source evidence remains available to the hash-bound workflow and
operator UI; the model-visible copy never contains credentials. This is a
deterministic Driftline guardrail, not a claim that Google Model Armor is
configured.

The public source registry starts with five pinned raw GitHub fixtures with explicit cadence and freshness SLAs. An authenticated operator can add exact public HTTPS HTML/text URLs through `/api/operator/sources`; each custom source belongs to the caller's tenant, and its append-only snapshot ledger is stored under a tenant-namespaced key. Each source is bounded by an exact URL, no redirects, no query credentials, DNS-resolved private-address rejection, a 128KB body limit, and a scheduler cap of 25 sources. It is still an allowlist, not a universal web crawler. Public registry/history routes expose only the pinned fixtures; signed source history is tenant-scoped.
Operator fetches also reject common bot/challenge interstitials before recording
an observation, so a CAPTCHA or “verify you are human” page cannot masquerade as
a competitor change. The source remains unavailable until a clean page can be
retrieved. Scheduled monitor runs also return `source_fetch_failed` with
`change_detected=false` on outages, malformed bodies, or challenge pages; the
synthetic fallback is reserved for the explicit judge/demo replay path. The
internal scheduler carries the owning tenant into each monitor
job and applies the tenant-specific quota; it never turns the registry into a
cross-tenant public crawl.

The registry and freshness endpoints follow the same boundary: unauthenticated
requests receive only the five judge fixtures, while a signed operator can read
the exact source metadata and append-only freshness state for its own tenant.
The endpoint does not return source credentials or bodies, and an unsigned
request cannot select a tenant by query parameter alone.

## Operational checks

- `/api/ops/summary` exposes approval posture and connector readiness without secrets.
- `/api/ops/job-failures` is a signed, tenant-filtered dead-letter-style view
  of jobs that exhausted Cloud Tasks retries; it returns only bounded metadata
  and follows the configured retention window.
- `/api/ops/value-proof` reports observed deployment counters and lists outcomes that remain unmeasured.
- `/api/connectors/context/summary` is signed-only and returns the bounded
  internal workload context contract. Disabled connectors report
  `not_configured` / `prepared_only`; configured connectors report an explicit
  read success or failure without returning raw records.
- `/api/connectors/bindings` is signed-only and lists metadata for the caller's
  tenant. It never returns credential values. Only an owner can register or
  activate a binding; operator/viewer identities cannot rebind a tenant.
- `/api/operator/sources` is the only source-registration path and requires a signed or Google-verified operator identity.
- The signed operator path is exercised separately from public browser QA; its token is never committed or returned by the API.

## Tenant-specific break-glass signing

Google OIDC is the normal operator path. For a controlled fallback, the
runtime derives `driftline-tenant-operator-<tenant>` from the authenticated
tenant and reads that exact Secret Manager resource; request bodies cannot
choose a secret name. The hosted deployment requires this tenant signer and
fails closed when it is missing, so a deployment-wide HMAC token cannot cross
tenant boundaries. Each signer is labeled with its tenant and is readable only
by the derived tenant service identity. The shared Cloud Run runtime can
impersonate that exact identity but is not a direct Secret Manager reader.
Rotate it by adding a new version through infrastructure, then retire the old
signer; no API response returns the value.

The hosted authorization check accepts a signer only for an active tenant in
the durable Firestore tenant directory. This removes the need to redeploy for
every new tenant while preserving a fail-closed response when the directory is
unavailable or a tenant is disabled. The legacy environment allowlist remains
available only as a local/bootstrap compatibility path, not as the hosted
source of SaaS tenant admission. When Firestore persistence is enabled, tenant,
membership, binding, profile, and OAuth-state reads are authoritative: a
missing durable document never falls back to a stale in-memory record.

Platform tenant bootstrap is a separate OIDC-only route,
`POST /api/platform/tenants`. It is allowlisted by
`DRIFTLINE_PLATFORM_OPERATOR_EMAILS`, creates or reactivates only tenant and
owner-membership metadata, and returns deterministic secret references without
accepting or returning provider credentials. Secret containers and provider
token rotation remain infrastructure-controlled operations.
Tenant bootstrap writes the tenant record and initial owner membership in one
Firestore transaction, so concurrent platform requests cannot claim the same
tenant identifier for different owners. The local development fallback uses a
process lock with the same single-winner contract.

The identity-only `GET /api/tenants/available` route completes the operator
tenant-selection boundary. It verifies the Google OIDC audience, issuer,
expiry, subject, and verified email, then returns only that email's active
tenant memberships and roles. A single active membership may be selected
implicitly by signed routes; multiple memberships require an explicit
`tenant_id`, and an unknown or disabled identity fails closed. The route never
accepts an operator-supplied email, HMAC token, credential, or arbitrary tenant
selector, so a user cannot discover or claim another tenant's namespace.
