# Driftline — change should trigger action, not another meeting

## Submission links

- Hosted application: added after the Cloud Run smoke test
- Source repository: https://github.com/mikeyerke/driftline
- Demonstration video: added after the public YouTube upload
- Architecture diagram: docs/architecture.md in the repository

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

Driftline monitors an approved source and runs a resumable change-to-action
workflow. It verifies evidence, maps operational impact, drafts updates for
each downstream artifact, and executes only bounded actions. When a change
touches a contractual expectation, deterministic policy pauses the workflow and
requests a named human decision. After approval, Driftline resumes exactly
where it stopped, publishes two bounded updates, queues one owner review, and
schedules one low-risk update. Every step receives an event ID and the
evidence hash is carried into the approval record.

The judge-ready workflow uses synthetic data: a public/pricing fixture changes
Enterprise audit-log retention from unlimited to 365 days. The UI labels this
fixture and is not connected to a real company, CRM, customer, or billing
system.

## Google technology

- Gemini 3.5 Flash through Vertex AI for evidence-grounded interpretation and
  bounded drafting.
- Google Agent Development Kit for the coordinator, session runner, and
  allowlisted tools.
- Cloud Run for the public API and operational console with scale-to-zero.
- Firestore for workflow documents plus audit_events subcollections.
- Artifact Registry and Cloud Build for the isolated deployment.

The model can inspect an allowlisted source and read workflow state. It cannot
approve, resume, widen its own permissions, or publish a high-risk action. The
separate API policy gate requires an explicit named human and an exact
allowlisted decision.

## Architecture and state

The React console calls FastAPI on the same Cloud Run service. The deterministic
workflow engine creates evidence, impact records, approval interrupts, and
audit events. Firestore persists the whole workflow and each audit event. A
workflow loaded after a process restart is restored into the policy engine
before approval or undo is accepted.

## Disclosure of prior work

The contest rules require new projects to be created during the submission
period and require disclosure of pre-existing work. Driftline continues an
earlier concept conversation and incorporates the supplied source package. The
implementation, cloud configuration, verification, documentation, and
submission materials in this entry were completed or materially changed during
the submission period. This entry does not claim that the earlier ideation was
created during the contest.

## Accomplishments

- Full change-to-action workflow with resumable human approval.
- Immutable SHA-256 evidence attached to the approval decision.
- Four independently owned downstream artifacts mapped from one source change.
- A synthetic, reproducible demonstration that requires no private company data.
- An isolated Cloud Run and Firestore deployment configuration with a
  dedicated runtime identity (live deployment evidence will be added before
  submission).
- Deterministic safety controls around an actual Google ADK/Gemini path.

## Limitations and next steps

The current build intentionally stops at approved public or synthetic sources.
It does not connect to Salesforce, Slack, CPQ, customer records, or private
knowledge bases; the four artifact updates are bounded demonstration actions.
Future connectors would need source-level permissions, rate limits, retries,
idempotency keys, and organization-specific approval policies before production
use.

## Official links

See docs/hackathon-rules.md for the rules, dates, required technology, video
limit, category definitions, and eligibility disclosures verified from the
official Devpost rules page.
