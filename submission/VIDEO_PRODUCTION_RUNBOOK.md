# Final demo video production runbook

Status: production-ready script and capture plan. The existing short MP4 is a
rehearsal artifact, not the final submission video. Nothing has been uploaded.

## Capture setup

- 1920×1080, 30 fps, browser zoom 100%, notifications off.
- Use a fresh logged-out window for the public lane.
- Preload `/health` and Google Cloud proof in separate tabs; verify there are no
  tokens, tenant names, private records, or editable secret fields on screen.
- Use the serving release only. Record the release SHA and build ID in the take
  log before capture.
- Turn Judge Mode on and rehearse the path twice without recording.

## Single-take product sequence

1. URL and packet-safe lane.
2. Judge Mode and **Run live agent**.
3. Exact before/after evidence and full hash.
4. Four mapped surfaces and one artifact detail.
5. Decision Copilot, policy review, and visible human gate.
6. Human approval click in-frame.
7. Four-part proof receipt: Firestore action, artifact persistence, rollback,
   operation ID.
8. Owner queue and audit event.
9. Reopen decision; show return to the human gate and reversed history.

Do not splice across the approval click and receipt. A judge should be able to
see that the result came from the visible action in the same workflow.

## B-roll inserts

- `/health`: model, persistence, tasks, serving SHA, Cloud Build ID.
- Cloud Run revision and one redacted request log.
- Firestore workflow fields: status, operation, evidence hash, action record.
- Architecture image for the closing 20–25 seconds.

## Edit and QA

- Target 3:45–3:50; hard reject at 3:56 to protect the four-minute rule.
- Remove waits, not policy steps. Never accelerate narration beyond clarity.
- Burn in English captions and attach the matching `.srt`.
- Normalize speech, remove long silences, and confirm no music masks narration.
- Watch once at 1× without pausing, once muted for caption comprehension, and
  once at 720p for small-text legibility.
- Confirm the first 30 seconds shows the live URL and the last frame contains
  project name, URL, repository, category, and Google technology.

## Take log

| Take | Release SHA | Duration | Approval continuous | Secrets clean | Notes |
| --- | --- | ---: | --- | --- | --- |
|  |  |  |  |  |  |

## Entrant-owned final actions

The entrant records the narration/on-screen take, approves the final edit, and
uploads it publicly to YouTube or Vimeo. Those actions require identity,
voice/likeness, and public-publishing decisions and are intentionally not
performed by automation.
