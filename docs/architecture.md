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
that identity before running. The source adapter can read only the two
explicitly registered public snapshots (`public/pricing`, `public/terms`,
`competitor/pricing`, `competitor/offerings`, and `competitor/blog`),
with a bounded timeout and snapshot size; failed fetches become an explicitly
labelled synthetic replay. Cloud Scheduler runs monitor
mode every six hours, and a Firestore snapshot ledger distinguishes a baseline,
unchanged source, and a verified change. The deterministic workflow engine—not
the model—creates the evidence, maps explicit offering impact profiles to
downstream work surfaces, applies the
approval policy, and records state transitions. Cloud Run hosts the API and
console; Firestore stores jobs, workflows, snapshot history, and immutable
audit-event documents.

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
Source observations use an append-only `observations` subcollection plus a
current pointer for comparison.
Reopening a decision restores the approval gate and is not an external undo.
Connector manifests are deliberately marked `external_write: false` until a
human approves the action. The hosted project now has one separately configured
least-privilege Jira connector: a Jira-scoped token is held in Secret Manager,
the runtime calls Atlassian's `api.atlassian.com/ex/jira/<cloudId>` gateway, and
the adapter is restricted to the free `KAN` / `Driftline` project. It creates
one marker-idempotent Task for the first approved packet, then undo changes only
Driftline-owned labels and appends an audit comment; it never deletes the Jira
issue. The live deployment verified `KAN-3` create and reversal while keeping
the token out of the browser and repository. Other target manifests remain
drafts until their own connectors are configured.
The public demo has no identity provider, so the displayed “Demo operator” is
a named demo actor, not production authentication.
