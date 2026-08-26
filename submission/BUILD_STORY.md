# Building Driftline: the decision should change when the evidence does

*I created this build story for the purpose of entering the Google All Things
Agentic Hackathon.*

I kept making roadmap calls whose evidence changed after the commitment. The
decision itself would survive—in a meeting note, a ticket, or collective
memory—but the assumptions that justified it would disappear across analytics,
customer conversations, strategy, and engineering constraints.

That is the friction behind Driftline. It is not a chatbot that gives product
advice. It turns one contested product decision into an inspectable learning
loop:

`evidence → dissent → counterfactuals → human experiment → outcome → reopen`

The twist is what happens after the recommendation. A named human authorizes a
falsifiable, reversible experiment. A background monitor evaluates the metric
and risk guardrail committed at approval. If the guardrail breaks, Driftline
records the result, rolls back its bounded internal allocation, and reopens the
same decision as a new generation—with the original evidence, disagreement,
approval, and outcome still attached.

## Five agents, one constrained synthesis

The Decision Twin begins with five evidence surfaces: customer, usage,
strategy, feasibility, and challenger. Five independent Google ADK specialists
use Gemini 3.5 Flash through Vertex AI to inspect bounded projections of those
sources. Each role has its own mandate, but none has a mutation or approval
tool.

The synthesis must cite the evidence and preserve material disagreement. It
cannot silently average every position into a safe-sounding paragraph. The
showcase decision deliberately contains tension: small teams activate faster
after an onboarding redesign while enterprise activation and permission setup
degrade. That conflict produces four real alternatives—ship, rollback, segment,
or defer—with different upside, downside, unknowns, metrics, stop conditions,
and reversibility.

The useful output is not “AI recommends segmentation.” It is a decision a PM
can inspect, reject, or turn into an operating contract.

## The model recommends; a human authorizes

Human authority is a state transition, not a sentence in a system prompt.
Approval is disabled until a reviewer is named. Firestore compare-and-set logic
binds the approval to the exact evidence hash, synthesis hash, option, and
decision generation. Stale and conflicting approvals fail closed.

The current verified public release proves the council, human approval, bounded
outcome, and generation-2 reopen. An unreleased local candidate makes the action
boundary even more visible: approval creates one allocation only inside
Driftline’s own decision state. The receipt says **decision state only** and
**external writes: none**. A breached guardrail rolls that allocation back
before the decision reopens.

That candidate is not production proof. It must not be described as live until
its exact public commit, Cloud Run revision, Cloud Build, image digest, ADK
trace, and browser journeys are independently reverified.

## Google Cloud is the execution substrate

Firebase Hosting provides a stable credential-free judge URL and rewrites the
application to Cloud Run. Firestore stores cases, generations, evidence
identity, approvals, outcomes, and lineage. BigQuery supplies a
privacy-thresholded aggregate and vector precedent memory. Cloud Tasks runs the
asynchronous outcome path after approval. Cloud Scheduler provides bounded
monitor cadence. Cloud Build and Artifact Registry bind the deployed image to a
reviewable source identity.

The direct Cloud Run health endpoint exposes the serving application commit
and build without revealing credentials. The final continuous video will show
that `*.run.app` endpoint in-frame; an architecture diagram or “Cloud Run”
caption is not treated as deployment proof.

## The hardest engineering problem was authority recovery

Happy-path agents are easy to demo. The dangerous state is a process ending
after an operation may have begun but before the application records the final
result.

Driftline uses stable operation identities, compare-and-set transitions,
idempotent artifacts, bounded leases, and explicit reconciliation states. The
model never decides whether a side effect already happened. Deterministic code
and provider evidence do. Retries converge on the same operation rather than
manufacturing a second action.

The public Decision Twin grants anonymous judges no external-system authority.
A separate signed tenant lane has exercised a least-privilege Jira marker and
reversal, but it is supporting engineering proof—not the public demo’s action
claim and not customer validation.

## Ten checks before a decision can be trusted

The Decision Twin evaluator tests ten visible contracts:

1. evidence provenance is retained;
2. specialist positions are genuinely independent;
3. synthesis keeps citations;
4. material disagreement remains visible;
5. the experiment is falsifiable;
6. human authority is required; and
7. the outcome can reopen the original decision without erasing lineage;
8. decision debt follows approval, monitoring, resolution, and reopening;
9. all seven PM capabilities advance through one monotonic ten-step loop; and
10. product memory never assigns confidence to a zero-sample claim.

The release gate also checks privacy floors, billed-byte ceilings, bounded model
calls, exact release identity, dependency safety, production browser journeys,
and current-revision errors. These are not prompt promises. They are code and
deployment invariants.

## What I refused to claim

The system proves engineering execution: Google ADK and Gemini reasoning,
privacy-bounded evidence, human approval, asynchronous monitoring, a measured
demo outcome, rollback, and decision reopening.

It does not yet prove independent PM adoption, customer ROI, revenue, retention,
time saved, or willingness to pay. Those values remain `not_measured` until a
qualified external PM brings a current decision and completes the precommitted
review window. A design-partner conversation is not a customer; payment or a
signed paid-pilot commitment is required for that claim.

The main lesson is simple: an agent becomes trustworthy when its authority is
smaller than its reasoning ability. Driftline makes that boundary visible—and
makes the decision change when reality says it should.

Live application: https://driftline-ops.web.app/

Source and reproducible setup: https://github.com/mikeyerke/driftline
