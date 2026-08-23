# Driftline Taskmaster PRD

## Product promise

Driftline turns a monitored promise change into evidence-bound, reversible owner
action. It is not a chatbot, an alert feed, or an unbounded crawler.

## Epic 1: Verify a bounded change

**Story:** As an operator, I want Driftline to monitor an approved source and
prove exactly what changed so downstream work begins from defensible evidence.

Acceptance criteria:

- The selected source is allowlisted and visibly labeled as public, synthetic,
  or tenant-registered.
- A scan creates a durable asynchronous job instead of holding a chat request.
- The UI displays before/after evidence, retrieval metadata, confidence, and a
  full SHA-256 evidence hash.
- Duplicate delivery reuses the same stable Change Card identity.
- Failed or unavailable evidence fails closed or uses only the explicitly
  labeled anonymous replay path.

## Epic 2: Convert evidence into owner-ready work

**Story:** As a PMM or RevOps operator, I want one change mapped to named owners,
artifacts, risks, and actions so the signal becomes coordinated work.

Acceptance criteria:

- Gemini 3.5 Flash through Google ADK produces structured impact analysis.
- The UI connects source, offering, business consequence, work surface, and
  target handoff.
- Every proposed artifact includes an owner, action, risk, evidence citation,
  and rollback path.
- The public trace shows only redacted runtime provenance, never raw prompts,
  credentials, or private source bodies.

## Epic 3: Keep authorization outside the model

**Story:** As an accountable human, I want consequential work paused until I
approve a bounded plan so the model cannot authorize its own action.

Acceptance criteria:

- High-risk workflows stop at `needs_approval`.
- The ADK agent has no approval tool.
- Approval requires a current evidence-hash match and deterministic policy pass.
- Anonymous approval creates only packet-safe Driftline artifacts.
- External connector writes require a signed operator, tenant membership, and
  least-privilege credential binding.

## Epic 4: Take and reverse real action

**Story:** As an operator, I want an approved owner action created idempotently
and reversibly so automation completes work without leaving unsafe residue.

Acceptance criteria:

- Signed Jira approval creates or reactivates one Driftline-owned marker.
- Repeating the same request reuses the marker rather than creating duplicates.
- Reopen/undo removes only Driftline-owned active state and appends a reversal
  record; it never deletes unrelated Jira work.
- The activity ledger and returned packet retain the evidence and action IDs.

## Epic 5: Let a judge verify everything quickly

**Story:** As a judge, I want a credential-free product path, a focused video,
and exact reproduction commands so I can score the project without trusting
marketing claims.

Acceptance criteria:

- The public URL loads without credentials and labels its data boundary.
- The first viewport exposes the model, ADK runtime, health, trace gate, and
  serving release.
- The repository passes automated tests, lint, dependency audit, frontend build,
  image build, trace evaluation, and production checks.
- The video shows the problem, live action, Google Cloud proof, and rollback in
  no more than four minutes.
- The Devpost copy names Taskmaster, the exact release, and the limits of the
  evidence without stale or duplicate claims.

## Non-goals

- Customer-facing publication without human review.
- Anonymous third-party writes.
- Fleet-scale registry/identity claims.
- Customer ROI claims without an independent pilot.
- Salesforce metrics before fresh consent and a verified aggregate read.
