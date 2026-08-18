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
    H --> P[Bounded sandbox packet]
    W --> F[(Firestore jobs, workflow + audit events)]
    P --> F
    F --> U[React operations console]
```

Gemini 3.5 Flash supplies the live ADK turns through Vertex AI. Google ADK owns
the coordinator and its two allowlisted inspect/state tools, then runs a
separate task-mode analyst with a strict JSON contract. Driftline validates the
analyst's artifact names, owners, risk values, and evidence hash before using
the proposals; invalid output fails closed to an explicitly labelled
deterministic demo fallback. Cloud Tasks turns the scan into a durable
asynchronous job; the task carries an OIDC identity and the worker verifies
that identity before running. The source adapter can read only
`public/pricing`, with a bounded timeout and snapshot size; failed fetches
become an explicitly labelled synthetic replay. Cloud Scheduler runs monitor
mode every six hours, and a Firestore snapshot ledger distinguishes a baseline,
unchanged source, and a verified change. The deterministic workflow engine—not
the model—creates the evidence, maps four bounded demo artifacts, applies the
approval policy, and records state transitions. Cloud Run hosts the API and
console; Firestore stores jobs, workflows, snapshot history, and immutable
audit-event documents.

The policy gate is deliberately deterministic. A model cannot self-approve a
high-risk action, widen its own tool permissions, or call the approval and undo
endpoints. Approval creates a packet inside Driftline only; it never claims to
have updated Salesforce, a CRM, billing, support, or customer records. The
approval also creates a reversible Firestore action record with its own ID;
undo changes that record to `reversed` and reopens the gate.
Reopening a decision restores the approval gate and is not an external undo.
The public demo has no identity provider, so the displayed “Demo operator” is
a named demo actor, not production authentication.
