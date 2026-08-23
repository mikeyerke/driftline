# Driftline proof-of-action demo — 3:45 target

The official limit is four minutes. Record at 1080p, narrate briskly, and upload
the final cut publicly to YouTube or Vimeo. Show real application behavior and
visible Google Cloud proof; no slide-only substitute.

## 0:00–0:18 — Hook

**Screen:** Deployed Driftline URL with the competitor pricing diff in view.

**Narration:** “A competitor changes one pricing sentence. The alert is easy.
Finding every stale promise, assigning the right owner, and proving what a human
approved is the real work. Driftline turns that change into reversible action.”

## 0:18–0:48 — Trigger the Taskmaster workflow

**Screen:** Show the public URL and packet-safe label. Select **Competitor
pricing snapshot** and click **Run live agent**. Keep production proof and job progress
visible.

**Narration:** “This is the live Cloud Run application. Run live agent creates a
durable Cloud Tasks job. Google ADK and Gemini 3.5 Flash inspect an allowlisted
source while Firestore stores the job, workflow, and audit state. The browser
does not hold the model request open.”

## 0:48–1:25 — Prove evidence became work

**Screen:** Open evidence, show the full SHA-256 hash, then trace the impact map
from source to offering to four work surfaces. Open one artifact detail.

**Narration:** “Driftline binds the exact before and after bytes to an evidence
hash. Gemini maps the change into a comparison map, battlecard, deal-desk rule,
and executive brief. Every action has an owner, risk, citation, and rollback.
The persisted trace shows the model and only the two allowlisted tools.”

## 1:25–1:55 — Show the autonomy boundary

**Screen:** Decision Copilot options and **Human approval required**.

**Narration:** “The model can interpret and recommend, but it cannot authorize.
High-risk work stops in deterministic policy. The ADK agent has no approval
tool, and approval fails if the evidence hash or allowlisted action changes.”

## 1:55–2:38 — Wow moment: real signed action and reversal

**Screen:** Cut to the already authenticated operator lane without showing the
login flow. Approve the Jira handoff. Show the returned Jira marker and activity
event, then click **Reopen decision** and show the reversed action status.

**Narration:** “In the signed tenant lane, approval uses a tenant-scoped Secret
Manager credential to create or reactivate one Jira marker. The same evidence
and idempotency key prevent duplicates. Reopen decision reverses only
Driftline-owned labels and comments. It never deletes unrelated Jira work, and
the reversal remains in the append-only audit ledger.”

## 2:38–3:16 — Visible Google Cloud proof

**Screen:** Show `/health`, `/api/ops/summary`, one Firestore workflow/audit
record, and Cloud Run revision/log view. Never show tokens or secret values.

**Narration:** “This is the serving Git SHA and Cloud Build ID. Cloud Run hosts
the API and console, Cloud Tasks dispatches work, Firestore restores state,
Scheduler drives monitoring, and the latest trace gate passes fourteen of
fourteen safety and usefulness checks.”

## 3:16–3:45 — Close

**Screen:** Architecture image followed by project name, live URL, repository,
and Taskmaster.

**Narration:** “Driftline is not another alert and not another chat window. It
is an evidence-bound Taskmaster agent: autonomous where policy allows, human
where judgment matters, and reversible when the decision changes.”

## Recording gate

- [ ] Total duration is 3:45 or shorter.
- [ ] Live URL appears in the first 30 seconds.
- [ ] Gemini 3.5 Flash, Google ADK, and actual action appear on screen or aloud.
- [ ] Signed Jira action and reversal form one truthful sequence.
- [ ] Google Cloud proof appears before 3:16.
- [ ] No credentials, tokens, private records, or raw prompts appear.
- [ ] Captions are accurate and English.
- [ ] Final upload is public, not private or unlisted.
