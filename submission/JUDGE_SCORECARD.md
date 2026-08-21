# Driftline judge scorecard

This is the shortest path from the official judging rubric to reproducible
proof in the deployed product. It is intentionally evidence-led: public demo
activity is labeled as evaluation telemetry, and no customer ROI is claimed.

Official brief: [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/)

## 40% — Innovation & operational utility

**Problem:** Product Marketing and RevOps receive market and promise changes,
but the expensive work is deciding whether a change matters, finding every
affected promise, assigning owners, and proving the work closed.

**What is different:** Driftline turns one verified source transition into a
Change Card: materiality and decision window, affected offering, role-specific
work packets, evidence citations, owner deadlines, reversible action identity,
and an append-only closure trail. It is a change-to-action operator, not an
alert feed or chat summary.

**Live proof:**

1. Open the [deployed console](https://driftline-xvxczqg62a-uc.a.run.app/).
2. Select `Competitor pricing snapshot` and click **Run scan**.
3. Watch the agent trace move from durable queue to Google ADK tools and the
   structured Gemini impact pass.
4. Open the source evidence and follow the graph to the comparison map,
   pricing battlecard, deal-desk guidance, and executive brief.
5. Approve the recommended or narrower plan, claim/complete an owner action,
   then **Reopen decision**. The output and reversal remain in the audit trail.

The public lane creates a real private Cloud Storage change packet and
Firestore workflow, but never writes a customer's systems. The signed tenant
lane is the only lane allowed to call configured connectors.

## 30% — Architectural discipline & Google stack

The deployed path is:

```text
allowlisted snapshot → Cloud Tasks → Cloud Run worker
  → Google ADK + Gemini 3.5 Flash
  → deterministic materiality/policy gate
  → Firestore workflow + audit + source ledger
  → versioned Cloud Storage output / scoped connector handoff
```

The model receives only bounded, quoted source evidence and two allowlisted
read/state tools. It cannot approve itself, widen permissions, or call undo.
Cloud Tasks is at-least-once with durable deduplication; connector actions use
tenant-bound Secret Manager bindings, operation scopes, marker idempotency, and
reversal markers. Firestore and Cloud Storage are in the isolated
`driftline-hackathon-2026` project.

## 30% — Demo & production readiness

Run the exact release checks from the repository root:

```bash
BASE=https://driftline-xvxczqg62a-uc.a.run.app
curl -fsS "$BASE/health"
./scripts/verify_production.sh
./scripts/verify_live_agent.sh
./scripts/verify_public_approval_undo.sh
```

The scripts fail closed unless the public service is healthy, the active Cloud
Run deployment is in the isolated project, the live job reaches
`needs_approval`, the response proves `gemini-3.5-flash` and `google_adk`, the
two allowlisted tools are present, and the evidence-bound artifacts and audit
events are persisted. The live verifier retries the explicitly permitted
anonymous deterministic fallback for up to three bounded runs, but still
fails unless a genuine Gemini structured turn is proven. The full local gate
is:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check backend
npm run build --prefix frontend
git diff --check
```

The packet-safety verifier is separate from the Gemini proof so the two claims
remain auditable: it creates a fresh public workflow, approves a bounded
evidence packet, asserts `storage_status=persisted` with both external-write
flags false, then reopens the decision and asserts a persisted reversal marker.
It never needs a connector credential or performs a third-party write.

The current release evidence is recorded in
[`docs/RESOURCE_INVENTORY.md`](../docs/RESOURCE_INVENTORY.md), including the
source commit, Cloud Build ID, Cloud Run revision, public job ID, and exact
fixture URLs. The architecture diagram is in
[`docs/architecture.md`](../docs/architecture.md).

## Honest limits

- The anonymous demo monitors five pinned fixtures; it is not arbitrary web
  crawling.
- Salesforce is a read-only OAuth lane awaiting a real tenant's consent.
- Public connector cards are packet-safe; configured external writes require
  signed tenant approval.
- Hours saved, revenue lift, retention impact, willingness-to-pay, and a
  customer pilot are not measured. The Value proof panel reports deployment
  observations separately from those outcomes.
