# Driftline — change should trigger action, not another meeting

## Submission links

- Hosted application: https://driftline-xvxczqg62a-uc.a.run.app/
- Source repository: https://github.com/mikeyerke/driftline
- Demonstration video: held while the product is being pressure-tested; replace with a public upload only after final QA
- Architecture diagram: https://github.com/mikeyerke/driftline/blob/main/docs/architecture.md

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
After approval, Driftline creates an evidence-linked sandbox packet, an owner
review item, or a queued item per artifact. Each artifact also receives a
durable human-owned action item with an idempotency key and evidence hash; a
named reviewer can claim and complete it without giving the model write access.
The packet and one approved low-risk operational output are persisted as
private, versioned Cloud Storage objects inside the isolated Driftline project;
undo writes separate reversal markers while preserving the original evidence.
Every step receives an event ID and the evidence hash is carried into the
approval record and packet. The isolated build has one real, least-privilege
Jira connector for the free `KAN` / `Driftline` project: only the separately
authenticated signed-operator lane can create at most one marker-idempotent
Jira Task, and undo keeps that issue, changes only Driftline-owned labels, and
appends a reversal comment. The public judge console is packet-only even when
credentials are present; its named demo actor is not production identity.
Approval also prepares target-specific Confluence, Slack, GitHub, and
Salesforce-context manifests. The Salesforce contract is read-only and
prepared-only; it is not authenticated in this deployment.

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
interrupts, sandbox packets, and audit events. Firestore persists the job,
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
- Approval-gated handoff manifests plus one signed-operator-only, reversible
  Jira Task connector with explicit project and token scope boundaries.
- A synthetic, reproducible demonstration that requires no private company data.
- A live isolated Cloud Run, Cloud Tasks, and Firestore deployment with a
  dedicated runtime identity, scale-to-zero configuration, and a
  project-scoped budget guardrail.
- The current public verification job is `job-b5650db09934`, with workflow
  `907c39d8-e869-4332-87b8-e86823fca116`. Its persisted audit trail contains
  verified evidence, four mapped artifacts, four drafted updates, a human
  approval, packet creation, and `decision_reopened`; the final state is back
  at the deterministic approval gate.
- The deployed public path returned `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and both allowlisted tool calls. Cloud Run revision
  `driftline-00169-8cw` serves 100% of traffic in the isolated project. The
  latest browser proof passed desktop and 390px mobile scan, evidence, artifact
  selection, approval, completion, and reopen/undo with no console errors or
  failed requests.
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
- The current evidence proves operational execution and safety boundaries, not
  customer revenue lift, hours saved, willingness-to-pay, or a multi-customer
  pilot. Those remain validation work rather than claims in this entry.

## Limitations and next steps

The current public build intentionally stops at approved public or synthetic
sources and does not perform live writes from the public console. The
integration layer produces bounded, target-specific handoff manifests and
tracks their prepared state. The signed operator connector lane is deliberately
limited to the free Driftline Jira project, uses a Jira-scoped token held only
in Secret Manager, and never deletes Jira work. Confluence, Slack, and GitHub
are similarly bounded but require their own isolated configuration. Salesforce
is read-only context preparation only. Customer ROI, hours saved, and
willingness-to-pay remain unmeasured; see `docs/VALIDATION_PLAN.md`. This is a
verified multi-tenant control-plane foundation, not a claim of self-serve
enterprise SSO, commercial billing, or a multi-customer pilot.

## Official links

See [docs/hackathon-rules.md](https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md)
for the rules, dates, required technology, video limit, category definitions,
and eligibility disclosures verified from the official Devpost rules page.
