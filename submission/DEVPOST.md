# Driftline

**Tagline:** Contradictory evidence becomes a reversible experiment—and the
outcome can reopen the decision.

- Category: **Taskmaster**
- Live application: https://driftline-ops.web.app/
- Public repository: https://github.com/mikeyerke/driftline
- Architecture: `submission/assets/driftline-decision-twin-architecture.png`
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
It proves the full Gemini/ADK evidence, dissent, approval, autonomous outcome,
and generation-reopen journey without granting anonymous visitors access to an
external system.

## Proof of action

The final verified release serves public `main` Git SHA
`03ec8f12fc23d265c89b462a345a5b599a6411e8` on Cloud Run revision
`driftline-00305-xln` from Cloud Build
`c01bec2e-a950-407c-873b-b1d4fdc6bae6`. `/health`, the Cloud Run revision, and
Artifact Registry all resolve to immutable digest
`sha256:fca505ce56c6bd933f9cde8d55ff1e4ea7f9cad099d6fe39e8bb8321c96ea6d3`
(verified August 25, 2026). GitHub Actions run `32923233214` passed backend,
frontend, standalone-image, dependency, and repository-hygiene gates on that
same merge commit.

The final live browser proof ran the Decision Twin from generation 1 through a
named-human approval and autonomous Cloud Tasks measurement. The initial
Google ADK council recommended `segment`; the measured enterprise guardrail
then invalidated the plan, reopened the same case as generation 2, and changed
the selected recommendation to `rollback`. The original approval, outcome,
evidence hash, synthesis hash, and trigger reason remained attached. The
reopened action was disabled until a fresh human name was entered.

The release verifier independently ran five real Google ADK specialists with
Gemini 3.5 Flash, attached sample-weighted BigQuery aggregate evidence and a
BigQuery-vector precedent, preserved dissent, passed the 14/14 trace evaluation,
and completed the same two-generation workflow through Cloud Tasks. The public
browser console was clean on desktop and at a 390-pixel viewport.

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

The showcased Decision Twin uses a live, privacy-thresholded BigQuery aggregate
for activation by segment plus explicitly labeled redacted/synthetic support,
customer, strategy, and feasibility evidence. Its nearest-decision precedent is
an explicitly labeled synthetic fixture retrieved through BigQuery vector
similarity. The signed operator lane can read bounded aggregate Jira,
Confluence, Slack, GitHub, and consented Salesforce context, but raw private
records never enter the public console or submission materials.

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
2. Click **Run the decision workflow**.
3. Confirm generation 1 recommends **Segment the rollout**, shows five cited
   signals, five independent agents, competing responses, and the BigQuery
   vector precedent.
4. Open the full evidence/council disclosure or compare the four decision
   options. Notice that no action is available until a human approver is named.
5. Enter any review name and click **Approve segmented experiment**.
6. Stop clicking. Cloud Tasks evaluates the bounded aggregate and automatically
   reopens generation 2.
7. Confirm **Roll back globally** is now both recommended and selected, the new
   approval is disabled pending a fresh human name, and the learning receipt
   shows 7/7 policy checks plus the preserved prior approval and outcome.
8. Check `/health` for serving SHA
   `03ec8f12fc23d265c89b462a345a5b599a6411e8` and Cloud Build
   `c01bec2e-a950-407c-873b-b1d4fdc6bae6`.

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
