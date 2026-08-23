# Internal technical pilot — 2026-08-23

This record is an internal engineering pilot of the isolated Driftline
deployment. It is not a customer pilot and must not be used as evidence of
time saved, revenue lift, retention, willingness to pay, or product-market fit.

## Question

Can one evidence-bound change move through Driftline's real control plane and
reach one least-privilege downstream system without losing its evidence,
approval boundary, idempotency, or rollback semantics?

## Fixture and evidence

- Change: pinned competitor pricing snapshot (`Competitor pricing snapshot`).
- Evidence hash: `3b2df1ed8f635d1cc7ab425f675df0baa9bac941aaeddbfbca81ecada501d957`.
- Mapped artifact: `Pricing battlecard`.
- Owner: `Product Marketing`.
- Public data is synthetic/pinned and explicitly labeled in the console.

## Production control-plane run

The live verifier exercised the deployed Cloud Run service in the isolated
`driftline-hackathon-2026` project:

- ADK/Gemini run: job `job-737f3c871329`, workflow
  `0294b699-19b4-4888-9c2c-9ab2fdf7d588`.
- Model/execution: `gemini-3.5-flash` through `google_adk`.
- Result: `needs_approval`, two allowlisted tools, four mapped artifacts, five
  audit events, two decision options, and trace evaluation
  `eval-a8a6ae0dd580` at 100% overall/safety/usefulness.
- Public approval/undo safety run: job `job-6014eaf19c24`, workflow
  `8c5febd4-4899-46c3-a306-9c21601f49c2`; the Driftline-owned packet was
  completed and then reversed with `external_write=false` and
  `external_systems_changed=false`.

These runs prove the deployed workflow and packet-safe public boundary. They do
not prove a customer's business outcome.

## Real Jira downstream round trip

Using the same tenant-scoped Secret Manager binding as the connector
(`driftline-tenant-driftline-demo-jira`), the local adapter was run against the
isolated free Jira project `KAN` through its Atlassian gateway. The token was
read directly by `gcloud` into the process and was never printed, persisted in
the repository, or sent to the browser.

The guarded run performed this sequence:

1. Create or reactivate one marker `Task` for the evidence-bound action.
2. Repeat the exact request and verify marker idempotency (`reused` on retry).
3. Reverse only Driftline-owned Jira state; keep the issue and append the
   reversal comment/label.

Observed result: marker `KAN-20` was created on the first run, reactivated on
the next run, reused idempotently on retry, and finally reversed. Re-running
the same command is safe; it does not delete or mutate unrelated Jira work.

Reproduce only when an external write is intended:

```bash
DRIFTLINE_JIRA_LIVE_WRITE=1 ./scripts/verify_jira_roundtrip.sh
```

The current public judge lane intentionally cannot invoke Jira and reports
`external_write=false`. This record is an adapter-level external proof, not a
claim that the anonymous console can write Jira. A fresh signed hosted HTTP
round trip on the current candidate remains a separate verification gate; the
historical hosted OIDC proof is retained in `docs/RESOURCE_INVENTORY.md`.

## Measurements and limits

| Measure | Result | Interpretation |
| --- | --- | --- |
| Workflow completion | Verified | Engineering/control-plane behavior only |
| Evidence/hash continuity | Verified | Evidence is carried into the action and audit records |
| Jira create/reuse/reverse | Verified | One isolated project, one scoped tenant credential |
| Idempotent retry | Verified | Same marker does not create duplicate work |
| Rollback | Verified | Driftline-owned Jira state is reversed without deletion |
| Customer baseline | `not_measured` | No external customer participated |
| Time saved | `not_measured` | No paired customer baseline/Driftline timing |
| Revenue, win rate, retention | `not_measured` | No customer outcome data |
| Willingness to pay | `not_measured` | No customer interview or purchase evidence |

The next evidence step is a real operator pilot with a dated before/after
baseline, a bounded change set, and aggregate signed measurements. Until that
exists, deployment telemetry and trace scores remain engineering evidence only.
