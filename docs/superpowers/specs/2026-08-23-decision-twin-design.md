# Driftline Decision Twin — Winning Architecture Design

Date: 2026-08-23  
Status: Approved direction; implementation pending spec review  
Target: Google All Things Agentic Hackathon, Taskmaster category

## 1. Product thesis

Driftline will become an evidence-to-outcome operating system for product
managers. It will continuously detect **decision debt**: product decisions,
assumptions, customer promises, experiments, or roadmap commitments that new
evidence has weakened or invalidated.

The product's job is not to summarize everything or create more tickets. For
one consequential question at a time, it must produce an evidence-bound answer
to seven questions:

1. What changed?
2. Which existing decision or assumption is now at risk?
3. What should the product team do next?
4. What evidence supports and contradicts that recommendation?
5. What would change the recommendation?
6. What reversible experiment or action should be launched?
7. Did the outcome validate the decision, or should Driftline reopen it?

This expands the existing promise-drift workflow without discarding its
strongest differentiators: durable operations, deterministic safety policy,
human approval, evidence hashes, idempotency, scoped rollback, and complete
decision provenance.

## 2. Core judge journey

The demo will use one realistic decision case rather than expose every feature:

> Activation fell after a redesigned onboarding flow. Customer calls praise
> faster setup, support tickets show enterprise permission confusion, usage
> data shows smaller teams improving and larger workspaces regressing, and a
> roadmap commitment promises broader rollout next week. Should the PM ship,
> roll back, or run a segmented experiment?

The visible journey has four beats:

1. **Evidence changed** — Driftline ingests a call excerpt, support themes, a
   product screenshot, bounded usage aggregates, and the existing roadmap
   commitment. Each datum has provenance, freshness, confidence, and a content
   hash.
2. **The council disagrees** — customer, usage, strategy, feasibility, and
   challenger agents independently analyze the case. The UI highlights the
   decisive conflict instead of presenting artificial consensus.
3. **A human decides** — Driftline ranks Ship, Roll back, Segment, and Defer;
   simulates each option; states what would change its recommendation; and asks
   the PM to approve one bounded plan.
4. **The system learns** — approval creates an experiment brief, measurement
   contract, and reversible owner actions. A simulated later outcome violates
   a guardrail, causing the same decision to reopen with an explicit reason and
   preserved lineage.

The judge should understand the value in under 20 seconds and see the complete
agentic loop in under four minutes.

## 3. Seven product capabilities

### 3.1 Decision-debt detection

Every durable `DecisionCase` records its question, approved option, assumptions,
expected outcome, guardrails, review window, and links to the evidence available
at decision time. A new `DecisionDebtDetector` compares later evidence with
those assumptions. It emits a bounded `DecisionDebtSignal` only when a typed
trigger fires:

- a metric crosses an approved guardrail;
- evidence contradicts a recorded assumption;
- a commitment reaches its review date without outcome proof;
- a material source change affects the case's evidence graph; or
- an experiment finishes without meeting its success contract.

The detector is deterministic over validated structured facts. Gemini may
classify evidence into those facts, but it cannot itself reopen or mutate a
decision.

### 3.2 Multimodal evidence graph

The graph is a typed projection, not a generic vector database. Nodes are
`EvidenceItem`, `Claim`, `Assumption`, `Metric`, `CustomerSegment`, `Commitment`,
`ProductSurface`, `DecisionCase`, and `OutcomeObservation`. Edges are
`supports`, `contradicts`, `affects`, `derived_from`, `commits_to`, and
`measures`.

Each evidence node stores:

- source type and allowlisted locator;
- capture time, observed time, and freshness;
- immutable SHA-256 content hash;
- tenant and case boundary;
- redacted excerpt or aggregate projection;
- extraction confidence and schema version; and
- raw-artifact pointer when the signed operator is allowed to access it.

The first slice supports bounded text, image, aggregate usage, and structured
commitment fixtures. Raw customer records are never exposed in the public judge
lane. Gemini Vision analyzes a supplied product screenshot; the structured
Gemini analyst extracts claims from redacted text; deterministic validators
reject missing provenance, unsupported claims, and cross-tenant references.

### 3.3 Google ADK Product Council

One ADK coordinator fans out to five specialized, read-only analysis agents:

- **Customer Agent** — identifies user problems, segments, and contradictory
  qualitative evidence.
- **Usage Agent** — interprets bounded aggregates and checks metric/segment
  claims.
- **Strategy Agent** — tests alignment with the recorded objective and roadmap
  commitment.
- **Feasibility Agent** — identifies implementation, rollout, reliability, and
  reversibility constraints from supplied evidence only.
- **Challenger Agent** — attacks the leading recommendation, identifies missing
  evidence, and states the cheapest evidence that could change the decision.

Agents run independently from the same immutable evidence manifest. They return
strict JSON with citations to graph node IDs. They have no approval or connector
write tools. The coordinator validates every citation, records disagreement,
and produces a `CouncilSynthesis`; it does not hide minority positions.

The design intentionally avoids agent-role theater. Each role owns a distinct
schema, evaluation rubric, and failure mode. A deterministic policy layer—not
another model—decides whether the case is complete enough for human review.

### 3.4 Ranked decision and falsifiability contract

The Decision Room shows a single recommended next move plus alternatives. Each
option contains:

- expected outcome and affected segment;
- cited supporting and contradicting evidence;
- confidence calibrated as low/medium/high rather than fake precision;
- cost of delay and reversibility class;
- assumptions and guardrails;
- `would_change_mind_if`, expressed as measurable conditions; and
- an explicit `decline` list for tempting but unsupported work.

A recommendation cannot reach approval unless every material claim cites an
evidence node, the challenger has run, at least one alternative is present, and
the success and rollback conditions are machine-checkable.

### 3.5 Counterfactual simulation

The system evaluates four bounded actions: Ship, Roll back, Segment, and Defer.
It does not predict revenue or user behavior as fact. It calculates traceable
consequences from the case graph: affected segments, commitments, product
surfaces, owner work, guardrails, and evidence gaps.

The UI supports side-by-side comparison but defaults to the recommended option.
Changing an input invalidates the synthesis hash and requires a fresh council
run. Counterfactuals never write to external systems.

### 3.6 Reversible experiment execution

Human approval creates a durable `ExperimentPlan` containing:

- hypothesis and target segment;
- primary metric and guardrails;
- baseline and target expressed without fabricated values;
- start, review, and stop conditions;
- owner actions and due dates;
- rollback plan; and
- evidence, council, option, and approval hashes.

The public lane produces a packet-safe plan and receipt. A signed tenant may
create only allowlisted, scoped Jira/Confluence/Slack/GitHub actions through the
existing durable-operation protocol. Every side effect has an idempotency key,
lease, recovery path, operation ID, and compensating action. The agent cannot
approve its own recommendation.

### 3.7 Outcome-aware decision memory

Outcome observations are appended, never overwritten. The deterministic
`OutcomeEvaluator` compares them with the measurement contract and returns
`validated`, `invalidated`, `inconclusive`, or `awaiting_data`.

An invalidated guardrail or contradicted assumption creates a new decision
generation and reopens human review. It preserves the original decision,
approval, predicted outcome, actual observation, and causal trigger. The judge
can scrub the timeline from initial evidence through reopening.

## 4. Google Cloud architecture

### 4.1 Runtime

- **Firebase Hosting** serves the public console and proxies API traffic.
- **Cloud Run** hosts the FastAPI control plane and Google ADK runtime, scales
  to zero, and uses request-scoped CPU.
- **Cloud Tasks** provides at-least-once execution for council and outcome jobs.
- **Cloud Scheduler** triggers bounded source and outcome monitoring.
- **Firestore** is the durable state machine, operation ledger, evidence graph,
  decision memory, and append-only audit store.
- **Cloud Storage** holds immutable evidence and generated packet artifacts.
- **Vertex AI / Gemini 3.5+** performs structured analysis and multimodal image
  understanding.
- **BigQuery** stores bounded, aggregate product-usage fixtures and supports the
  signed tenant aggregate adapter. Queries require a maximum-bytes-billed cap.
- **Secret Manager** contains connector credentials; the browser and agent
  prompts never receive secrets.
- **Cloud Logging and Error Reporting** capture structured correlation IDs,
  workflow generations, and safe operational errors.

BigQuery is the only new infrastructure service required for the winning slice.
Additional services will not be added merely to inflate the architecture
diagram.

### 4.2 Orchestration and data flow

1. The API creates a `DecisionCase` and immutable evidence manifest in a
   Firestore transaction.
2. A Cloud Task durably claims the council generation.
3. The ADK coordinator invokes independent specialist agents with the same
   manifest and per-agent token/call budgets.
4. Validated positions and citations are persisted before synthesis.
5. Deterministic policy verifies completeness, provenance, disagreement, and
   reversibility.
6. A human approves through the existing signed or packet-safe lane.
7. The durable operation layer creates experiment artifacts and approved
   connector actions.
8. A later scheduled or demo outcome observation runs deterministic evaluation.
9. If a typed trigger fires, compare-and-set creates a new decision generation
   and the UI marks why the decision reopened.

Every write includes `tenant_id`, `case_id`, `generation`, `evidence_hash`, and
`correlation_id`. Stale generations cannot mutate current state.

## 5. Reliability and security boundaries

- Public and tenant lanes remain explicitly separate.
- All external evidence sources are allowlisted and protected by the existing
  SSRF, redirect, content-type, and size controls.
- Agent outputs are untrusted until schema, citation, tenant, and policy checks
  pass.
- Prompts use redacted projections; raw customer text and credentials never
  enter the public lane.
- Side effects require named human approval and the existing durable claim,
  bounded lease, retry, reconciliation, and rollback protocol.
- Firestore compare-and-set prevents two council or decision generations from
  becoming current.
- Cloud Tasks handlers are idempotent and authenticate service identities.
- BigQuery accepts parameterized, allowlisted aggregate queries only; no model
  generates SQL in the winning slice.
- Each specialist failure is recorded. The case fails closed instead of
  silently synthesizing from partial council output.

## 6. Cost controls for the authorized $300 credits

The build target is under $100, preserving at least $200 for rehearsal and the
judging window. Google Cloud budgets are alerts, not hard stops, so application
limits provide the actual enforcement:

- Cloud Run: minimum instances `0`, maximum instances `2`, bounded request
  concurrency and timeout.
- Council: at most five specialist calls plus one synthesis call per generation;
  no recursive delegation.
- Gemini: explicit input/output token ceilings, image-size optimization, and a
  tenant/day call quota.
- Public judge lane: low per-IP and global generation limits with pinned fallback
  artifacts for resilience.
- Cloud Tasks: capped retry count, exponential backoff, and dead-letter state in
  Firestore.
- BigQuery: partitioned fixture table, dry run before execution, and maximum
  bytes billed per query.
- Storage: lifecycle deletion for transient uploads; immutable demo proof retained
  only through the judging window.
- Logging: sampling and retention limits for high-volume informational events.
- Billing: alerts at $25, $75, $150, $225, and $285 when project access permits.

No paid resource will be provisioned until the authenticated project and active
billing account are confirmed. No service will be given an unbounded autoscaling
or model-call path.

## 7. Product experience

The primary surface becomes one **Decision Room**, not another collection of
panels. It has four vertically ordered sections:

1. **Decision at risk** — one-sentence question, urgency, current commitment,
   and the new evidence that triggered review.
2. **Evidence and disagreement** — a compact evidence graph and one highlighted
   council conflict. Raw hashes and infrastructure details remain available
   behind disclosure.
3. **Recommended move** — the leading option, alternatives, `what would change
   our mind`, counterfactual selector, and clear approval gate.
4. **Plan and learning receipt** — experiment contract, owner work, four-part
   receipt, and an outcome timeline that visibly reopens the decision.

Judge Mode removes operator configuration and secondary telemetry from the
primary path. Body text remains at least 14px, every state change is announced,
keyboard focus is preserved, reduced motion is respected, and color is never
the only signal.

## 8. Evaluation and testing

### Deterministic unit and property tests

- Evidence graph rejects missing provenance, invalid hashes, stale generations,
  and cross-tenant edges.
- Council outputs reject nonexistent citations, unsupported claims, duplicate
  roles, and partial completion.
- Counterfactual simulation is deterministic for the same graph and options.
- Approval rejects incomplete experiment contracts and stale synthesis hashes.
- Outcome evaluation correctly validates, invalidates, or leaves cases
  inconclusive.
- Reopening is exclusive and preserves the original decision lineage.
- Durable operations survive retries, concurrency, worker termination, and
  ambiguous external results.

### Agent evaluations

The existing trace-to-eval gate gains checks for citation coverage, disagreement
preservation, falsifiability, alternative quality, counterfactual grounding,
and decision-reopening correctness. Critical provenance, tenant, approval, or
rollback failures fail CI.

### End-to-end acceptance

A pinned case must run from multimodal evidence through council disagreement,
human approval, packet creation, outcome observation, and automatic reopening.
The live verifier records workflow, case, generation, evaluation, operation,
release SHA, and build IDs.

## 9. Validation and demo evidence

The participant study will ask 6–8 PM/product-ops participants to complete the
same decision case with and without Driftline. Measures are time-to-decision,
evidence recall, identification of contradicting evidence, confidence rationale,
and ability to explain what would reverse the decision. Results remain blank
until real people participate; no synthetic response will be presented as user
validation.

The 3:45–3:50 video will spend approximately:

- 25 seconds on the PM problem;
- 45 seconds on multimodal evidence and the decision-debt trigger;
- 55 seconds on independent council disagreement;
- 55 seconds on counterfactuals and human approval;
- 45 seconds on the experiment receipt and automatic reopening; and
- 25 seconds on the Google Cloud architecture and reproducible proof.

## 10. Delivery sequence

1. Add decision-domain models, fixtures, evidence graph, and deterministic
   policies.
2. Add bounded specialist schemas, ADK council orchestration, and agent evals.
3. Add counterfactuals, experiment plan, outcome evaluator, and reopening state
   machine.
4. Build the focused Decision Room using the existing visual system.
5. Add BigQuery aggregate adapter and infrastructure configuration behind a
   fail-closed feature flag.
6. Run the full backend, frontend, accessibility, security, and production-build
   gates; update the existing PR rather than opening competing submission work.
7. Deploy the exact green SHA only from an authenticated Google Cloud project,
   apply cost caps, and run the complete live verifier.
8. Conduct real participant validation and record the final demo after the
   deployed experience is stable.

Registration and Devpost submission remain explicitly out of scope until the
entrant requests them.

## 11. Scope discipline

The winning slice does not attempt to become a full roadmap system, feedback
repository, analytics platform, or feature-flag service. It proves one novel
loop extremely well: **new evidence challenges an existing product decision;
independent agents disagree; a human chooses a falsifiable, reversible plan;
and measured outcomes can reopen that decision.**

