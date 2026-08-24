# Driftline Decision Twin demo — 3:48 target

The official limit is four minutes. Record one continuous 1080p product take
with a visible deployed URL and finish with Google Cloud proof. Do not claim a
customer study, BigQuery deployment, or live council unless each is verifiable
on the serving SHA.

## 0:00–0:20 — The product decision bottleneck

**Screen:** Decision Room hero and the pinned onboarding decision.

**Narration:** “PMs do not lack opinions. They lack a defensible way to combine
contradictory evidence, commit to a test, and learn without losing the original
reasoning. Driftline is a Decision Twin: an evidence-to-outcome control room.”

## 0:20–0:52 — Evidence with provenance

**Screen:** Start the council. Open the evidence graph and move through usage,
customer, strategy, and feasibility nodes.

**Narration:** “Small teams activate faster after the redesign, while enterprise
activation falls and permission setup becomes confusing. Every claim keeps its
source, metric, segment, observation window, and confidence. Aggregate product
metrics can come through a parameterized, dry-run-checked, bytes-capped BigQuery
adapter; the fixture remains explicitly labeled when live data is unavailable.”

## 0:52–1:28 — Independent ADK council and visible dissent

**Screen:** Show the five council positions and pause on the challenger dissent.

**Narration:** “Five independent Google ADK agents inspect bounded projections:
customer, usage, strategy, feasibility, and challenger. They cannot approve or
write anywhere. A single synthesis turn preserves citations and disagreement
instead of averaging it away. Here the council rejects a universal rollout.”

## 1:28–2:02 — Counterfactual decision quality

**Screen:** Compare ship, rollback, segment, and defer. Switch tabs and show
expected upside, downside, reversibility, unknowns, and cited evidence.

**Narration:** “Driftline makes the alternatives concrete before anyone commits.
Shipping protects momentum but risks enterprise conversion. Rolling back loses
small-team gains. Deferring buys information but misses the launch window. A
segmented rollout preserves upside and contains the observed failure mode.”

## 2:02–2:40 — Human authority becomes an experiment

**Screen:** Approve the segmented option and show the experiment receipt.

**Narration:** “The model recommends; a named human authorizes. Approval freezes
a falsifiable experiment: target segment, success metric, enterprise guardrail,
stop condition, owner, and review date. Driftline rejects stale generations and
conflicting approvals with compare-and-set persistence.”

## 2:40–3:15 — The wow moment: outcome reopens the same decision

**Screen:** Apply the measured demo outcome. Show the learning receipt and the
new case generation with prior lineage retained.

**Narration:** “A decision is not done when a ticket moves. The measured outcome
is evaluated against the thresholds committed at approval. If a guardrail
breaks, Driftline writes a learning receipt and reopens the same decision as a
new generation. The evidence, dissent, approval, and result remain linked, so
the organization compounds judgment instead of repeating debate.”

## 3:15–3:38 — Google architecture and bounded cost

**Screen:** Architecture view, evaluation score, then Cloud Run/Firestore/
BigQuery proof for the exact serving SHA.

**Narration:** “Cloud Run hosts the control room. Firestore stores cases and
lineage. Google ADK and Gemini power the bounded council. BigQuery supplies
privacy-thresholded aggregates. A deterministic seven-check evaluator tests
provenance, role independence, disagreement, citations, falsifiability, human
authority, and reopening. Cloud Run scales to zero and one instance, model
calls are quota-bound, and every query has a billed-bytes ceiling.”

## 3:38–3:48 — Close

**Screen:** Decision Room hero with the learning receipt visible.

**Narration:** “Driftline turns product judgment from a meeting artifact into a
measurable, auditable learning loop: evidence, dissent, decision, outcome.”

## Recording gates

- Serving `/health` SHA equals the release commit.
- `./scripts/verify_decision_twin.sh` passes against the public URL.
- Live council proof shows `google_adk` and `gemini-3.5-flash`; otherwise narrate
  the visible deterministic fallback honestly.
- BigQuery is provisioned and the production result reports its aggregate
  source before claiming it in narration.
- No invented user, ROI, retention, or revenue result appears on screen.
