# Driftline

**Tagline:** When a public promise changes, Driftline turns the evidence into
reversible owner action—autonomous where policy allows, human where judgment
matters.

- Category: **Taskmaster**
- Live application: https://driftline-xvxczqg62a-uc.a.run.app/
- Public repository: https://github.com/mikeyerke/driftline
- Architecture: `submission/assets/driftline-architecture.png`
- Demo video: **TODO — public YouTube or Vimeo URL, maximum four minutes**

## Inspiration

A competitor changes one pricing sentence. The alert is easy. The hard part is
finding every comparison, battlecard, deal-desk rule, and executive brief that
now carries a stale promise; deciding what can change safely; assigning the
right owner; and proving what the human actually approved.

Product Marketing and RevOps teams do not need another feed or chat window.
They need the change to become accountable work without giving a model the
authority to rewrite consequential business promises on its own.

## What it does

Driftline is an evidence-bound change-to-action agent:

1. It monitors a bounded registry of approved public sources.
2. A material transition creates an immutable before/after snapshot, SHA-256
   evidence hash, and stable Change Card identity.
3. Cloud Tasks invokes a Google ADK workflow asynchronously.
4. Gemini 3.5 Flash interprets the evidence, maps affected work surfaces, and
   drafts decision options with citations, tradeoffs, and rollback paths.
5. Deterministic policy outside the model stops high-risk work at a named human
   approval gate.
6. Approval creates evidence-linked owner work. In the authenticated tenant
   lane, Driftline can create or reactivate one least-privilege Jira marker.
7. Repeating the same action reuses the marker instead of duplicating work.
8. **Reopen decision** reverses only Driftline-owned Jira state and appends the
   reversal to the audit ledger.

The public judge lane is deliberately packet-safe and requires no credentials.
It proves the full Gemini/ADK, evidence, impact, approval, output, and reversal
journey without granting anonymous visitors access to an external system.

## Proof of action

The live release serves repository-head Git SHA
`63d96995808c8b1a891abd16682d645db19986fb` from Cloud Build
`92a1fcac-7d63-4c73-8306-0dcbe18c2466`. The application code is unchanged
from candidate `ddf5a5b`; subsequent commits preserve release and signed-action
proof.

In the signed operator lane, a live Gemini/ADK job reached the deterministic
approval gate and approval reactivated Jira marker `KAN-19`. The same hosted
workflow then reopened the decision and reversed only Driftline-owned labels
and comments. Both HTTP operations returned 200, the tenant credential stayed
in Secret Manager, and no unrelated Jira work was deleted or modified. The
reproducible evidence is recorded in `docs/INTERNAL_PILOT_2026-08-23.md`.

This is engineering proof from an isolated project, not a customer outcome or
ROI claim.

## How we built it

### Google technology

- **Gemini 3.5 Flash on Vertex AI** for evidence interpretation, structured
  impact analysis, and bounded Decision Copilot options.
- **Google Agent Development Kit** for the coordinator and two allowlisted
  read/inspect tools. The agent is intentionally not given an approval tool.
- **Cloud Run** for the FastAPI API and React operations console.
- **Cloud Tasks** for asynchronous OIDC-authenticated job dispatch and retries.
- **Cloud Scheduler** for the bounded monitor cadence.
- **Firestore** for jobs, workflows, observations, traces, tenant metadata,
  action state, and append-only audit records.
- **Cloud Storage** for versioned packet artifacts and reversal markers.
- **Secret Manager** for tenant-scoped connector credentials.
- **Cloud Build and Artifact Registry** for provenance-checked releases.

### Safety and architectural discipline

Model output never directly authorizes an action. Pydantic schemas, source and
artifact allowlists, evidence-hash checks, materiality rules, approval policy,
idempotency keys, tenant membership, credential scope, and rollback semantics
are deterministic code.

Source text is treated as untrusted evidence. Instruction-like content and
control characters are removed from the model-visible projection while raw
bytes remain unchanged for hashing and audit. Persisted traces exclude prompts,
source bodies, and credentials.

The anonymous and authenticated lanes are separate. Anonymous runs cannot write
to Jira. Signed actions require Google OIDC identity, active tenant membership,
a tenant-scoped Secret Manager binding, and an allowlisted operation.

## Key features

- Bounded source registry with cadence and freshness health
- Immutable evidence diff and full SHA-256 provenance
- Stable, retry-safe Change Card identity
- Gemini-generated impact map across four named owner surfaces
- Evidence-cited decision options with tradeoffs and rollback
- Deterministic human approval gate outside model authority
- Durable async execution and run recovery
- Idempotent, reversible Jira action in the signed tenant lane
- Append-only activity, source memory, and reversal history
- Trace-to-eval gate covering 14 independent safety/usefulness cases
- Credential-free public evaluation lane with explicit data labels

## Challenges

The hardest problem was not prompting Gemini. It was separating interpretation
from authority. Driftline needed to let the model understand messy evidence and
draft useful work while guaranteeing that the model could not approve itself,
silently widen connector scope, duplicate an action on retry, or lose the
evidence binding after a restart.

The second challenge was honest demoability. Judges need a free public path,
but giving anonymous traffic an external Jira credential would be irresponsible.
The solution is a packet-safe public lane plus separately verified signed action
proof, both using the same workflow and deterministic policy contracts.

## Accomplishments

- A deployed Gemini 3.5 Flash + Google ADK workflow, not a frontend simulation
- Durable Cloud Tasks/Firestore execution that survives browser reloads
- Real source, trace, impact, policy, approval, artifact, and reversal records
- One hosted signed Jira create/reactivate/reverse round trip
- 337 local backend tests, Ruff, frontend build, and 14/14 trace evaluation
  cases passing at the final packaging checkpoint
- Public release metadata exposing the exact serving SHA and Cloud Build ID
- No embedded credentials found in the repository

## Other data sources

The public lane uses five pinned, synthetic GitHub fixtures covering own pricing,
own terms, competitor pricing, competitor offerings, and competitor narrative
changes. They are labeled as fixtures and observed claims, not product truth.
The signed lane can read aggregate Jira, Confluence, Slack, GitHub, and consented
Salesforce context, but raw private records never enter the public console or
submission materials.

## What we learned

An agent becomes trustworthy when its authority is smaller than its reasoning
ability. Evidence identity, deterministic gates, scoped credentials, idempotency,
and reversal are not infrastructure details; they are the product.

Operational telemetry and customer value are also different. Driftline can
prove execution, approval latency, source observations, and action reversal.
It intentionally leaves customer time saved, revenue, retention, and willingness
to pay as `not_measured` until an independent pilot provides evidence.

## Testing instructions

1. Open https://driftline-xvxczqg62a-uc.a.run.app/ logged out.
2. Leave **Competitor pricing snapshot** selected and click **Run scan**.
3. Wait for the asynchronous job to reach **Human approval required**.
4. Inspect **Evidence diff**, **Open evidence**, **Agent trace**, the impact map,
   and an artifact detail row.
5. Select an action option and click **Approve action plan**.
6. Open the packet and activity history. The public lane states
   `External systems changed: No` by design.
7. Click **Reopen decision** and confirm reversed owner-action history while the
   workflow returns to the approval gate.
8. Check `/health` for the serving SHA/build and `/api/ops/summary` for the
   runtime, persistence, policy, and source-health posture.

Local and deployment reproduction steps are in the repository README.

## New-project and third-party disclosure

The implementation repository began August 18, 2026, within the contest period.
It continued from earlier product ideation and a source package; that ideation
is disclosed and is not represented as contest-period implementation. The
project uses open-source Python, React, Vite, Google ADK, Google Cloud client
libraries, FastAPI, Pydantic, and Lucide components under their licenses. All
contest implementation and integration work represented here was completed
during the submission period.

## What's next

The next milestone is a small independent Product Marketing pilot with paired
before/after timing and one bounded change class. Until then, Driftline will
describe its live deployment as engineering proof rather than customer ROI.
