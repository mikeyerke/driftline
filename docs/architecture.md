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
    H --> P[Bounded sandbox packet + owner action items]
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
that identity before running. The source adapter starts with five pinned judge
fixtures and can also read exact public HTTPS HTML/text URLs added by a signed
operator through `/api/operator/sources`. Those operator sources are bounded
to an 8-second fetch, 128KB body, no redirects, no query credentials, and no
private or reserved DNS-resolved addresses; this is an allowlist, not arbitrary competitor
crawling. Failed fixture fetches become an explicitly labelled synthetic
replay, while a failed operator source is reported unavailable rather than
fabricated. Cloud Scheduler runs monitor mode every six hours, and a Firestore
snapshot ledger distinguishes a baseline, unchanged source, and a verified
change. Scheduler fan-out is capped at 25 sources; a signed canary can target
one source. The deterministic workflow engine—not
the model—creates the evidence, maps explicit offering impact profiles to
downstream work surfaces, applies the
approval policy, and records state transitions. Cloud Run hosts the API and
console; Firestore stores jobs, workflows, snapshot history, and immutable
audit-event documents. Failed jobs are retried by Cloud Tasks at most three
times with bounded backoff. Persisted jobs, workflows, source observations, and
outcome measurements carry an explicit 30-day TTL by default.

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
sandbox packet and the approved operational output are written to the isolated,
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
The signed-only `/api/connectors/context/summary` route closes the utility
loop without broadening the crawler: each configured adapter performs one
fixed, bounded read against its deployment scope and returns aggregate
metadata only. Jira is limited to open work in the configured project,
Confluence to page counts in the configured space, Slack to recent message
volume in the configured channel, and GitHub to open issue/PR counts in the
configured repository. No user-supplied query, object ID, page body, message
text, or repository target is accepted. The result is request-scoped, not
persisted, and never becomes public demo context.
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
verifies a Google OIDC identity for the configured operator email (with an
isolated HMAC break-glass path) before any external write. Salesforce has a
tenant-scoped OAuth callback and read-only REST query allowlist, but remains
disabled until a real org authorizes it. `/api/ops/value-proof` reports
observed deployment counts, approval latency, and action-item completion while
explicitly separating those observations from unmeasured customer ROI, time
saved, revenue lift, and willingness-to-pay.

Connector credentials are tenant-scoped rather than deployment-scoped. A
signed request resolves its tenant principal, looks up a metadata-only binding
in Firestore, and reads the deterministic Secret Manager secret
`driftline-tenant-<tenant>-<connector>`. Only the owner binding route can
activate that reference; arbitrary secret names and raw credential values are
rejected. Cloud Run has no legacy global connector-secret fallback. This keeps
two customer tenants from sharing a token even when they use the same
connector type, while preserving the public packet-only lane.

The Change Card is the product's decision unit. It is assembled from verified
source evidence, the deterministic impact graph, and action lifecycle state.
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
