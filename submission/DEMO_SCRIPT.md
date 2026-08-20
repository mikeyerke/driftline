# Four-minute demo

The official rules cap the evaluated video at four minutes. Use captions or
the entrant's own narration; do not synthesize the entrant's voice or likeness.
Show the public Cloud Run URL and a Cloud Run or log view in the same recording.

## 0:00–0:25 — The problem

Caption: “One sentence changes on a public pricing page. The alert is easy.
Finding every downstream promise, deciding what can update safely, and proving
who approved the risky part is the actual work.”

Show the deployed Driftline console at
https://driftline-xvxczqg62a-uc.a.run.app/ and the “Synthetic demo data” label.

## 0:25–0:55 — Choose the change surface and start the workflow

Choose **Public pricing snapshot** in the scenario selector, then click
**Run scan**. Explain that Driftline is bounded to allowlisted source types,
not arbitrary URLs, and that this creates a durable asynchronous job: the
browser queues work, Cloud Tasks invokes the worker, and Firestore stores the
job and workflow. The public snapshot badge shows whether the allowlisted
GitHub fixture was fetched; synthetic replay is explicitly labelled if the
fetch is unavailable. Keep the agent trace panel visible.

## 0:55–1:35 — Evidence and impact

Open **Evidence diff** and then **Open evidence**. Show the exact removed and
added language, the synthetic source ID, the full SHA-256 hash, and the
confidence value. Trace the impact map from the observed own-product move into
the affected offering and four downstream artifacts. Show each artifact's
owner, bounded action, risk, and target-specific handoff status. Select an
artifact row to show its detail card.

## 1:35–2:10 — The autonomy boundary

Point to **Human decision needed**. Explain that a contractual expectation is a
high-risk change. Deterministic policy pauses the workflow; the ADK agent is
not given an approval tool and cannot manufacture a human decision.

## 2:10–2:45 — Approve, resume, and undo

Choose a different action for one artifact, then click **Approve action plan**.
Call out that the deterministic decision is a human gate, not a model-generated
permission. The public flow creates only an isolated packet and operational
output; it does not write to external systems.
Show the packet-ready, owner-review, and queued rows, the named Demo operator,
the evidence hash, and the real audit event ID. Open the generated packet and
show its explicit “External systems changed: No” line plus the connector cards'
`prepared_only` status. Explain that public demo approvals cannot write to
external systems; only the separately authenticated signed-operator lane can.
Click **Reopen decision** and show that the high-risk gate and draft statuses
return.

## 2:45–3:25 — Live Google path and Cloud proof

Show the Agent run panel with `gemini-3.5-flash`, `google_adk`, the two
allowlisted tools, and the job event count. In a terminal or API client, show
the same `/api/jobs/{job_id}` payload, the Cloud Run revision, the
`/api/ops/summary` approval posture, and a Firestore job/workflow document with
its `audit_events` subcollection. If signed-operator proof is shown, use a
separate authenticated capture and never expose the signing secret.

## 3:25–4:00 — Close

Caption: “Driftline is not another alert and not another chat window. It is an
auditable change-to-action system: autonomous where policy allows, human where
judgment matters.”

End on the deployed URL, repository URL, and architecture diagram URL. The
official rules require the final video to be publicly visible; keep the current
YouTube draft private until the product and all claims are final.
