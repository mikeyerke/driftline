# Driftline decision-utility validation study

## Claim under test

For a verified promise change, Driftline helps a product-marketing or revenue-enablement operator produce a more complete, evidence-linked, owner-ready response faster than their current manual workflow—without removing human control.

This study is designed to generate decision-grade evidence, not flattering quotes. Do not report results until real participants complete the tasks.

## Participants

- Recruit 6–8 people who currently own product marketing, competitive intelligence, enablement, deal-desk, or revenue operations work.
- Exclude Driftline builders and anyone who has rehearsed the demo.
- Assign anonymous IDs (`P01`, `P02`, …). Do not store names, emails, company names, customer data, or raw source documents in the results file.
- Counterbalance order: odd participant IDs do Manual → Driftline; even IDs do Driftline → Manual.

## Two matched tasks

Use the repository's synthetic fixtures only.

1. Own-pricing change: unlimited audit-log retention becomes 365 days.
2. Competitor-pricing change: a public competitor changes packaging or price.

The participant receives the before/after evidence and must decide what should happen next. In the manual condition, provide a blank document. In the Driftline condition, use Judge Mode from a fresh run.

## Success rubric (0–5 coverage)

Award one point for each observable element:

1. Cites the exact source change.
2. Identifies at least three affected downstream surfaces.
3. Names an owner for every proposed action.
4. Separates immediate packet work from owner review or queued follow-up.
5. Includes an approval/audit/rollback path.

Stop the timer when the participant says the response is ready for another owner to execute. Do not coach toward the rubric.

## Session script (25 minutes)

1. Consent and context — 2 minutes.
2. Condition A task — up to 8 minutes.
3. Confidence rating (1–5) — 1 minute.
4. Condition B task — up to 8 minutes.
5. Confidence, weekly-use, and open questions — 6 minutes.

Use these neutral prompts only:

- “What would you do next?”
- “What, if anything, would another owner still need?”
- “What evidence would make you trust or reject this recommendation?”
- “Where did you hesitate?”
- “Would this earn a place in your weekly workflow? Why or why not?”

## Measures and win thresholds

Primary thresholds, chosen before data collection:

- Median task time improves by at least 30%.
- Median artifact/owner coverage improves by at least 1 point on the 0–5 rubric.
- At least 5 of 6 participants say they would use it weekly or for material changes.
- No participant believes the agent can approve itself or silently change a customer-facing system.

Secondary evidence:

- Confidence delta on a 1–5 scale.
- Number of moderator hints (target: zero).
- Recovery comprehension: participant can explain what “reconcile same operation” does.
- One concise quote may be used only with explicit participant permission.

## Data capture

Copy `docs/validation/results-template.csv` to a private working file and enter anonymous observations. Run:

```bash
python scripts/summarize_validation.py path/to/results.csv --output path/to/summary.md
```

The generated report calculates medians and directional deltas. Review raw rows for protocol deviations before publishing any aggregate. A missing or incomplete sample is reported as incomplete—not converted into a success claim.

## Facilitator QA

- Use the same laptop, browser, and network for both conditions.
- Start each Driftline condition from a fresh source run.
- Do not count loading time caused by a known service outage; record the deviation.
- Never substitute a builder walkthrough for an observed participant task.
- Archive the study date, app release SHA, fixture IDs, and anonymized CSV hash.
- Record negative and confusing moments verbatim; those are the next build queue.
