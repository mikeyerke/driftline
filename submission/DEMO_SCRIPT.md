# Four-minute demo

The official rules cap the evaluated video at four minutes. Use captions or
the entrant's own narration; do not synthesize the entrant's voice or likeness.
Show the public Cloud Run URL and a Cloud Run or log view in the same recording.

## 0:00–0:25 — The problem

Caption: “One sentence changes on a public pricing page. The alert is easy.
Finding every downstream promise, deciding what can update safely, and proving
who approved the risky part is the actual work.”

Show the deployed Driftline console and the “Synthetic demo data” label.

## 0:25–0:55 — Start the workflow

Click **Run scan**. Explain that the deterministic synthetic fixture creates a
reproducible workflow for judges. Show the /api/workflows/demo request in the
browser network view or a terminal beside the console. The live /api/agent/run
path is shown separately so the demo does not imply that the fixture itself
needed a model call.

## 0:55–1:35 — Evidence and impact

Open **Evidence diff** and then **Open evidence**. Show the exact removed and
added language, the synthetic source ID, the full SHA-256 hash, and the
confidence value. Trace the impact map into the battlecard, renewal playbook,
FAQ, and CRM guidance. Select an artifact row to show its owner, bounded action,
and risk.

## 1:35–2:10 — The autonomy boundary

Point to **Human decision needed**. Explain that a contractual expectation is a
high-risk change. Deterministic policy pauses the workflow; the ADK agent is
not given an approval tool and cannot manufacture a human decision.

## 2:10–2:45 — Approve, resume, and undo

Click **Approve exception path**. Show the two Published rows, one Owner Review
row, one Scheduled row, the named Demo operator, and the real audit event ID.
Open the Activity panel and show the event IDs and stages. Click **Undo
decision** and show that the high-risk gate and draft statuses return.

## 2:45–3:25 — Live Google path and Cloud proof

In a terminal or API client, call the deployed /api/agent/run endpoint with
the allowlisted synthetic source request. Show the response model,
execution_mode, and tool_calls fields. Show the Cloud Run URL, revision, and a
log line from the same request, plus a Firestore document containing the
workflow and its audit_events subcollection.

## 3:25–4:00 — Close

Caption: “Driftline is not another alert and not another chat window. It is an
auditable change-to-action system: autonomous where policy allows, human where
judgment matters.”

End on the deployed URL, repository URL, and architecture diagram URL.
