# Driftline pilot and outcome measurement

This is the smallest honest pilot that can establish whether Driftline earns a
budget. No customer metrics are prefilled or inferred.

## Pilot design

- Recruit 3–5 product-marketing or competitive-intelligence teams.
- Use one real competitor page and one internal source per team.
- Run a two-week baseline using the team’s current process, then two weeks with
  Driftline monitoring and approval-gated handoffs.
- Keep write connectors disabled for the first week; enable one reversible Jira
  or Slack action only after the team approves the scope.
- Review every measurement against an evidence reference before labeling it
  verified.

## Minimum measurements

| Measure | Baseline | Driftline | Evidence |
| --- | ---: | ---: | --- |
| Minutes from change observed to owner-ready artifact | blank | blank | blank |
| Changes with a named owner within 24 hours | blank | blank | blank |
| Action items completed within 7 days | blank | blank | blank |
| Reversed or reopened decisions | blank | blank | blank |
| Willingness to pay (USD/month) | blank | blank | blank |
| Revenue, win-rate, or retention effect | blank | blank | blank |

Record only aggregate values through `POST /api/ops/outcomes`; never upload
customer names, raw interview text, opportunity IDs, or private CRM records.
The endpoint labels entries `operator_reported_unverified` until a human
reviews the referenced artifact.

The signed console includes a pilot-readiness checklist that is deliberately
separate from customer evidence. It confirms the tenant lane, an exact
operator-registered source, an observed tenant workflow, and an aggregate
outcome record. A checked item proves only that Driftline observed that product
event in this tenant; it does not prove customer ROI, revenue, retention, or
willingness to pay.

## Decision gates

- Continue if teams report a repeatable reduction in change-to-owner time and
  complete materially more downstream work.
- Narrow the product if teams want alerts but not automated handoffs.
- Stop or redesign if no team can name a budget owner or if the measured work
  does not improve after two weeks.

Until this pilot is run, Driftline must continue to report customer ROI,
revenue lift, retention impact, and willingness to pay as `not_measured`.
