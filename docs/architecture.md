# Architecture

```mermaid
flowchart TD
    S[Allowlisted public snapshot or synthetic replay] --> A[Google ADK coordinator]
    Q[/api/jobs/demo] --> TQ[Cloud Tasks queue]
    TQ --> A
    A --> T[Allowlisted inspect/state tools]
    T --> W
    W --> E[Evidence, impact map, draft state]
    E --> G{Deterministic policy gate}
    G --> H[Named human decision]
    H --> P[Bounded sandbox packet]
    W --> F[(Firestore jobs, workflow + audit events)]
    P --> F
    F --> U[React operations console]
```

Gemini 3.5 Flash supplies the live ADK turn through Vertex AI. Google ADK owns
the coordinator and its two allowlisted inspect/state tools. Cloud Tasks turns
the scan into a durable asynchronous job; the task carries an OIDC identity
and the worker verifies that identity before running. The source adapter can
read only `public/pricing`, with a bounded timeout and snapshot size; failed
fetches become an explicitly labelled synthetic replay. The deterministic
workflow engine—not the model—creates the evidence, maps four bounded demo
artifacts, applies the approval policy, and records state transitions. Cloud
Run hosts the API and console; Firestore stores jobs, workflows, and immutable
audit-event documents.

The policy gate is deliberately deterministic. A model cannot self-approve a
high-risk action, widen its own tool permissions, or call the approval and undo
endpoints. Approval creates a packet inside Driftline only; it never claims to
have updated Salesforce, a CRM, billing, support, or customer records.
Reopening a decision restores the approval gate and is not an external undo.
The public demo has no identity provider, so the displayed “Demo operator” is
a named demo actor, not production authentication.
