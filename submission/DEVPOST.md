# Driftline

**Tagline:** Driftline detects decision debt, turns it into a reversible
experiment, and reopens the decision when reality changes.

- Category: **Taskmaster**
- Live application: https://driftline-ops.web.app/
- Public repository: https://github.com/mikeyerke/driftline
- Architecture: `submission/assets/driftline-decision-twin-architecture.png`
- Demo video: **TODO — public YouTube or Vimeo URL, maximum four minutes**

> Draft custody note: the immutable production proof below describes the
> currently serving release. The bounded internal-allocation card and authored
> custom measurement contract exist only in the unreleased local candidate and
> must not be presented as live until that candidate is released and reverified.

## Judge this in 45 seconds

Open the Decision Room and start the pinned onboarding council. Inspect the
autonomously detected decision-debt item, its affected commitment, missing
evidence, and urgency score. Then inspect the evidence graph and five cited specialist positions, pause on strategy and
challenger dissent, compare ship/rollback/segment/defer, and approve one
falsifiable experiment as a named human. Then stop clicking: a durable Cloud
Tasks monitor processes the bounded measurement and the same case reopens as
generation 2 while retaining the complete original approval and experiment plan.

**Taskmaster proof:** one named authorization starts the multi-step background
workflow. After that approval, Driftline evaluates the committed measurement,
writes the learning receipt, and reopens the decision without another prompt or
PM click.

The live system uses Gemini 3.5 Flash through Vertex AI and Google ADK on Cloud
Run. The public judge lane changes only Driftline decision state; a separately
verified signed-operator run reversibly updated one Driftline-owned Jira marker.
The model never receives approval authority. This is deployed engineering
proof, not customer ROI or independent PM adoption.

## Inspiration

I kept recreating the same friction while building products: the decision was
scattered across evidence, commitments, and follow-up, and the decision
outlived the assumptions that created it. PMs do not lack opinions. They lack a
defensible way to combine contradictory
usage, customer, strategy, and delivery evidence; freeze what would prove a
choice right or wrong; and carry the measured result back into the original
decision. Driftline turns that decision debt into an inspectable learning loop
without giving a model approval authority.

### Why now

Current product-leadership research points to a decision-system problem, not a
lack of roadmap templates. Atlassian's 1,000+ respondent State of Product 2026
reports balancing projects, priorities, and capacity (39%), prioritization
(37%), strategy (36%), customer insight (33%), stakeholder alignment (31%), and
demonstrating impact (29%) among the most significant challenges. Product
Focus's 677-person 2026 survey reports too much firefighting (58%), lack of
resource (38%), weak or missing strategy (33%), and prioritization (29%).
ProductPlan's 250-leader 2026 study says more than 60% of prioritization
frameworks are overridden by leadership escalations and becoming
outcome-focused remains a top challenge.

Driftline targets the seam connecting those findings: preserve the evidence and
dissent behind a choice, bind authority and rollback before acting, then return
the measured result to the same decision. These surveys establish market pain;
they do not establish Driftline adoption or customer value.

## What it does

Driftline first watches active commitments for decision debt: fresh evidence
that contradicts a bet, an overdue measurement, or a breached guardrail. It
creates a cited decision-inbox item with the affected commitment, why it matters
now, what evidence is still missing, and the next bounded decision. It then
takes that commitment through five visible stages:

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

In the unreleased candidate, that same approval also executes one bounded
internal allocation in Driftline's own decision state. The receipt exposes its
generation, segment, and status, states **external writes: none**, and the
durable named-human approver and approval time remain visible after refresh.
The guardrail automatically completes or rolls the allocation back before any
reopen. This is
judge-visible action with an honest authority boundary, not a simulated customer
system write. A PM-provided decision never receives a synthetic outcome: after
the review window, the PM attaches the actual primary and risk aggregates, both
labeled unverified. Success resolves only when both metrics support it; a risk
breach rolls the action back and reopens the case. An opaque return link restores
the same non-confidential case after the review window as a read-only view. A
separate HttpOnly, case-specific capability in the originating browser is
required for approval or measurement; the UI warns that shared links must never
contain secret or customer-identifying data.

For a real PM session, the intake also preserves up to four additional redacted
research, support, analytics, or product-surface observations as separately
cited evidence. The PM records when it was observed and whether it supports or
contradicts the active commitment; Driftline never treats a user-entered source
label as proof that the source was independently connected or observed.
Expired cases fail closed at read and mutation boundaries rather than waiting
for background TTL deletion.

The Decision Twin runs on Driftline's durable action foundation. Approved public
sources become immutable before/after snapshots, SHA-256 evidence hashes, and
stable retry-safe identities. Cloud Tasks invokes the ADK workflow; deterministic
policy gates every consequential transition. In the signed tenant lane, the same
engine claims one credential-free operation before a least-privilege Jira action,
reconciles an interrupted attempt against that same ID, reuses rather than
duplicates the marker, and reverses only Driftline-owned state.

The public judge lane is deliberately packet-safe and requires no credentials.
It proves the full Gemini/ADK evidence, dissent, approval, autonomous outcome,
and generation-reopen journey without granting anonymous visitors access to an
external system.

## Proof of action

The current verified release serves application Git SHA
`03ec8f12fc23d265c89b462a345a5b599a6411e8` on Cloud Run revision
`driftline-00305-xln` from Cloud Build
`c01bec2e-a950-407c-873b-b1d4fdc6bae6`. `/health`, the Cloud Run revision, and
Artifact Registry all resolve to immutable digest
`sha256:fca505ce56c6bd933f9cde8d55ff1e4ea7f9cad099d6fe39e8bb8321c96ea6d3`
(verified August 25, 2026). That application commit is preserved in public
`main` history. GitHub Actions run `32923233214` passed backend,
frontend, standalone-image, dependency, and repository-hygiene gates on that
same merge commit.

Firebase Hosting serves the stable `driftline-ops.web.app` judge URL and
rewrites application traffic to that Cloud Run service. Google Analytics is
disabled; the facade exists for stable, credential-free judge access rather
than a separate application runtime.

The live browser proof ran the Decision Twin from generation 1 through a
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
browser console was clean on desktop and at a 390-pixel viewport. A fresh August
26 mobile run again reached generation 2 with rollback selected, the approver
cleared, and 7/7 policy checks.

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
- **Firebase Hosting** for the stable public judge URL and rewrite to Cloud Run.
- **Cloud Run** for the FastAPI API, workflow runtime, and React operations console.
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
- Autonomous Decision Debt Radar with cited triggers, severity, missing
  evidence, and compounding generation history
- Continuous PM operating loop with honest evidence-harvest modes, preserved
  stakeholder disagreement, approval-bound execution, scheduled measurement,
  and sample-sized product memory
- Ten-step state rail from observed source change through measured learning;
  completion is derived from durable case state rather than model narration
- Immutable evidence diff and full SHA-256 provenance
- Stable, retry-safe Change Card identity
- Gemini-generated impact map across four named owner surfaces
- Evidence-cited decision options with tradeoffs and rollback
- Deterministic human approval gate outside model authority
- Durable async execution and run recovery
- Idempotent, reversible Jira action in the signed tenant lane
- Append-only activity, source memory, and reversal history
- Trace-to-eval gate covering 14 independent safety/usefulness cases
- Decision Twin policy gate covering 10/10 provenance, authority, lineage,
  operating-loop, and memory-calibration contracts
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
- 521 backend tests, Ruff, the frontend production build, and all 14 trace
  evaluation cases passing at the current local-candidate checkpoint
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

Driftline continued earlier product ideation. Its implementation began during
the contest period from an entrant-supplied archive,
`driftline-source.tar.gz` (SHA-256
`9026ee2eccc94fd925ec00a54228c8b858442baaf8ac695e2ca56f54bbce37b0`).
Its 50 regular files are timestamped August 18, 2026 and included the initial
FastAPI/Google ADK backend, React frontend, tests, deployment and dependency
files, submission drafts, and two concept images. The Git repository began
later that morning and materially evolved those files. The entry does not claim
that the earlier ideation originated during the contest.

The public GitHub repository was created at 13:57:39Z, the dedicated Google
Cloud project at 14:14:30Z, and the first successful Cloud Build at 20:23:59Z
that day. The archive hash, 50-file manifest, member timestamp window, Git root,
repository creation, project creation, and first build are independently
recheckable through `submission/ORIGINALITY_PROVENANCE.md` and
`scripts/verify_contest_provenance.sh`. The entrant must still personally
confirm ownership/rights and accept the live eligibility terms.

The locked third-party runtime and build inventory is documented in
`submission/THIRD_PARTY_DISCLOSURE.md` and fails closed on missing license
evidence or review-required strong-copyleft/source-available license families.

## What's next

The next milestone is a small independent Product Management or fractional
product-leader pilot using one real, currently open decision and paired
before/after timing. Until then, Driftline will
describe its live deployment as engineering proof rather than customer ROI.

Market references: [Atlassian State of Product
2026](https://www.atlassian.com/software/jira/product-discovery/resources/state-of-product-2026),
[Product Focus 2026 profession
survey](https://www.productfocus.com/product-management-resources/profession-survey/),
and [ProductPlan State of Product Management
2026](https://www.productplan.com/ebooks/the-state-of-product-management-report-2026).
