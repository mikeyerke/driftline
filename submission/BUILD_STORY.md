# Building Driftline: giving an agent less authority than intelligence

*I created this build story for the purpose of entering the Google All Things
Agentic Hackathon.*

Most agent demos focus on what the model can do. Driftline started with the
opposite question: what must the model never be allowed to authorize?

The problem is promise drift. A public pricing, product, or policy sentence
changes and the signal appears immediately, but comparison pages, battlecards,
deal guidance, FAQs, and internal work stay stale. A summary does not fix that.
Someone still has to prove the change, determine what it affects, route the
work, make a consequential decision, and preserve who approved it.

Driftline handles that path as an asynchronous Taskmaster workflow:

`observe -> hash -> interpret -> map -> gate -> claim -> act -> reconcile -> reverse -> audit`

## Gemini interprets; deterministic code authorizes

Gemini 3.5 Flash runs through Vertex AI and Google ADK. It receives a bounded,
sanitized evidence projection and returns structured impact analysis and
decision options. The agent has only two read/inspect tools. It does not receive
an approval tool.

Before model output can become work, Pydantic schemas and deterministic policy
verify the source, evidence hash, artifact allowlist, action, owner, risk,
citations, and rollback. High-risk state persists at `needs_approval` until a
named human acts.

This is more than a safety wrapper. It makes the product explainable: every
screen can show which evidence produced which recommendation and where human
authority begins.

## Durable action, not a chat response

Cloud Tasks invokes the worker asynchronously. Firestore stores the observation,
job, workflow, trace metadata, action state, and append-only audit trail. A
stable Change Card identity derives from source and evidence hash, so retries
cannot manufacture duplicate work.

The hardest failure is not a clean connector rejection. It is a process ending
after a provider may have accepted a write but before the application records
the final result. Driftline claims a credential-free operation record before
side effects begin. Approval and reversal enter distinct executing states,
conflicting decisions fail closed, and an interrupted attempt moves to
`reconciliation_required`. A named human retries the same operation ID and
generation; idempotent adapters and artifact keys converge on one durable
outcome instead of manufacturing a second action. Configured-write recovery
still requires signed tenant authority. A bounded lease also covers hard
process termination: an unexpired claim cannot be stolen, and an expired claim
must first win a separate Firestore CAS into the recovery lane.

The public judge lane creates only Driftline-owned packets. External writes are
reserved for a signed tenant lane. In the isolated Jira proof, an approved
action created or reactivated one scoped marker. Repeating it reused the same
marker. Reopening the decision reversed only Driftline-owned state and preserved
the issue and reversal history.

## The architecture lesson

An agent can reason broadly while acting narrowly. Trust comes from making the
authority boundary explicit:

- evidence bytes stay immutable;
- source text is treated as untrusted data;
- traces exclude prompts, source bodies, and credentials;
- approval is deterministic and evidence-bound;
- credentials are tenant-scoped and never sent to the browser;
- retries reuse one durable operation ID and are idempotent;
- every action has a reversal contract.

## What we refused to claim

The deployment proves agent execution, durability, source observations,
approval, action, and reversal. It does not prove customer ROI. Time saved,
revenue, retention, and willingness to pay remain `not_measured` until an
independent pilot produces paired evidence.

The most important build decision was not adding another connector. It was
keeping the story focused: one change, four affected work surfaces, one human
gate, one real least-privilege action, and one clean reversal.

Live application: https://driftline-ops.web.app/

Source: https://github.com/mikeyerke/driftline
