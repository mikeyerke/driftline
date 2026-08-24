# Driftline decision-utility validation study

## Claim under test

For a consequential product decision, Driftline helps a PM produce a more
complete, evidence-linked, falsifiable decision faster than their current
workflow—without hiding dissent or removing human control.

This study is designed to generate decision-grade evidence, not flattering quotes. Do not report results until real participants complete the tasks.

## Participants

- Recruit 6–8 people who currently own product, growth, product operations, or
  product-marketing decisions.
- Exclude Driftline builders and anyone who has rehearsed the demo.
- Assign anonymous IDs (`P01`, `P02`, …). Do not store names, emails, company names, customer data, or raw source documents in the results file.
- Counterbalance order: odd participant IDs do Manual → Driftline; even IDs do Driftline → Manual.

## Two matched decision tasks

Use the repository's synthetic fixtures only.

1. Onboarding redesign: small-team activation improves while enterprise
   activation falls and permission setup becomes confusing.
2. Packaging change: self-serve conversion improves while sales-assisted deal
   quality and support load move in the wrong direction.

The participant receives the before/after evidence and must decide what should happen next. In the manual condition, provide a blank document. In the Driftline condition, use Judge Mode from a fresh run.

## Success rubric (0–5 coverage)

Award one point for each observable element:

1. Cites the exact evidence and identifies a material contradiction.
2. Compares at least three plausible options rather than defending only one.
3. Preserves a meaningful dissenting view or unresolved unknown.
4. Defines a measurable success threshold, guardrail, and stop condition.
5. Names the human owner and explains what outcome would reopen the decision.

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
- “What would cause you to reverse or reopen this decision?”
- “Would this earn a place in your weekly workflow? Why or why not?”

## Measures and win thresholds

Primary thresholds, chosen before data collection:

- Median task time improves by at least 30%.
- Median decision-quality coverage improves by at least 1 point on the 0–5 rubric.
- At least 5 of 6 participants say they would use it weekly or for material changes.
- No participant believes the agent can approve itself or silently change a customer-facing system.

Secondary evidence:

- Confidence delta on a 1–5 scale.
- Number of moderator hints (target: zero).
- Learning-loop comprehension: participant can explain why a measured outcome
  reopens the same case generation instead of creating an unrelated decision.
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
