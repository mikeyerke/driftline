# Driftline validation plan

Driftline currently has deployment and workflow evidence, not customer evidence. This plan keeps those claims separate and gives a buyer-facing team a short path to validate operational value without collecting sensitive customer data.

## What is already observed

- The isolated deployment records source observations, agent runs, approvals, reversals, action items, and connector outcomes in Firestore.
- `/api/ops/value-proof` reports bounded counts, observed approval latency, owner-action cycle time, action-item completion, and explicitly lists unmeasured outcomes.
- The public demo is packet-only. A signed operator lane is required before a configured connector can write.

These are product-operation facts, not proof of revenue lift, hours saved, or willingness to pay.

## PMM/PMM Ops discovery script

Ask five people who own competitive intelligence, product launches, or enablement. Do not ask for customer data or credentials.

1. “Walk me through the last competitor or market change that reached your team. Where did the signal arrive, and how long until an owner acted?”
2. “Which downstream artifacts had to change: pricing pages, battle cards, launch briefs, support guidance, CRM fields, or project work?”
3. “What evidence would you require before allowing an automated update, and which actions must remain human-approved?”
4. “How do you prove that the change was actually reflected everywhere, and what gets missed when the work is busy?”
5. “If a system reduced this coordination loop, which budget would pay for it and what measurable result would justify renewal?”

## Suggested validation thresholds

Treat these as hypotheses to test, not results:

- At least 4 of 5 interviewees report a recurring change-to-action workflow.
- At least 3 can name two or more downstream systems that must stay aligned.
- At least 3 require evidence and a human gate for high-risk edits.
- At least 2 volunteer a real, non-sensitive workflow for a time-boxed pilot.
- A paid pilot is only credible after a baseline and post-pilot measure exist for time-to-owner, artifact coverage, and reversals.

## Instrumentation that is safe to add

Use aggregate counters only: scan count, source freshness, time from detected change to approval, time from action creation to owner completion, action-item completion, connector success/failure, and reversal count. Driftline exposes approval-latency and owner-action-cycle p50/p90 from its own audit timestamps, not a customer productivity claim. Never log source credentials, customer text, or raw CRM records. Keep browser analytics optional and privacy-preserving.

When a real pilot exists, a signed operator can submit one aggregate record to
`POST /api/ops/outcomes` with a source type, cohort label, before/after minutes,
and an evidence reference. The API rejects raw customer text and marks every
record `operator_reported_unverified` until a human reconciles it to the
referenced interview, pilot log, win/loss record, or billing artifact. The
public console exposes only the redacted outcome ledger through
`GET /api/ops/outcomes`. Tenant owners can use the signed
`GET /api/ops/pilot-report` endpoint to compute before/after totals and deltas
for one cohort without returning evidence references or other tenant records.

## Open proof gaps

- No customer interviews or willingness-to-pay results are represented in the repository.
- No causal hours-saved, pipeline, win-rate, or retention claim is supported yet.
- Salesforce is a read-only context connector contract and remains prepared-only until a customer supplies an isolated OAuth configuration.
