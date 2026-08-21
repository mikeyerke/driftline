# Driftline — change should trigger action, not another meeting

## Submission links

- Hosted application: https://driftline-xvxczqg62a-uc.a.run.app/
- Source repository: https://github.com/mikeyerke/driftline
- Demonstration video: pending final live upload; the official rules require a public YouTube/Vimeo upload (not unlisted)
- Architecture diagram: https://github.com/mikeyerke/driftline/blob/main/docs/architecture.md
- Fresh live evidence frames: [pending approval](https://github.com/mikeyerke/driftline/blob/main/submission/assets/live-pending-approval-2026-08-20.jpg) and [completed workflow](https://github.com/mikeyerke/driftline/blob/main/submission/assets/live-completed-2026-08-20.jpg)

## Category

**Taskmaster.** Driftline completes a messy, multi-step change-management
workflow and takes bounded action, rather than acting as a chatbot. It is not
being entered as Fortified Enterprise Fleet because this build intentionally
does not claim a multi-agent registry, enterprise identity gateway, Model Armor,
or cross-department production data plane.

## Inspiration

A public pricing page changes one sentence. Days later, sales is still quoting
the old promise, support has a conflicting answer, and customer success has no
renewal exception path. Enterprises do not lack alerts; they lack a reliable
way to turn evidence into coordinated action.

## What it does

Driftline runs a resumable change-to-action workflow across five allowlisted
public source types: own pricing, own terms, competitor pricing, competitor
offerings, and competitor product narratives. Cloud Tasks starts the scan
asynchronously; the ADK coordinator verifies evidence, maps the affected
offering and business domains, and drafts updates for each downstream work
surface. When a change touches a contractual expectation,
deterministic policy pauses the workflow and requests a named human decision.
After approval, Driftline creates an evidence-linked public-demo packet, an owner
review item, or a queued item per artifact. Each artifact also receives a
durable human-owned action item with an idempotency key and evidence hash; a
named reviewer can claim and complete it without giving the model write access.
The packet and one approved low-risk operational output are persisted as
private, versioned Cloud Storage objects inside the isolated Driftline project;
undo writes separate reversal markers while preserving the original evidence.
Every step receives an event ID and the evidence hash is carried into the
approval record and packet. The isolated build has four real, least-privilege
reversible connectors for the free `KAN` / `Driftline` Jira project, `DRIFT`
Confluence space, one Slack channel, and the isolated GitHub repository. Only
the separately authenticated signed-operator lane can execute these
marker-idempotent handoffs; undo keeps customer work intact where applicable,
changes only Driftline-owned markers, and appends reversal evidence. The public
judge console is packet-only even when credentials are present; its named demo
actor is not production identity. A signed live context probe on the deployed
runtime returned aggregate-only reads for Jira (`KAN`, 18 sampled issues),
Confluence (`DRIFT`, 5 pages), Slack (`C0BRGFUSADA`, 27 recent messages), and
GitHub (0 open issues, 0 open pull requests); no source text or message bodies
were returned or persisted. The Salesforce contract is read-only and remains
pending final tenant consent.

## Other data sources used

The public judge flow uses only five bounded source definitions: two Driftline
own-product fixtures (pricing and terms) and three explicitly labelled
synthetic competitor fixtures (pricing, offering, and product narrative). The
live public pricing fixture is a pinned raw GitHub text file. No private company
data, customer records, CRM objects, credentials, or arbitrary web crawl are
used by the anonymous demo. Authenticated connector lanes are present only for
separately provisioned tenant identities and are not part of the public demo.

The agent entry point has the same explicit two-lane boundary: the public judge
request is tenantless and packet-safe, while a signed operator request carries
the verified tenant through the ADK turn, quota reservation, and Firestore
workflow. Durable tenant memberships, connector profiles, Secret Manager
bindings, revocation metadata, and transactional rate limits are isolated in
the Driftline project; no deployment-wide connector target fallback is enabled.

The judge-ready workflow uses synthetic data: a public/pricing fixture changes
Enterprise audit-log retention from unlimited to 365 days. The UI labels this
fixture and is not connected to a real company, CRM, customer, or billing
system.

## Google technology

- Gemini 3.5 Flash through Vertex AI for evidence-grounded interpretation and
  bounded drafting. A second task-mode ADK analyst returns a strict JSON impact
  contract; Driftline validates every artifact owner, risk, and evidence hash.
- Google Agent Development Kit for the coordinator, structured analyst, session
  runner, and allowlisted tools.
- Cloud Tasks for durable asynchronous job dispatch.
- Cloud Scheduler for the six-hour historical monitor and signed monitor calls.
- Cloud Run for the public API and operational console with scale-to-zero.
- Firestore for workflow documents, the source snapshot ledger, and
  audit_events subcollections.
- Cloud Storage for private, versioned action packets and rollback markers.
- Artifact Registry and Cloud Build for the isolated deployment.

The model can inspect an allowlisted source and read workflow state. It cannot
approve, resume, widen its own permissions, or publish a high-risk action. The
separate API policy gate requires an exact allowlisted decision. Public demo
approvals are packet-only; configured connector writes require a signed
operator token. The public demonstration does not include production identity
authentication, so its named actor is not an enterprise IAM claim.

## Architecture and state

The React console calls FastAPI on the same Cloud Run service. A scan creates a
Firestore job, Cloud Tasks dispatches an OIDC-authenticated worker request, and
the ADK run records its model/tool trace against the resulting workflow. The
deterministic workflow engine creates evidence, impact records, approval
interrupts, public-demo packets, and audit events. Firestore persists the job,
whole workflow, source history, and each audit event. A workflow loaded after a
process restart is restored into the policy engine before approval or reopening
is accepted. Cloud Scheduler's monitor path records a baseline or no-change
result without inventing a workflow.

## Disclosure of prior work

The contest rules require new projects to be created during the submission
period and require disclosure of pre-existing work. Driftline continues an
earlier concept conversation and incorporates the supplied source package. The
implementation, cloud configuration, verification, documentation, and
submission materials in this entry were completed or materially changed during
the submission period. This entry does not claim that the earlier ideation was
created during the contest.

## Accomplishments

- Full asynchronous change-to-action workflow with resumable human approval.
- SHA-256 evidence attached to the approval decision.
- Four independently owned downstream artifacts mapped from one source change.
- Offering impact graph that routes own and competitor changes into Product
  Marketing, enablement, support, customer lifecycle, and planning surfaces.
- Approval-gated handoff manifests plus four signed-operator-only, reversible
  Jira, Confluence, Slack, and GitHub connectors with explicit target and token
  scope boundaries.
- A synthetic, reproducible demonstration that requires no private company data.
- A live isolated Cloud Run, Cloud Tasks, and Firestore deployment with a
  dedicated runtime identity, scale-to-zero configuration, and a
  project-scoped budget guardrail.
- The current active release is source commit `2b35881`, Cloud Build
  `09f36c8f-43e4-469f-a170-01a317090b6c`, and Cloud Run revision
  `driftline-00084-7bh` at 100% traffic. It passed 239 backend tests, Ruff,
  the frontend production build, and isolated deployment probes. The console
  and signed direct-agent API route authenticate operator-registered URLs
  through the real monitor lane, support bounded HTML/text/RSS onboarding, and
  expose a signed aggregate pilot-measurement flow without claiming customer
  ROI. Signed tenant operators can also retry terminally failed jobs from Run
  history; retries preserve the original tenant/source/query boundary and use
  a durable idempotency link, while public jobs remain packet-only.
  The scheduled monitor also deduplicates queued/running source jobs across
  duplicate deliveries and reports explicit in-flight no-ops instead of
  creating duplicate model work.
  The current release also includes the CSP fix for the Google Identity
  Services stylesheet; replacing the legacy OAuth client with a new client
  owned by this isolated project remains the final operator-auth gate.
  It also includes a recoverable frontend error boundary so a render failure
  cannot present a blank console or imply that persisted workflow state was
  lost.
  Multimodal evidence is pinned to an immutable asset commit and served as
  smaller JPEG bytes; fingerprinted frontend bundles are immutable-cacheable.
- An earlier live rollout (`driftline-00037-6t9`, source `bb8a437`, Cloud Build
  `db3305b1-7770-4cec-a7f3-e468eb4210f5`) presents the console as a production
  control plane while keeping the anonymous judging lane explicitly packet-only
  and isolated from customer writes.
- A historical live revision was `driftline-00061-46f` from source commit
  `a4f675a`, deployed by Cloud Build
  `dd23aeae-fec2-45e9-b383-9e956367e7d7`; it serves 100% of traffic with the
  same scale-to-zero and one-instance guardrails. Its image digest is
  `sha256:8cdd40105bd51c275e42f2af3cc1d99a9be92e22181c44b56c8f68351d4a2a14`.
- The deployed public path has returned `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and allowlisted tool calls in direct live probes.
  The deployed runtime source is commit `a4f675a`, deployed through Cloud Build
  `dd23aeae-fec2-45e9-b383-9e956367e7d7` as Cloud Run revision
  `driftline-00061-46f` at 100% traffic after local and CI gates passed. The
  latest repository verification run `32449633360` passed; the
  local release gate also passed all 225 backend tests, Ruff, and the frontend
  production build. A live direct-agent canary
  returned the two allowlisted tool calls without echoing anonymous query or
  user fields; a fresh browser run had no console errors and Lighthouse scored
  100 across accessibility, best practices, SEO, and agentic browsing on both
  desktop and mobile. The signed
  tenant-filtered pilot report is deployed; the signed report currently
  returns `not_measured` with zero records, and an unsigned public request
  returned HTTP 401. The agent trace now updates its public status after
  approval, reopen, and dismissal. Fresh browser QA passed the live scan,
  evidence, approval, completion, activity log, timeline, and 390px mobile path
  without console errors.
- The final smoke workflow `de3f6c7f-4a59-4005-ad24-4968bf3a50c4` reached
  `needs_approval` on this revision; signed public-demo approval persisted four
  packets with `external_write=false`, and immediate undo persisted the
  reversal marker. Current-revision logs contained no `ERROR` entries.
- A signed `tenant_demo` fixture pilot on the current revision carried tenant
  `driftline-demo` through real ADK/Gemini into Firestore as
  `synthetic_tenant_demo`. After named human approval, the isolated Jira
  connector reactivated the prior marker-scoped `KAN-18` task and a direct Jira
  API read confirmed Driftline's active labels. Signed undo then changed only
  the Driftline-owned labels to `driftline-reversed`; the issue was retained.
  This proves an operational connector path, not customer ROI or a live
  competitor-monitoring result.
- The GitHub adapter fails closed when a matching issue is human-closed:
  `blocked_closed` performs no automatic reopen or relabel. This preserves
  operator control over external task lifecycle while keeping the connector
  auditable and reversible.
- A current-revision signed approval/undo canary also exercised all four
  configured external adapters. Approval returned `reactivated` for Jira,
  Confluence, Slack, and GitHub; direct provider reads confirmed active versus
  reversed state transitions, with GitHub unrelated labels preserved. Undo
  returned all four to reversed state. This is operational connector evidence,
  not customer ROI or a claim of live competitor data.
- On 2026-08-21, the preceding `driftline-00038-2gq` revision was rechecked end to
  end: `/health` returned Firestore persistence and async jobs; a direct ADK
  run returned HTTP 200 with `persisted=true`, `model=gemini-3.5-flash`, and
  exactly `inspect_source_change` plus `get_workflow_state`; a public demo
  approval completed to a persisted packet and a named demo undo returned it
  to `needs_approval` with a reversal marker. Fresh desktop and 390px mobile
  Lighthouse navigation audits passed all 57 checks with no console warnings
  or errors. The signed connector binding-health probe returned four healthy,
  namespace-verified connectors (Jira, Confluence, Slack, GitHub), while the
  signed aggregate context probe returned Jira `KAN` (18 issues), Confluence
  `DRIFT` (5 pages), Slack `C0BRGFUSADA` (27 recent messages), and GitHub (0
  open issues and 0 open pull requests) with aggregate-only redaction.
- The hosted operator lane now requires Google OIDC (`DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY=true`); a direct HMAC probe returned HTTP 401, while the public lane remained packet-only. This keeps the deployed break-glass signer out of normal production authorization.
- The newest revision repaired an incomplete tenant bootstrap safely: an
  existing tenant with no memberships can receive exactly one owner membership
  through the platform bootstrap route, while an already-membered tenant still
  returns a conflict. The live OIDC directory then returned the isolated
  `driftline-demo` owner membership, aggregate connector context, and binding
  health without exposing credential values.
- A current authenticated `tenant_demo` run (`b6332414-3bc3-4eb4-b5fc-43041abe35d3`)
  carried `driftline-demo` through Gemini/ADK into Firestore and stopped at
  `needs_approval`. OIDC approval reactivated the existing marker-scoped Jira
  task `KAN-18` (idempotent, no duplicate issue); the same approval also
  reactivated the tenant's Confluence, Slack, and GitHub markers. OIDC undo
  changed the Driftline-owned Jira label to `driftline-reversed`, appended the
  reversal comment, and returned the workflow to `needs_approval` while
  retaining the issue and append-only audit record. This is direct production
  connector evidence for reversible operations, not a customer-ROI claim.
- The current public console also exposes this OIDC boundary as a real operator
  experience: Google sign-in stays in memory, tenant memberships are discovered
  from the signed identity, and the selected tenant is carried through scan,
  approval, action-item, and undo calls. Logged-out judges still receive the
  packet-safe demo with no credential prompt.
- The current responsive release was rechecked at a 390px emulated viewport:
  the document reports `bodyScrollWidth=500`, `documentElement.scrollWidth=500`,
  and `scrollX=0`, while the activity, run-history, and worklist panels retain
  their intentional inner horizontal scroll. Desktop and mobile Lighthouse each
  passed all 57 checks with 100 scores and the browser console had no messages.
- The anonymous public-source Change Card on the current `driftline-00061-46f`
  deployment was
  rechecked after a truthfulness fix: it displays `CRM context unavailable`
  and `No CRM context was read in this run`, never `Permissioned business
  context` without a connected Salesforce tenant.
- A fresh public-demo run selected the reviewed Gemini copilot option,
  persisted its private packet, and kept every connector `prepared_only` with
  `external_write=false`. A named Product Marketing demo actor then claimed
  and completed one owner action; the live value endpoint reports this as
  public-demo telemetry only (1 of 24 action items, 4.2%), not customer ROI.
- The latest public packet proof on `driftline-00061-46f` contains
  `isolated public-demo output` rather than the old sandbox wording; approval
  persisted the packet and undo returned `needs_approval` with both
  `external_write=false` and `external_systems_changed=false`.
- The signed source registry read returned the five pinned fixtures plus the
  verified operator-registered own-product source
  `custom/driftline-readme`. The research references in the README are not
  registered live competitor sources; no competitor target was invented.
- The tenant credential data plane is now canonical and fail-closed: durable
  tenant memberships, per-tenant Secret Manager namespaces, impersonated
  service identities, pinned versions, rotation/revocation, operation scopes,
  and metadata-only access auditing. Tenant owners can also set bounded quota
  and retention policy without a redeploy; the public lane never receives
  those credentials.

## Findings and learnings

- The highest-value unit is not an alert; it is a source-hash-bound Change Card
  that names the affected offering, owners, risk, proposed update, and rollback
  path before anything is published.
- Deterministic policy is more trustworthy than a model-generated approval:
  Gemini interprets and drafts, while the policy engine owns the approval gate,
  idempotency, and reversal state.
- A reliable agent must make its limitations visible. Driftline labels
  synthetic data, reports unavailable connectors, preserves raw evidence, and
  separates observed workflow telemetry from unmeasured customer ROI.
- The current evidence proves operational execution, live aggregate connector
  reads, and safety boundaries, not customer revenue lift, hours saved,
  willingness-to-pay, or a multi-customer pilot. Those remain validation work
  rather than claims in this entry.

## Limitations and next steps

The current public build intentionally stops at approved public or synthetic
sources and does not perform live writes from the public console. The
integration layer produces bounded, target-specific handoff manifests and
tracks their prepared state. The signed operator connector lane is deliberately
limited to the free Driftline Jira project, uses a Jira-scoped token held only
in Secret Manager, and never deletes Jira work. GitHub is authenticated and
reversible; Confluence and Slack live aggregate reads are verified for the
isolated tenant, while public writes remain prepared-only. Salesforce is
read-only context preparation pending tenant consent. Customer ROI, hours
saved, and willingness-to-pay remain unmeasured; see `docs/PILOT_PLAN.md` and
the deployed signed `/api/ops/pilot-report`. This is a verified multi-tenant
control-plane foundation, not a claim of self-serve enterprise SSO, commercial
billing, or a multi-customer pilot.

## Official links

See [docs/hackathon-rules.md](https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md)
for the rules, dates, required technology, video limit, category definitions,
and eligibility disclosures verified from the official Devpost rules page.

Official live references:

- [Hackathon overview](https://allthingsagentichackathon.devpost.com/)
- [Official rules](https://allthingsagentichackathon.devpost.com/rules)
- [Official judging criteria](https://allthingsagentichackathon.devpost.com/details/judging-criteria)
- [Official submission requirements](https://allthingsagentichackathon.devpost.com/details#what-to-submit)
- Submission deadline: **2026-09-01 00:00 UTC** (2026-08-31 7:00 PM Central / 5:00 PM Pacific)
- Required video: approximately four minutes maximum, public on YouTube or Vimeo, English or subtitled, showing the working agent and Google Cloud proof.
