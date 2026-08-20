# Connector security and approval lanes

Driftline has two deliberately separate approval lanes:

| Lane | Who can use it | Connector behavior | Purpose |
| --- | --- | --- | --- |
| Public demo | A named demo actor in the public console | Prepared-only packet; no external writes | Reliable judging and reproducible synthetic demonstration |
| Signed operator | An operator with a Google OIDC token or isolated approval secret | Configured, least-privilege connector handoffs and source onboarding may run | Authenticated production-style verification |

Connector environment variables do not authorize a public write by themselves. The API checks the approval identity scope before calling Jira, Confluence, Slack, or GitHub. A public demo approval is recorded with `scope=sandbox_packet_only`; a signed approval is recorded with `scope=configured`. Signed approvals can be backed by a Google OIDC token whose subject/email is verified against the configured operator allowlist; the HMAC secret remains a break-glass isolated lane.

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

Signed operator identities resolve to a tenant and role from
`DRIFTLINE_TENANT_MEMBERS`. `viewer` identities can inspect status, while
`operator` and `owner` identities can start signed connector work; only an
`owner` can disconnect Salesforce. The public demo has no tenant authority and
can only create sandbox packets.

Connector credentials are isolated per integration. Salesforce refresh tokens
are written only to a pre-provisioned tenant Secret Manager secret, while
Firestore stores the tenant, instance URL, scopes, and health status—never a
token. Firestore job, workflow, outcome, and source snapshot records carry a
bounded `expires_at` field for TTL cleanup; the configured deployment window is
30 days unless an operator changes it deliberately.

The public source registry starts with five pinned raw GitHub fixtures with explicit cadence and freshness SLAs. An authenticated operator can add exact public HTTPS HTML/text URLs through `/api/operator/sources`; each source is bounded by an exact URL, no redirects, no query credentials, DNS-resolved private-address rejection, a 128KB body limit, and a scheduler cap of 25 sources. It is still an allowlist, not a universal web crawler.

## Operational checks

- `/api/ops/summary` exposes approval posture and connector readiness without secrets.
- `/api/ops/value-proof` reports observed deployment counters and lists outcomes that remain unmeasured.
- `/api/connectors/context/summary` is signed-only and returns the bounded
  internal workload context contract. Disabled connectors report
  `not_configured` / `prepared_only`; configured connectors report an explicit
  read success or failure without returning raw records.
- `/api/operator/sources` is the only source-registration path and requires a signed or Google-verified operator identity.
- The signed operator path is exercised separately from public browser QA; its token is never committed or returned by the API.
