# Driftline winning technical specification

## Architecture and PRD mapping

### Source and observation plane — PRD Epic 1

`backend/app/source.py`, `snapshots.py`, and `materiality.py` enforce exact
allowlists, bounded bodies, source classification, snapshot hashing, and
materiality. Cloud Scheduler calls the bounded monitor route; Firestore stores
append-only observations.

### Agent and impact plane — PRD Epic 2

`backend/app/agent.py`, `adk_runtime.py`, `analysis.py`, `impact.py`, and
`decision_copilot.py` run Gemini 3.5 Flash through Vertex AI and Google ADK.
Pydantic schemas validate structured outputs before they can replace draft
artifacts. Guarded evidence projections treat source text as untrusted data.

### Policy and action plane — PRD Epics 3–4

`backend/app/workflow.py`, `guardrails.py`, `artifacts.py`, `connectors.py`,
`credential_broker.py`, and `tenant.py` keep approval, credentials, connector
scope, idempotency, and rollback outside model authority. Anonymous evaluation
is packet-safe. Signed Jira actions use tenant-scoped Secret Manager bindings.

### Durable execution plane — PRD Epics 1–4

`backend/app/persistence.py` and `memory.py` store jobs, workflows, traces,
snapshots, actions, and audit events in Firestore. Cloud Tasks dispatches the
worker asynchronously with bounded retries. Cloud Run hosts the API and React
console in one release image.

### Judge surface — PRD Epic 5

`frontend/src/App.jsx` and its focused components render the evidence diff,
impact map, Decision Copilot, human gate, action results, rollback history, and
release proof. `submission/` carries the scorecard, compliant demo script,
architecture upload, screenshots, captions, and final Devpost copy.

## Core data lifecycle

1. A source observation is fetched under an allowlist and normalized.
2. Before/after bytes produce an immutable evidence hash and stable Change Card.
3. A durable job is enqueued and claimed idempotently.
4. ADK/Gemini produces structured impact and decision options.
5. Deterministic validation binds all proposed work to the evidence hash.
6. High-risk state persists at `needs_approval`.
7. Anonymous approval writes only versioned Driftline artifacts; a signed
   operator may invoke one tenant-scoped connector operation.
8. Reopen appends reversal state and reverses only Driftline-owned output.
9. The UI reloads the durable workflow and audit history from the API.

## Release contract

- Python 3.12 with `uv.lock`; Node 22 with `package-lock.json`.
- Gemini model: `gemini-3.5-flash` via Vertex AI `global`.
- Google framework: Google ADK.
- Google infrastructure: Cloud Run, Firestore, Cloud Tasks, Cloud Scheduler,
  Cloud Storage, Secret Manager, Artifact Registry, and Cloud Build.
- Deployment script refuses dirty trees and embeds the exact Git SHA/build ID.
- Cloud Build verifies the serving image digest and `/health` contract.

## Demo failure strategy

- Keep the public packet-safe lane available without sign-in.
- Pre-warm the service and run one practice workflow before recording.
- Record the signed Jira approval/reversal as one uninterrupted segment.
- Preserve a single continuous screen recording; trim only dead time without
  changing the order or outcomes shown.
- Never expose tokens, tenant secrets, or private source bodies.
- If the signed lane fails, do not substitute a fabricated result. Fix the
  release or use the already verified public packet flow while clearly labeling
  the Jira proof as separately recorded production evidence.

## External references

- Google ADK: https://google.github.io/adk-docs/
- Cloud Run: https://cloud.google.com/run/docs
- Firestore: https://cloud.google.com/firestore/docs
- Cloud Tasks: https://cloud.google.com/tasks/docs
- Vertex AI Gemini: https://cloud.google.com/vertex-ai/generative-ai/docs

## Submission artifacts

- `submission/DEVPOST.md`: canonical concise project narrative.
- `submission/DEMO_SCRIPT.md`: 3:45 target video plan.
- `submission/assets/driftline-architecture.png`: required architecture upload.
- `submission/BUILD_STORY.md`: optional public build-content bonus.
- `devpost-submission.md`: exact form-ready packet and remaining private fields.
