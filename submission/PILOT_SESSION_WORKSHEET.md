# Driftline real-decision pilot worksheet

Status: local draft only. Nothing in this worksheet authorizes publication, attribution, product deployment, or external contact.

## Participant and consent

- Date:
- Facilitator:
- Participant role:
- Company stage:
- Decision authority: owner / recommender / advisor
- Independent of the Driftline build, judging, and paid implementation work: yes / no
- Recruitment channel: organic opt-in / paid research panel / existing relationship / referral
- Participant research incentive (USD; zero if none):
- May Driftline process the redacted inputs during this private session? yes / no
- May anonymized aggregate results be retained? yes / no
- May a quote be requested later under separate written approval? yes / no
- Raw inputs to delete after session:

Do not enter customer-confidential, personal, privileged, regulated, security-sensitive, or contract-restricted information.

## Qualification gate

- Real decision due within 30 days:
- At least two plausible options:
- Meaningful downside if wrong:
- Named human decision owner:
- Safe redaction is possible:

Stop the session if any answer above is no.

## Before Driftline

- Decision question:
- Current commitment:
- Deadline and reason it matters now:
- Participant's current preferred option:
- Confidence, 1–7:
- Time already spent on this decision:
- Strongest signal in favor:
- Strongest risk signal:
- Most important stakeholder disagreement:

## Operating contract

- Affected segment:
- Action owner:
- Primary outcome metric:
- Metric unit:
- Current outcome baseline:
- Success direction: at least / at most
- Success threshold:
- Risk guardrail metric:
- Current risk baseline:
- Stop direction: at least / at most
- Stop threshold:
- Review window: 3 / 7 / 14 / 30 days
- Smallest reversible action:
- Rollback action:

## Evidence check

For each input, record source, observed date, affected segment, and whether it is verified or PM-provided.

| Input | Source | Date | Segment | Verified? | Direction |
|---|---|---|---|---|---|
| 1 |  |  |  |  | supports / contradicts |
| 2 |  |  |  |  | supports / contradicts |
| 3 |  |  |  |  | supports / contradicts |
| 4 |  |  |  |  | supports / contradicts |
| 5 |  |  |  |  | supports / contradicts |

## After Driftline

- Recommended option:
- Participant's final option:
- Confidence, 1–7:
- Time from complete intake to defensible brief:
- Decision changed / sharpened / unchanged:
- Strongest useful disagreement exposed:
- Unsupported inference or citation error found:
- Every generated citation opened and reviewed: yes / no
- Most important missing evidence:
- Would this replace a meeting, document, or tool? Which one?
- Largest adoption blocker:

## Review-window follow-up

Complete this only from observed, non-confidential aggregate values. Do not
estimate or substitute a demo fixture.

- Follow-up date:
- Measurement source label:
- Observed primary outcome and unit:
- Observed risk guardrail and unit:
- Driftline verdict: validated / invalidated / inconclusive
- Internal action: completed / rolled back / still active
- Decision generation after evaluation:
- Did the participant agree the result matched the precommitted thresholds?
- What did the team actually do next?

## Costly commitment

Check only behavior that actually occurred:

- [ ] Scheduled a second live decision
- [ ] Invited a teammate or decision owner
- [ ] Offered a qualified introduction
- [ ] Asked about a paid pilot
- [ ] Agreed to discuss price
- [ ] Granted separately scoped permission for an anonymized result
- [ ] None

Praise, feature requests, and “keep me posted” do not count as demand.
Recruiting fees and participant incentives are research costs, never customer revenue.

## Evidence-safe result statement

Use only after the fields above are complete and the participant has approved the exact scope:

> An anonymized [role] at a [company stage] company used Driftline on a real [decision type] decision due within [timeframe]. The workflow [changed / sharpened / did not change] the decision, moved stated confidence from [before] to [after], and produced a bounded operating contract in [minutes]. The participant's next commitment was [observable action].

Never substitute unobserved ROI, revenue, retention, time savings, or customer status.

## Machine-checked evidence handoff

Copy `docs/validation/real-pm-pilot-template.json` to a private location and
transcribe only the bounded categories above. Do not add identity or raw-data
fields. Run `scripts/summarize_real_pm_pilot.py`; it will classify the session,
public-consent gate, commercial evidence, and outcome status independently.
Keep the source JSON private. A generated public statement is still subject to
the participant's exact consent scope and entrant review.
