# Architecture

```mermaid
flowchart TD
    S[Approved public or synthetic source fixture] --> W[FastAPI workflow engine]
    Q[/api/agent/run] --> A[Google ADK coordinator]
    A --> T[Allowlisted inspect/state tools]
    T --> W
    W --> E[Evidence, impact map, draft state]
    E --> G{Deterministic policy gate}
    G -->|High risk| H[Named human decision]
    H --> P[Bounded demo publisher]
    G -->|No approval needed| P
    P --> F[(Firestore workflow + audit events)]
    F --> U[React operations console]
```

Gemini 3.5 Flash supplies the live ADK turn when Vertex AI is configured.
Google ADK owns the coordinator and its two read/inspect tools. The
deterministic workflow engine—not the model—creates the reproducible synthetic
evidence, maps four bounded demo artifacts, applies the approval policy, and
records the state transitions. Cloud Run is the intended public API and console
host; Firestore is the intended durable workflow and audit store after the
isolated deployment is verified.

The policy gate is deliberately deterministic. A model cannot self-approve a
high-risk action, widen its own tool permissions, or call the approval and undo
endpoints. The public demo has no identity provider, so the displayed
“Demo operator” is a named demo actor, not production authentication.
