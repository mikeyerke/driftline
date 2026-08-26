# Driftline submission assets

- `driftline-decision-twin-architecture.png`: 1600×900 final Decision Twin
  architecture upload.
- `driftline-decision-twin-architecture.svg`: editable source for that upload.
- `driftline-decision-twin-candidate-architecture.png`: 1600×900 local review
  render of the unreleased action-to-learning candidate. Do not upload it until
  that exact candidate commit has passed release identity and browser proof.
- `driftline-decision-twin-candidate-architecture.svg`: editable source for the
  candidate render. Its unreleased badge and pending release gate are
  intentional custody controls.
- `driftline-architecture.png` / `.svg`: historical operational-foundation
  diagram; do not use as the primary Devpost image.

The PNGs in this folder are submission-frame references captured from the
public Cloud Run application at 1440×810. Replace them after each release
capture; the synthetic/public-source badge is part of the product UI. The
captions are written for a silent, caption-led demo so no voice or likeness is
synthesized.

- `driftline-pending-approval.png`: live scan paused at the deterministic gate.
- `driftline-evidence-modal.png`: live SHA-256 evidence modal.
- `driftline-completed.png`: live approval with packet-ready, owner-review, and
  queued artifact outcomes plus a durable audit event.
- `driftline-activity-log.png`: live workflow activity log.
- `driftline-undo.png`: live undo state returned to the approval gate.
- `driftline-final-slide.png`: captioned Google technology and public-link end
  card.
- `driftline-demo-captions.srt`: matching caption track for the four-minute
  silent demo render.
- `driftline-live-demo.mp4`: 43-second historical proof clip; do not submit it.
- `decision-twin-*-final.png`: exact-release browser captures from serving app
  `03ec8f12fc23d265c89b462a345a5b599a6411e8`.
- `demo-slide-*.png`: 1920×1080 captioned frames rendered from those captures.
- `driftline-final-demo-review.mp4`: three-minute, 1080p/30fps, captioned local
  review cut with English reference narration. It is upload-ready as a fallback,
  but a continuous native browser take remains the strongest final submission.
- `driftline-final-demo.srt`: matching accessible caption track.
- `driftline-continuous-candidate-proof.mp4`: 31.17-second local-only
  visible-click continuity rehearsal. It is unreleased candidate QA, not a
  deploy or customer-outcome claim.
- `driftline-candidate-rehearsal-narration.txt` and
  `driftline-candidate-rehearsal-overlays.svg`: exact local-only narration,
  watermark, and captions for a 52-second candidate rehearsal. Build it with
  `scripts/build_candidate_rehearsal.sh`. The result is permanently watermarked
  **UNRELEASED LOCAL CANDIDATE · NOT PRODUCTION** and must not be submitted as
  live proof.
- `driftline-final-demo-candidate.mp4`: 3:40 local fallback that mixes candidate
  screens with pre-candidate release narration. Do not submit it; its custody
  language is intentionally superseded by the watermarked rehearsal above.

The final entry still needs a public YouTube or Vimeo URL. Prefer a continuous
native browser recording that follows `submission/DEMO_SCRIPT.md`; use the
review cut only if a native take cannot be completed in time.
