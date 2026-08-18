# Driftline

Driftline is a change-to-action agent for operational teams. It monitors one
explicitly allowlisted public source, verifies a material change, maps the
downstream artifacts that could become stale, drafts evidence-linked updates,
and pauses when a consequential human decision is required. The hosted demo
uses a bounded asynchronous job and a durable Firestore workflow; it produces
an auditable sandbox packet rather than pretending to write to a customer's
systems.

The demonstration models a pricing-page change from unlimited audit-log
retention to 365-day retention, then traces the impact into a pricing
battlecard, renewal playbook, enterprise FAQ, and CRM guidance. The deployed
source adapter fetches a single public GitHub snapshot when reachable and
falls back to the clearly labelled synthetic replay when it is not. It is not
connected to a real company system.

## Why it is agentic

Driftline is a complete resumable workflow rather than a chat interface:

1. Monitor source snapshots and detect semantic changes.
2. Verify the evidence and classify its operational risk.
3. Map the change to downstream artifacts and owners.
4. Draft bounded updates with evidence attached.
5. Interrupt the workflow for high-risk human decisions.
6. Resume from the decision and create a reversible packet, owner-review item,
   or queued item for each artifact.
7. Preserve an auditable event trail for every action.

The Google ADK coordinator is configured for the Gemini 3.5 Flash model and a
strictly allowlisted read/inspect tool set for reasoning. Cloud Tasks starts
the live run asynchronously, so the browser is not holding a model request
open. A separate deterministic API gate owns high-risk approval; the model is
not given an approval tool. Cloud Run serves the API and web console in one
container, with Firestore as the durable workflow, job, and audit store. The
synthetic replay remains available for predictable judging. Both live and
identity-free preview mutations are query-capped and rate-limited to bound
demo spend.

## Repository layout

~~~text
frontend/        React + Vite operational console
backend/         FastAPI, Google ADK agent, and workflow engine
docs/            architecture, contest rules, inventory, and visual concepts
submission/      Devpost copy and four-minute demo script
~~~

## Run locally

### Frontend

~~~bash
cd frontend
npm install
npm run dev
~~~

### Backend

~~~bash
cd backend
uv sync --extra dev
uv run uvicorn app.api:app --reload --port 8080
~~~

Copy backend/.env.example to backend/.env and provide a Google Cloud project
when enabling the live Gemini path. Synthetic demo mode is the default.

## Test

~~~bash
cd frontend && npm run build
cd ../backend && uv run --extra dev pytest
~~~

The verified local suite also runs Ruff lint and format checks. If uv is not
installed, a standard Python virtual environment with the dependencies in
backend/pyproject.toml produces the same test result.

## Deploy to Google Cloud

The contest deployment is isolated in the driftline-hackathon-2026 project.
Create the dedicated resources and review docs/RESOURCE_INVENTORY.md before
submitting the included build:

~~~bash
gcloud config set project driftline-hackathon-2026
gcloud builds submit --project=driftline-hackathon-2026 --config cloudbuild.yaml .
~~~

The root Dockerfile builds the React console and serves it from FastAPI. Cloud
Run uses the dedicated runtime service account for Vertex AI and Firestore; no
API key is embedded in the client.

## Public links

- Live demo: https://driftline-xvxczqg62a-uc.a.run.app/
- GitHub: https://github.com/mikeyerke/driftline
- Demo video: to be added after the four-minute public video is uploaded
- Architecture: https://github.com/mikeyerke/driftline/blob/main/docs/architecture.md
- Verified rules: https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md
- Cloud inventory: https://github.com/mikeyerke/driftline/blob/main/docs/RESOURCE_INVENTORY.md

## Reproducible verification

~~~bash
BASE=https://driftline-xvxczqg62a-uc.a.run.app
curl -fsS "$BASE/health"
JOB=$(curl -fsS -X POST "$BASE/api/jobs/demo" -H 'content-type: application/json')
JOB_ID=$(printf '%s' "$JOB" | jq -r .job_id)
curl -fsS "$BASE/api/jobs/$JOB_ID"
~~~

The final release evidence in `docs/RESOURCE_INVENTORY.md` records the exact
Cloud Run revision, async job result, browser smoke test, Firestore documents,
and Cloud Run logs. A live ADK response is only claimed when those fields have
been observed directly; the identity-free deterministic `/api/workflows/demo`
endpoint is the fallback for evaluation.

## Safety model

- Synthetic or explicitly approved public data only in the demonstration.
- Every detected change carries hash-bound source evidence.
- High-risk actions stop at a human approval gate.
- Tools are allowlisted and the demonstration state transitions are bounded.
- The model proposes actions; deterministic policy code decides whether a
  bounded packet may be created.
- Generated packets explicitly state that no external systems changed.
- The public demonstration names a demo operator but does not provide
  production identity authentication.
- No real Salesforce, CRM, billing, customer, or private company data is used.

## Cost and isolation

The deployment is isolated in the new `driftline-hackathon-2026` Google Cloud
project. Cloud Run is configured with zero minimum instances and a maximum of
one instance. Cloud Tasks is limited to one concurrent dispatch and 0.2
dispatches per second. A $10 monthly billing budget is filtered to this project with
25%, 50%, 75%, 90%, and 100% current-spend thresholds. The Google Cloud free
trial started 2026-08-18 and ends 2026-11-17; the full paid-account activation
control is intentionally not enabled. See `docs/RESOURCE_INVENTORY.md` for
the complete cleanup inventory and exact image digest.
