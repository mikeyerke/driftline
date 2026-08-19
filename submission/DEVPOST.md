# Driftline — change should trigger action, not another meeting

## Submission links

- Hosted application: https://driftline-xvxczqg62a-uc.a.run.app/
- Source repository: https://github.com/mikeyerke/driftline
- Demonstration video: https://youtu.be/r9z-GNQasBc (public, caption-led, 44 seconds)
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

Driftline runs a resumable change-to-action workflow from two allowlisted public
source types (`public/pricing` and `public/terms`). Cloud Tasks starts the scan asynchronously; the ADK coordinator
verifies evidence, maps operational impact, and drafts updates for each
downstream artifact. When a change touches a contractual expectation,
deterministic policy pauses the workflow and requests a named human decision.
After approval, Driftline creates an evidence-linked sandbox packet, an owner
review item, or a queued item per artifact. The packet is persisted as a private,
versioned Cloud Storage object; undo writes a separate rollback marker while
preserving the original evidence. Every step receives an event ID and the
evidence hash is carried into the approval record and packet. No external system
is changed by the public demo.

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
separate API policy gate requires an explicit named demo actor and an exact
allowlisted decision. The public demonstration does not include production
identity authentication, so this named actor is not an enterprise IAM claim.

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
- A synthetic, reproducible demonstration that requires no private company data.
- A live isolated Cloud Run, Cloud Tasks, and Firestore deployment with a
  dedicated runtime identity, scale-to-zero configuration, and a
  project-scoped budget guardrail.
- Direct Vertex AI execution evidence is claimed only in the release inventory
  after the deployed endpoint returned `gemini-3.5-flash`, `google_adk`, and both
  allowlisted tool calls. The final verified demo job was
  `job-b18a4ec4ebfe` / workflow `96b39124-656b-4de1-84d7-c2b79e40a51a`;
  approval created `action-c20fd36afe28`, a private packet object, and undo
  created its rollback marker. A signed monitor run
  (`job-59ef418b4531`) completed unchanged without inventing a workflow.

## Limitations and next steps

The current build intentionally stops at approved public or synthetic sources.
It does not connect to Salesforce, Slack, CPQ, customer records, or private
knowledge bases; the four artifact updates are bounded demonstration actions.
Future connectors would need source-level permissions, rate limits, retries,
idempotency keys, and organization-specific approval policies before production
use.

## Official links

See [docs/hackathon-rules.md](https://github.com/mikeyerke/driftline/blob/main/docs/hackathon-rules.md)
for the rules, dates, required technology, video limit, category definitions,
and eligibility disclosures verified from the official Devpost rules page.
