# Driftline

**Tagline:** Contradictory evidence becomes a reversible experiment—and the
outcome can reopen the decision.

- Category: **Taskmaster**
- Live application: https://driftline-ops.web.app/
- Public repository: https://github.com/mikeyerke/driftline
- Architecture: `submission/assets/driftline-architecture.png`
- Demo video: **TODO — public YouTube or Vimeo URL, maximum four minutes**

## Judge this in 45 seconds

Open the Decision Room and start the pinned onboarding council. Inspect the
evidence graph and five cited specialist positions, pause on strategy and
challenger dissent, compare ship/rollback/segment/defer, and approve one
falsifiable experiment as a named human. Then stop clicking: a durable Cloud
Tasks monitor processes the bounded measurement and the same case reopens as
generation 2 while retaining the complete original approval and experiment plan.

## Inspiration

PMs do not lack opinions. They lack a defensible way to combine contradictory
usage, customer, strategy, and delivery evidence; freeze what would prove a
choice right or wrong; and carry the measured result back into the original
decision. Driftline turns that decision debt into an inspectable learning loop
without giving a model approval authority.

## What it does

Driftline is an evidence-bound Decision Twin built on a durable
change-to-action agent:

1. It combines bounded customer, usage, strategy, and feasibility evidence in
   a provenance-preserving graph. Live product metrics come from a
   sample-weighted, privacy-thresholded, billed-bytes-capped BigQuery adapter.
2. Five independent Google ADK specialists use Gemini 3.5 Flash to produce
   cited positions; a sixth synthesis turn must retain visible disagreement.
3. The product compares ship, rollback, segment, and defer with option-specific
   metrics, guardrails, stop conditions, rollbacks, and owner actions.
4. A named human alone approves, and Firestore binds the approval to the exact
   evidence, synthesis hash, and decision generation.
5. Human approval starts an idempotent Cloud Tasks monitor. A measured outcome
   produces a learning receipt and either closes the case or reopens the next
   generation with complete prior lineage—without another PM prompt.

The underlying operational foundation remains independently useful:

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
7. Before side effects begin, Driftline claims one durable operation. An
   interrupted result blocks conflicting decisions and reconciles the same ID;
   an expired lease also recovers a hard process termination through a separate
   Firestore compare-and-set before retrying.
8. Repeating the same action reuses the marker instead of duplicating work.
9. **Reopen decision** reverses only Driftline-owned Jira state and appends the
   reversal to the audit ledger.

The public judge lane is deliberately packet-safe and requires no credentials.
It proves the full Gemini/ADK, evidence, impact, approval, output, and reversal
journey without granting anonymous visitors access to an external system.

## Proof of action

The August 24 verified baseline release served Git SHA
`1b8a8bfbcf2249136dbf08de54c0f7ee15f575d6` on Cloud Run revision
`driftline-00291-v89` from Cloud Build
`154547e7-36ae-4eb2-a79a-35064e293191`. `/health`, the Cloud Run revision, and
Artifact Registry all resolve to immutable digest
`sha256:18d8e1f76dd3c2a305f6e76aacbbc75fe876a2028f6881e371f9d3b21e34d450`
(verified August 24, 2026). Final submission metadata must use the identity
returned by `/health` and `./scripts/verify_production.sh` for the final
candidate.

The live Decision Twin proof ran five real Google ADK specialists with cited
customer, usage, strategy, feasibility, and challenger positions. It preserved
`ship`/`segment`/`defer` disagreement, attached sample-weighted BigQuery
aggregate evidence, stopped for named-human approval, evaluated a measured
outcome, and reopened the same case as generation 2 with its complete prior
approval and experiment plan retained.

In the signed operator lane, a live Gemini/ADK job reached the deterministic
approval gate and approval reactivated Jira marker `KAN-19`. The same hosted
workflow then reopened the decision, updated only Driftline-owned labels, and
appended a named-human reversal comment; prior Jira comments were retained.
Both HTTP operations returned 200, the tenant credential stayed
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

Approval and reversal have distinct durable executing states. If a process
ends during a side-effect sequence, the workflow enters
`reconciliation_required` with the same credential-free operation ID and
generation. A named human can retry that operation; configured connector
recovery still requires signed tenant authority.

Source text is treated as untrusted evidence. Instruction-like content and
control characters are removed from the model-visible projection. Hashing and
audit bind the bounded, decoded, whitespace-normalized source text rather than
claiming byte-for-byte preservation of the HTTP response. Persisted traces
exclude prompts, source bodies, and credentials.

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
- Full local backend suite, Ruff, frontend build, and 14/14 trace evaluation
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

1. Open https://driftline-ops.web.app/ logged out.
2. Leave **Competitor pricing snapshot** selected and click **Run live agent**.
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
