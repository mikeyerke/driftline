# Driftline — when the market moves, the work moves

## Submission links

- Hosted application: https://driftline-xvxczqg62a-uc.a.run.app/
- Public source repository: https://github.com/mikeyerke/driftline
- Architecture diagram: https://github.com/mikeyerke/driftline/blob/main/docs/architecture.md
- Judge scorecard: https://github.com/mikeyerke/driftline/blob/main/docs/JUDGE_SCORECARD.md
- Cloud/resource evidence: https://github.com/mikeyerke/driftline/blob/main/docs/RESOURCE_INVENTORY.md
- Rules and eligibility evidence: https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md
- Demonstration video: held for final owner review; no upload or submission has been made
- Pending-approval frame: [`live-pending-approval-2026-08-20.jpg`](assets/live-pending-approval-2026-08-20.jpg)
- Completed frame: [`live-completed-2026-08-20.jpg`](assets/live-completed-2026-08-20.jpg)

## Category

**Taskmaster.** Driftline turns a monitored change into a coordinated,
evidence-bound work package and pauses for a human decision before anything
can be published. It is a complete asynchronous workflow, not a chat surface.
It is not claiming Fortified Enterprise Fleet: the public build does not claim
that track's enterprise agent registry, Model Armor, or cross-department
production data plane.

## The problem

A competitor changes one pricing sentence. Product Marketing sees the alert,
but the comparison map, battlecard, deal-desk guidance, enablement notes, and
executive narrative drift out of sync. The expensive work is not detecting the
sentence; it is proving what changed, deciding what it means, coordinating the
owners, and making a reversible update without inventing a claim.

This is the BYOF friction behind Driftline: the recurring RevOps/Product
Marketing chore of reconciling competitive signals with the internal surfaces
that sellers and decision-makers actually use. An alert is not the deliverable;
an evidence-bound, owner-routed change package is.

## The solution

Driftline is a change-to-action control plane for Product Marketing and revenue
operations. It monitors a bounded set of own-product and competitor change
surfaces, creates an append-only evidence record, maps the affected offering
and business domains, and asks Gemini to propose owner-ready updates. A
deterministic policy engine—not Gemini—decides whether the workflow may cross
the human gate.

One observed price change produces four named surfaces in the demo:

1. Comparison map — Product Marketing — re-score price/value.
2. Pricing battlecard — Product Marketing — draft the response.
3. Deal-desk guidance — RevOps — review the discount guardrail.
4. Executive weekly brief — Product Marketing — add the market signal.

Each surface carries the source evidence hash, risk, owner, proposed text,
tradeoffs, citations, and rollback plan. The operator can approve a bounded
packet, claim/complete owner work, or reopen/undo. The public evaluation lane
is intentionally packet-safe; it never pretends that an anonymous judge wrote
to a third-party system.

## What the agent actually does

1. Cloud Tasks starts a durable asynchronous scan.
2. A Google ADK coordinator uses only `inspect_source_change` and
   `get_workflow_state` to verify the source and persist Firestore state.
3. Gemini 3.5 Flash returns a strict, evidence-hash-bound impact analysis for
   all four artifacts.
4. A second Gemini 3.5 Flash Decision Copilot returns two bounded options with
   tradeoffs, citations, rollback, and artifact decisions.
5. Deterministic policy checks the evidence hash, artifact allowlist, risk, and
   human-approval requirement. The model cannot approve itself.
6. Approval persists a versioned packet and append-only audit events. Undo
   appends a reversal marker and returns the workflow to the decision state.

The public fixture moves `Competitor Pro` from `$49` to `$59` per seat per
month. It is synthetic and visibly labelled as such. The console also exposes
the append-only source ledger, recurring change memory, a bounded Gemini vision
before/after pair, owner-action telemetry, and deployment health.

## Google technology

- Gemini 3.5 Flash through Vertex AI for evidence-grounded analysis and
  Decision Copilot options.
- Google Agent Development Kit (ADK) for the coordinator, task-mode analysts,
  session runners, and allowlisted tools.
- Cloud Run for the FastAPI + React service, configured scale-to-zero and
  max-one instance for the isolated hackathon project.
- Firestore for durable workflows, source history, tenant state, and audit
  events.
- Cloud Tasks for asynchronous dispatch and bounded retries.
- Cloud Scheduler for the signed monitor cycle.
- Cloud Storage for private, versioned packets and reversal markers.
- Cloud Build and Artifact Registry for the reproducible container release.

## Architecture and safety

The React console and FastAPI API share one Cloud Run service. A scan creates a
Firestore job; Cloud Tasks sends an OIDC-authenticated request to the worker;
ADK records the model/tool trace; Firestore restores the workflow across
process restarts. The deterministic workflow engine owns approval, idempotency,
connector scope, and reversal state.

The public lane is anonymous, tenantless, and packet-only. Signed operator
requests are a separate tenant boundary. Connector credentials are held in
tenant-specific Secret Manager namespaces and are never returned to the
browser, source control, or logs. The isolated signed lane has been exercised
against Driftline-owned Jira, Confluence, Slack, and GitHub targets with
aggregate-only context reads and reversible marker operations. Those probes are
not customer data or customer ROI. Salesforce's owner-controlled callback has
been persisted as a read-only tenant connection, but the latest direct
aggregate probe returned `invalid_grant`; no Salesforce object totals or
successful CRM read are claimed until fresh consent succeeds.

The source adapter accepts pinned fixtures and exact operator-registered public
URLs only. It rejects redirects, query credentials, private addresses, and
unbounded bodies. Competitor content is an observed signal, not verified
product truth.

## Verified release evidence

The current serving release is source commit `6215311`, Cloud Build
`ddbb1aea-fa8c-4618-bda4-bba1468f852c`, and Cloud Run revision
`driftline-00156-k4k` at 100% traffic in project `driftline-hackathon-2026`.
The immutable image digest is
`sha256:2e2fd930a57591c99f99d2e084bd6e6dcd7dc923d778c97357596760b89372d1`.

The current release includes the visible Salesforce reauthorization recovery
control and an explicit `reauthorization_required` health response when a
stored refresh token is rejected. The callback metadata and tenant-scoped
secret pointer are durable, but no Salesforce object totals or successful CRM
read are claimed until fresh consent succeeds.

- Local gate for the current source: 264 backend tests passed, the focused
  Salesforce connector suite passed 37 tests, Ruff passed, and the frontend
  production build passed. The current serving image was built from the
  already-verified application code; the additional local tests protect the
  tenant credential broker and aggregate Salesforce query boundary.
- CI: GitHub Actions run `32538796189` passed the backend suite, Ruff,
  frontend build, standalone image build, and repository hygiene.
- Production check: `scripts/verify_production.sh` passed Firestore,
  Cloud Tasks, Scheduler, uptime, alerting, IAM, Artifact Registry retention,
  and zero recent Cloud Run errors.
- Live agent check: fresh job `job-400c45830923` / workflow
  `d5e25360-43c2-4911-95cf-7ea9de72f812` returned `needs_approval`,
  `public_source`, `gemini-3.5-flash`, `google_adk`, two allowlisted tools,
  four artifacts, five audit events, and two decision options.
- Current-revision logged-out browser QA visibly rendered
  `Impact analysis · gemini structured`, the Gemini summary/rationale, the
  Decision Copilot, and the approval gate; the scripted live proof above is
  the durable source of the current job/workflow identifiers.
- Current-revision browser journey (job `job-f1bfaa9665c9`, workflow
  `38da400c-5581-47cc-9210-5126061006bc`) completed scan -> approval -> undo.
  The undo response persisted action record
  `action-63355af11e1c35cb5150` as `reversed`; Jira, Confluence, and Slack
  all returned `external_write=false` in the public packet-safe lane.
- Approval/undo check: fresh job `job-9d91cfb22e0a` / workflow
  `f524d78c-3535-465a-a3e5-4c1ac8711d73` persisted the packet, reversed the
  operational output, and returned `external_write=false` and
  `external_systems_changed=false`.
- Background proof: the isolated `driftline-monitor` Cloud Scheduler job was
  manually triggered and Cloud Logging recorded an OIDC-authenticated HTTP 200
  request to `/api/scheduler/tick` on the serving Cloud Run revision. Cadence
  rules deferred healthy sources that were not due, so no synthetic monitoring
  claim is made beyond the recorded delivery.
- Breadth check on the same serving revision: competitor offerings
  (`job-82ac284398b6`, workflow `a1190503-0c2f-4182-83c9-22e4879fc6e1`),
  competitor narrative/blog (`job-b8a7d0ebcf6d`, workflow
  `7a63eea4-7dec-4626-8b2b-1834a4542716`), and own terms
  (`job-ee66d880b4eb`, workflow `d5f75932-3a41-48a8-8765-d629abae9441`)
  each reached `needs_approval` with Gemini structured analysis, four mapped
  impacts, and five audit events.
- Browser QA: desktop and mobile Lighthouse navigation both scored 100 for
  accessibility, best practices, SEO, and agentic browsing (53/53 checks,
  zero failures). At 390×844, body and document widths equal the viewport and
  the console has no application messages. Below-fold ledger, monitor,
  multimodal, memory, value-proof, run-history, and telemetry reads load when
  their panels approach the viewport.

## Four-minute demo plan

1. State the problem: one competitor change creates multiple stale internal
   surfaces.
2. Click **Run scan** on the deployed URL.
3. Show the evidence diff, source hash, synthetic-data label, Gemini/ADK trace,
   four downstream owners, and the Gemini Decision Copilot options.
4. Open one artifact and the evidence modal; point out the citation and
   rollback.
5. Approve the bounded plan; show the persisted packet, owner work, timeline,
   and audit events.
6. Reopen/undo; show the reversal marker and the unchanged external-write
   flags. Scroll to the append-only history and multimodal evidence.
7. Briefly show Cloud Run/Firestore proof and the public repository.

The video must be public on YouTube or Vimeo and no longer than four minutes;
it is intentionally held until the final product review is complete.

## Findings, limitations, and honest claims

Driftline's strongest differentiated unit is not an alert. It is a
source-hash-bound Change Card that names the affected offering, owners, risk,
proposed update, citations, and rollback before anyone acts. The product has
real operational utility for a Product Marketing or competitive-intelligence
team that repeatedly reconciles public changes with internal enablement work.

What is proven: live Gemini/ADK execution, durable asynchronous state, strict
evidence binding, deterministic approval, append-only audit, reversible packet
behavior, isolated Cloud Run/Firestore architecture, and signed connector
boundaries.

What is not claimed: customer revenue lift, hours saved, retention impact,
willingness-to-pay, a multi-customer pilot, arbitrary competitor crawling,
Salesforce execution, self-serve enterprise billing/SSO, or an anonymous
third-party write. The public demo uses five pinned fixtures; a real pilot and
before/after business outcomes remain the highest-value commercial validation.

## Official links and eligibility

- [Hackathon overview](https://allthingsagentichackathon.devpost.com/)
- [Official rules](https://allthingsagentichackathon.devpost.com/rules)
- [Official judging criteria](https://allthingsagentichackathon.devpost.com/details/judging-criteria)
- [Official submission requirements](https://allthingsagentichackathon.devpost.com/details#what-to-submit)
- [Verified local rules record](https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md)

The current official deadline is **August 31, 2026 at 5:00 PM PDT** (September
1, 2026 at 00:00 UTC). The entry is designed around the Taskmaster track and
the official judging weights: operational utility 40%, architectural
discipline and technology 30%, and demo/production readiness 30%.

The project discloses that Driftline continues an earlier concept conversation
and incorporates the supplied source package; the current implementation,
deployment, verification, and documentation work was completed or materially
changed during the submission period. The public repository's first commit is
dated August 18, 2026, inside the August 3–31 submission period; that history
anchor does not misrepresent the earlier concept conversation as contest work.
