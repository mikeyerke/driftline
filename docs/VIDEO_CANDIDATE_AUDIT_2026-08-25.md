# Demo candidate audit — 2026-08-25

Status: local review only. Nothing uploaded or published.

## Verdict

`submission/assets/driftline-final-demo-candidate.mp4` is safe as an emergency
fallback and is not the strongest judging artifact. It explains the product
clearly, stays under four minutes, and is technically clean. Its main weakness
is evidentiary: long static browser frames make it feel like a narrated deck,
while the rubric rewards a visibly working agent and an unedited proof of
action.

## Measured technical checks

- Duration: 220.0 seconds (3:40).
- Video: H.264, 1920×1080, 30 fps.
- Audio: AAC, 48 kHz stereo.
- Integrated loudness: approximately -16.3 LUFS.
- True peak: approximately -4.5 dBFS.
- Detected black frames of 0.4 seconds or longer: none.
- File size: 13,861,783 bytes.

## Judge-visible strengths

- Product and problem appear immediately.
- Captions are large, high contrast, and understandable without audio.
- The sequence covers evidence, ADK dissent, counterfactuals, human approval,
  measured invalidation, generation-two reopening, and Google Cloud.
- No customer outcome, external write, or autonomous approval is fabricated.

## Score risk

The video changes between mostly static browser states. Freeze detection found
many holds longer than 14 seconds and several near 20–24 seconds. That is not a
codec defect, but it makes the artifact weaker than a continuous native take.
The separate 40-second approval/reopen clip is also largely held frames and has
no audio. Neither should be described as an unedited click recording.

## Release-gated replacement

After the local candidate is explicitly authorized for release and exact-SHA
proof passes, record one native browser take that:

1. keeps the council → approval → monitor → rollback → reopen sequence tied
   to one visible case;
2. shows the bounded internal action and **external writes: none**;
3. leaves the browser cursor and state transitions visible;
4. ends on the candidate architecture only after its unreleased badge is no
   longer true and the proof panel shows the serving commit, revision, build,
   digest, live trace, and BigQuery source; and
5. is watched once at 1×, once muted, and once at phone size before upload.

Until then, the current MP4 remains a local fallback and earns no public-video
credit.
