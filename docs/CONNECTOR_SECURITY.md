# Connector security and approval lanes

Driftline has two deliberately separate approval lanes:

| Lane | Who can use it | Connector behavior | Purpose |
| --- | --- | --- | --- |
| Public demo | A named demo actor in the public console | Prepared-only packet; no external writes | Reliable judging and reproducible synthetic demonstration |
| Signed operator | An operator holding the isolated approval secret | Configured, least-privilege connector handoffs may run | Authenticated production-style verification |

Connector environment variables do not authorize a public write by themselves. The API checks the approval identity scope before calling Jira, Confluence, Slack, or GitHub. A public demo approval is recorded with `scope=sandbox_packet_only`; a signed approval is recorded with `scope=configured`.

Undo follows the same boundary. A demo packet can be reopened without contacting an external system. A workflow that changed a configured connector requires a signed operator to reverse it. This prevents a public actor from creating or reversing customer-system work even if an isolated deployment happens to contain credentials.

## Current connector scope

- Jira: one configured project; idempotent marker; reversal uses Driftline-owned labels.
- Confluence: one configured space/page marker; reversal appends a note and preserves history.
- Slack: one configured channel; marker-based idempotency; reversal posts an audit message.
- GitHub: one configured repository; marker-based idempotency; reversal adds a label/comment.
- Salesforce: read-only context contract for `Product2`, `PricebookEntry`, and `Opportunity`; no write path and no live customer authorization in this deployment.

The public source registry is also intentionally bounded: five pinned raw GitHub fixtures with explicit cadence and freshness SLAs. It is not a universal web crawler. A new source must be reviewed, allowlisted, bounded, and tested before it enters the registry.

## Operational checks

- `/api/ops/summary` exposes approval posture and connector readiness without secrets.
- `/api/ops/value-proof` reports observed deployment counters and lists outcomes that remain unmeasured.
- The signed operator path is exercised separately from public browser QA; its token is never committed or returned by the API.
