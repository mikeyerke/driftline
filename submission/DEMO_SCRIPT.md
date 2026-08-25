# Driftline Decision Twin demo — 3:48 target

The official limit is four minutes. The organizer's August 24 checklist permits
cuts to remove setup, loading, and dead air, while the judging criterion asks
for a live, unedited proof of action. Keep the core council → human approval →
measured outcome → generation-2 reopen sequence continuous and visibly tied to
one case ID; edit only outside that proof sequence. Use 1080p, show the deployed
URL in the first 10–15 seconds, and finish with Google Cloud proof. Do not claim a
customer study, BigQuery deployment, or live council unless each is verifiable
on the serving SHA.

## 0:00–0:16 — The product decision bottleneck

**Screen:** Decision Room hero and the pinned onboarding decision.

**Narration:** “A roadmap decision becomes dangerous when the evidence changes
but the commitment does not. Driftline catches that drift, compares the safest
responses, and keeps the outcome attached to the original decision.”

## 0:16–0:47 — Autonomous evidence work with provenance

**Screen:** Start the council. Open the evidence graph and move through usage,
customer, strategy, and feasibility nodes.

**Narration:** “Without a prompt loop, Driftline attaches five cited signals,
including a live privacy-thresholded BigQuery aggregate. Small teams activate
faster after the redesign, while enterprise activation falls and permission
setup becomes confusing. Every claim keeps its source and segment.”

## 0:47–1:20 — Independent ADK council and visible dissent

**Screen:** Show the five council positions and pause on the challenger dissent.

**Narration:** “Five independent Google ADK agents inspect bounded projections:
customer, usage, strategy, feasibility, and challenger. They cannot approve or
write anywhere. A single synthesis turn preserves citations and disagreement
instead of averaging it away. Here the council rejects a universal rollout.”

## 1:20–1:52 — Counterfactual decision quality

**Screen:** Compare ship, rollback, segment, and defer. Switch tabs and show
expected upside, downside, reversibility, unknowns, and cited evidence.

**Narration:** “Driftline makes the alternatives concrete before anyone commits.
Shipping protects momentum but risks enterprise conversion. Rolling back loses
small-team gains. Deferring buys information but misses the launch window. A
segmented rollout preserves upside and contains the observed failure mode.”

## 1:52–2:28 — Human authority becomes an experiment

**Screen:** Approve the segmented option and show the experiment receipt.

**Narration:** “The model recommends; a named human authorizes. Approval freezes
a falsifiable experiment: target segment, success metric, enterprise guardrail,
stop condition, owner, and review date. Driftline rejects stale generations and
conflicting approvals with compare-and-set persistence.”

## 2:28–3:05 — The wow moment: outcome reopens the same decision

**Screen:** Apply the measured demo outcome. Show the learning receipt and the
new case generation with prior lineage retained.

**Narration:** “A decision is not done when a ticket moves. The measured outcome
is evaluated against the thresholds committed at approval. If a guardrail
breaks, Driftline writes a learning receipt and reopens the same decision as a
new generation. The evidence, dissent, approval, and result remain linked, so
the organization compounds judgment instead of repeating debate.”

## 3:05–3:38 — Google architecture and bounded cost

**Screen:** Architecture view, evaluation score, then Cloud Run/Firestore/
BigQuery proof for the exact serving SHA.

**Narration:** “This is the exact serving release. Cloud Run hosts the control room. Firestore stores cases and
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
- `./scripts/release_and_verify.sh` passes against the public URL. This refreshes
  the release-bound live trace before checking the Decision Twin and production
  proof surfaces, so the architecture disclosure must show a verified gate.
- Live council proof shows `google_adk` and `gemini-3.5-flash`; otherwise narrate
  the visible deterministic fallback honestly.
- BigQuery is provisioned and the production result reports its aggregate
  source before claiming it in narration.
- No invented user, ROI, retention, or revenue result appears on screen.
- Public YouTube/Vimeo result is under four minutes, English or English-
  subtitled, and visibly shows the working agent plus Google Cloud backend.
- Submission form names Google ADK and the August 18 implementation start and
  preserves the pre-existing ideation/source-package disclosure.
- No cut occurs inside the approval → outcome → reopen proof sequence.
