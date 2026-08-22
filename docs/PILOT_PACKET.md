# Driftline pilot packet

This packet is the shortest honest path from a live Driftline connector check
to a real, reviewable pilot. It is intentionally aggregate-only: no customer
names, CRM records, source bodies, interview transcripts, credentials, or
private opportunity identifiers belong in Driftline.

## What qualifies as a real pilot

Use one named product-marketing, competitive-intelligence, enablement, or
RevOps team that agrees to a time-boxed evaluation. A valid cohort has:

1. A real change signal and at least one internal destination that the team
   already maintains.
2. A baseline period using the team's existing process.
3. A Driftline period using the same class of change and an approval-gated
   handoff.
4. A human reviewer who can reconcile the aggregate result to a dated pilot log
   or interview artifact.

The public synthetic fixtures and the isolated Driftline dogfood environment
are useful for product QA, but they are not customer evidence. Do not submit
them as a customer pilot or ROI claim.

## Recommended five-day pilot

| Day | Activity | Record |
| --- | --- | --- |
| 0 | Agree on one change class, owners, sources, and the write boundary | signed scope note |
| 1–2 | Observe 2–5 comparable changes with the current process | baseline minutes and owner-ready timestamp |
| 3–5 | Run the same class through Driftline; keep the human gate on | Driftline minutes, owner, action status, reversal |
| 5 | Review the evidence and interview the operator | aggregate outcome record and evidence reference |

Measure only what the team can verify:

- minutes from change observed to owner-ready artifact;
- changes with a named owner within 24 hours;
- action items completed within seven days;
- reversals or reopens;
- willingness to pay, revenue, win-rate, or retention only when the team
  supplies a separate dated artifact supporting the number.

Do not infer revenue lift from faster workflow execution. Keep those fields
`not_measured` until the team provides a defensible source.

## Human review and privacy

Before a pilot starts, confirm the team has permission to connect the selected
Jira, Confluence, Slack, GitHub, or Salesforce tenant. Begin with aggregate
reads. Enable at most one reversible write after the team approves the exact
scope. Use a tenant-specific secret and least-privilege operation scope. A
participant may revoke access or stop the pilot at any time.

The reviewer should retain the source artifact outside Driftline and give the
measurement ledger only a stable `https://`, `gs://`, or `artifact://` reference.
Driftline stores the aggregate measurement as
`operator_reported_unverified` until the reviewer reconciles it.

## Record the aggregate result

The signed helper below reads only the isolated tenant signer from Secret
Manager; it never accepts a provider credential and never prints the signer.

~~~bash
DRIFTLINE_OPERATOR='Named pilot operator' \
DRIFTLINE_COHORT_LABEL='pmm-week-1' \
DRIFTLINE_SOURCE_TYPE='pilot_log' \
DRIFTLINE_CHANGES_OBSERVED='3' \
DRIFTLINE_BASELINE_MINUTES='150' \
DRIFTLINE_MINUTES='78' \
DRIFTLINE_EVIDENCE_REF='gs://private-pilot-artifacts/2026-08-21-pmm-week-1.json' \
bash scripts/record_pilot_measurement.sh
~~~

Replace every example value with measured evidence. The example is a command
shape, not a result. After recording, use the signed
`GET /api/ops/pilot-report` route for the tenant-filtered delta. The public
console should continue to say `not_measured` until a real cohort is recorded.

The authenticated Pilot measurement panel also offers **Download pilot packet**
(`GET /api/ops/pilot-packet`). This is a reviewer-friendly Markdown export of
the signed, tenant-filtered aggregate report. It intentionally omits evidence
references, customer identifiers, raw source bodies, CRM records, and
credentials; reconcile those details outside Driftline and keep only the stable
artifact reference in the measurement ledger. The packet also includes a
separate **Driftline operational telemetry (not customer proof)** section with
bounded workflow count, source observations, historical owner-action closures,
approval latency, owner-action cycle time, and the ratio of repeated no-op
observations to material ledger changes. Repeatable demo replays are
intentionally packet-safe and do not mutate this ledger; the no-op signal shows
whether a monitor is filtering repeated snapshots instead of manufacturing
work. Those values make the pilot review operationally useful while remaining explicitly
distinct from customer time saved, revenue lift, retention, or willingness-to-
pay evidence.

## Five-question closeout

1. Did the same change reach an owner faster, with a dated before/after record?
2. Did more downstream work actually close, rather than merely get drafted?
3. Did the team accept the evidence and approval boundary?
4. Which budget owner would pay, and what result would justify renewal?
5. What should Driftline stop doing or narrow after the pilot?

The pilot is a validation gate, not a marketing exercise. Keep claims limited
to the evidence the participant can reproduce.
