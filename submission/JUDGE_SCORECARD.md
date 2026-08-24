# Driftline judge scorecard

This is the shortest rubric-aligned review path for the Decision Twin release
candidate. The current public runtime still serves `e38facc`; run every hosted
gate again after deploying the candidate. Evaluation fixtures are labeled and
no customer ROI is claimed.

Official brief: [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/)

## 40% — Innovation and PM utility

**Core problem:** PMs make consequential decisions from contradictory usage,
customer, strategy, and delivery evidence. The rationale fragments across
meetings and documents; success criteria are rarely frozen; measured outcomes
do not reliably update the original decision.

**What is different:** Driftline turns decision debt into a closed learning
loop. A provenance-preserving evidence graph feeds five independent specialist
positions. The product keeps dissent visible, compares four concrete
counterfactuals, converts a named human choice into a falsifiable experiment,
then evaluates the outcome and reopens the same case generation when evidence
invalidates the plan. It is not a generic chat assistant, summary, or autonomous
roadmap manager.

**Judge proof:**

1. Open the Decision Room and run the pinned onboarding case.
2. Inspect usage, customer, strategy, and feasibility evidence with provenance.
3. Show the customer, usage, strategy, feasibility, and challenger council
   positions; pause on explicit dissent and citations.
4. Compare ship, rollback, segment, and defer across upside, downside,
   reversibility, unknowns, and supporting evidence.
5. Approve the segmented experiment as a named human; inspect its success,
   guardrail, stop, owner, and review conditions.
6. Apply the measured demo outcome; show the learning receipt and the same case
   reopened with a new generation and preserved lineage.

## 30% — Architectural discipline and Google stack

```text
bounded evidence + BigQuery aggregates
  → five independent Google ADK / Gemini specialists
  → one bounded synthesis preserving citations and dissent
  → deterministic counterfactual and policy validation
  → named-human experiment approval
  → Firestore case, approval, outcome, and generation lineage
  → deterministic seven-check evaluation
  → measured outcome reopens or closes the decision
```

- Google ADK agents receive separate, minimal evidence projections and have no
  approval or connector-write tool.
- Gemini output uses strict schemas; invalid live output fails into an explicitly
  labeled deterministic demo fallback rather than masquerading as live AI.
- BigQuery accepts only server-allowlisted metrics and segments. Values are
  parameterized, every query dry-runs first, cohorts below 25 are rejected, and
  billed bytes are capped at 50 MB in the deployment configuration.
- Firestore compare-and-set transitions reject stale generations and conflicting
  approvals. Outcomes preserve prior decisions instead of overwriting history.
- Cost boundaries include Cloud Run min 0/max 1, six reserved model calls per
  council, BigQuery bytes caps, bounded retries, and budget alerts at $25, $75,
  $150, $225, $285, and $300. Budget alerts do not falsely claim to hard-cap
  Google Cloud spend.

## 30% — Demo and production readiness

Local release gate:

```bash
cd backend && .venv/bin/ruff check app tests && .venv/bin/pytest -q
cd ../frontend && npm run build
cd .. && ./scripts/verify_frontend_contract.sh
for script in scripts/*.sh; do bash -n "$script"; done
git diff --check
```

After an authenticated Google operator provisions and deploys the exact PR SHA:

```bash
./scripts/update_budget_guardrail.sh
./scripts/provision_decision_twin_bigquery.sh
./scripts/deploy.sh
BASE=https://driftline-ops.web.app ./scripts/verify_decision_twin.sh
./scripts/verify_live_agent.sh
./scripts/verify_public_approval_undo.sh
./scripts/verify_production.sh
./scripts/verify_trace_eval.sh
```

The Decision Twin verifier fails unless production proves live Google ADK mode,
BigQuery aggregate evidence, a named-human approval, outcome-driven reopening,
preserved lineage, and a 100% seven-check evaluation. Existing checks still
protect the evidence-bound change-to-action workflow and reversible packet lane.

## Honest limits

- The showcased onboarding case and measured outcome are deterministic fixtures,
  not customer research or commercial traction.
- BigQuery provisioning and the new Cloud Run candidate require an authenticated
  Google Cloud operator; committed infrastructure is not deployment proof.
- The current public URL does not yet serve Decision Twin.
- A real 6–8 PM usability study, willingness-to-pay signal, and outcome pilot
  remain human dependencies and must be completed before making market claims.
- No feature can guarantee a hackathon win. The strongest defensible claim is a
  technically bounded, unusually complete evidence-to-outcome learning loop.
