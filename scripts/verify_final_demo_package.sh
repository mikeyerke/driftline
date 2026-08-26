#!/usr/bin/env bash
set -euo pipefail

VIDEO_PATH="${1:-}"
CAPTIONS_PATH="${2:-}"
MANIFEST_PATH="${3:-}"

usage() {
  printf 'Usage: %s VIDEO.mp4 CAPTIONS.srt MANIFEST.json\n' "$0" >&2
  exit 2
}

[[ -n "$VIDEO_PATH" && -n "$CAPTIONS_PATH" && -n "$MANIFEST_PATH" ]] || usage

for command_name in ffmpeg ffprobe python3 rg shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Final demo check failed: missing required command %s\n' "$command_name" >&2
    exit 1
  }
done

for input_path in "$VIDEO_PATH" "$CAPTIONS_PATH" "$MANIFEST_PATH"; do
  [[ -s "$input_path" ]] || {
    printf 'Final demo check failed: missing or empty input %s\n' "$input_path" >&2
    exit 1
  }
done

VIDEO_PREFLIGHT_SHA="$(shasum -a 256 "$VIDEO_PATH" | awk '{print $1}')"
case "$VIDEO_PREFLIGHT_SHA" in
  3bcc2e98c0133a8caf2d6089609b3055b2b3f03574079c7c05f7fabfe63841ac|\
  f79abadb65bf393a3221db810efa7a8212ac5430e7e3d3efa03c8def489bd42e|\
  24a693d2f0bb4633f337c06429dff871fd5c565135f088ba12009aee17f96645|\
  db0c59c4f52e020ba2d1d6a46b1f5d874925a1e4bdb55d306ee22f04e46b769a|\
  14b50b61d8674be7ff5f48e38411c732bbbaf2b93c73cc190c8b8e6a6223472e|\
  4605822e7726d280eaf8f8da67191b13b2c3d7bc6ab4f4ee45f3ba310c81d9e6|\
  f12467768113ed106d5c5a9bb43c3f8b6229c5990809b0c333568d15151171dc)
    printf 'Final demo check failed: video content matches a quarantined rehearsal or historical proof asset.\n' >&2
    exit 1
    ;;
esac

case "$(basename "$VIDEO_PATH")" in
  driftline-final-demo-candidate.mp4|driftline-final-demo-rehearsal.mp4|driftline-candidate-rehearsal-tight.mp4|driftline-continuous-candidate-proof.mp4|driftline-continuous-candidate-presentation.mp4|driftline-live-demo.mp4)
    printf 'Final demo check failed: %s is a quarantined rehearsal or historical proof asset.\n' \
      "$(basename "$VIDEO_PATH")" >&2
    exit 1
    ;;
esac

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ffprobe -v error \
  -show_entries format=duration,size:stream=codec_name,codec_type,width,height,pix_fmt,r_frame_rate,sample_rate,channels \
  -of json "$VIDEO_PATH" >"$TMP_DIR/probe.json"

# Rehearsals carry a permanent dark-red custody band across the top 42 pixels.
# Sample it by content so renaming a quarantined file cannot turn it into a
# final package. A real take may contain isolated red UI, but must not preserve
# this full-width band across the recording.
ffmpeg -v error -i "$VIDEO_PATH" \
  -vf "fps=1/30,crop=iw:42:0:0,scale=1:1,format=rgb24" \
  -frames:v 6 -f rawvideo "$TMP_DIR/top-band.rgb"

python3 - "$TMP_DIR/top-band.rgb" <<'PY'
from pathlib import Path
import sys

samples = list(Path(sys.argv[1]).read_bytes())
if len(samples) < 9 or len(samples) % 3:
    raise SystemExit("Final demo check failed: top-band custody scan produced invalid samples")
rgb = [tuple(samples[index:index + 3]) for index in range(0, len(samples), 3)]
red_band_samples = [
    sample for sample in rgb
    if sample[0] >= 105 and sample[0] >= sample[1] * 1.55 and sample[0] >= sample[2] * 1.35
]
if len(red_band_samples) >= max(2, len(rgb) - 1):
    raise SystemExit(
        "Final demo check failed: persistent red top-band custody watermark detected"
    )
PY

ffmpeg -hide_banner -i "$VIDEO_PATH" -vf "blackdetect=d=0.25:pix_th=0.02" \
  -an -f null - >"$TMP_DIR/black.stdout" 2>"$TMP_DIR/black.log"

ffmpeg -hide_banner -i "$VIDEO_PATH" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" \
  -f null - >"$TMP_DIR/loudness.stdout" 2>"$TMP_DIR/loudness.log"

ffmpeg -hide_banner -i "$VIDEO_PATH" \
  -af "silencedetect=n=-42dB:d=4" -f null - \
  >"$TMP_DIR/silence.stdout" 2>"$TMP_DIR/silence.log"

if rg -q 'black_start' "$TMP_DIR/black.log"; then
  printf 'Final demo check failed: detected a black interval of at least 0.25 seconds.\n' >&2
  rg 'black_start' "$TMP_DIR/black.log" >&2
  exit 1
fi

if rg -q 'silence_duration: ([4-9]|[1-9][0-9])' "$TMP_DIR/silence.log"; then
  printf 'Final demo check failed: detected a narration silence of at least four seconds.\n' >&2
  rg 'silence_(start|end)' "$TMP_DIR/silence.log" >&2
  exit 1
fi

python3 - "$VIDEO_PATH" "$CAPTIONS_PATH" "$MANIFEST_PATH" \
  "$TMP_DIR/probe.json" "$TMP_DIR/loudness.log" <<'PY'
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys


video_path = Path(sys.argv[1])
captions_path = Path(sys.argv[2])
manifest_path = Path(sys.argv[3])
probe_path = Path(sys.argv[4])
loudness_path = Path(sys.argv[5])


def fail(message: str) -> None:
    raise SystemExit(f"Final demo check failed: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


probe = json.loads(probe_path.read_text())
duration = float(probe["format"]["duration"])
if not 120 <= duration <= 236:
    fail(f"duration is {duration:.3f}s; expected 120–236 seconds")

streams = {stream["codec_type"]: stream for stream in probe["streams"]}
video = streams.get("video", {})
audio = streams.get("audio", {})
if video.get("codec_name") != "h264":
    fail(f"video codec is {video.get('codec_name')!r}; expected H.264")
if (video.get("width"), video.get("height")) != (1920, 1080):
    fail(
        f"video dimensions are {video.get('width')}x{video.get('height')}; "
        "expected 1920x1080"
    )
if video.get("r_frame_rate") not in {"30/1", "30000/1001"}:
    fail(f"frame rate is {video.get('r_frame_rate')!r}; expected 30 fps")
if video.get("pix_fmt") not in {"yuv420p", "yuvj420p"}:
    fail(f"pixel format is {video.get('pix_fmt')!r}; expected 4:2:0 playback format")
if audio.get("codec_name") != "aac":
    fail(f"audio codec is {audio.get('codec_name')!r}; expected AAC")
if audio.get("sample_rate") != "48000" or audio.get("channels") not in {1, 2}:
    fail(f"audio contract failed: {audio}")

loudness = loudness_path.read_text()
integrated_match = re.search(r'"input_i"\s*:\s*"(-?[0-9.]+)"', loudness)
peak_match = re.search(r'"input_tp"\s*:\s*"(-?[0-9.]+)"', loudness)
if not integrated_match or not peak_match:
    fail("loudness measurements are missing")
integrated = float(integrated_match.group(1))
peak = float(peak_match.group(1))
if not -18 <= integrated <= -14:
    fail(f"integrated loudness is {integrated:.2f} LUFS; expected -18 to -14")
if peak > -1:
    fail(f"true peak is {peak:.2f} dBTP; expected no higher than -1 dBTP")

caption_text = captions_path.read_text()
required_caption_claims = (
    "Driftline",
    "Google ADK",
    "Gemini",
    "Firebase Hosting",
    "Cloud Run",
    "Firestore",
    "BigQuery",
    "Cloud Tasks",
    "named human",
    "Generation 2",
    "External writes: none",
)
for claim in required_caption_claims:
    if claim.casefold() not in caption_text.casefold():
        fail(f"captions omit required judge claim: {claim}")

timestamp_pattern = re.compile(
    r"(?P<sh>\d{2}):(?P<sm>\d{2}):(?P<ss>\d{2}),(?P<sms>\d{3})\s+-->\s+"
    r"(?P<eh>\d{2}):(?P<em>\d{2}):(?P<es>\d{2}),(?P<ems>\d{3})"
)


def seconds(match: re.Match[str], prefix: str) -> float:
    return (
        int(match[f"{prefix}h"]) * 3600
        + int(match[f"{prefix}m"]) * 60
        + int(match[f"{prefix}s"])
        + int(match[f"{prefix}ms"]) / 1000
    )


cues = [(seconds(match, "s"), seconds(match, "e")) for match in timestamp_pattern.finditer(caption_text)]
if len(cues) < 8:
    fail(f"captions contain only {len(cues)} timed cues; expected at least 8")
if cues[0][0] > 2:
    fail("first caption begins after the first two seconds")
if cues[-1][1] < duration - 5 or cues[-1][1] > duration + 1:
    fail("last caption does not end within five seconds of the video")
previous_end = 0.0
for start, end in cues:
    if start < previous_end or end <= start:
        fail("caption timings overlap or are not strictly increasing")
    previous_end = end

manifest = json.loads(manifest_path.read_text())
required_fields = {
    "recorded_at",
    "source_url",
    "release_sha",
    "health_sha",
    "public_main_sha",
    "cloud_run_revision",
    "cloud_build_id",
    "image_digest",
    "video_sha256",
    "captions_sha256",
    "duration_seconds",
    "first_agent_action_timestamp_seconds",
    "first_agent_action_visible",
    "preapproval_background_workflow_visible",
    "continuous_native_take",
    "setup_and_loading_omitted",
    "human_approval_timestamp_seconds",
    "named_human_approval_visible",
    "bounded_action_receipt_timestamp_seconds",
    "bounded_action_receipt_visible",
    "generation_2_timestamp_seconds",
    "generation_2_reopen_visible",
    "generation_1_lineage_visible",
    "approval_to_reopen_continuous",
    "secrets_reviewed",
    "external_writes_none_visible",
    "google_cloud_proof_type",
    "google_cloud_proof_timestamp_seconds",
    "google_cloud_proof_visible",
    "google_cloud_proof_identity_matches_release",
    "release_proof_visible",
    "candidate_watermark_absent",
}
if set(manifest) != required_fields:
    missing = sorted(required_fields - set(manifest))
    unexpected = sorted(set(manifest) - required_fields)
    fail(f"manifest fields differ; missing={missing}, unexpected={unexpected}")

try:
    recorded_at = dt.datetime.fromisoformat(str(manifest["recorded_at"]).replace("Z", "+00:00"))
except ValueError:
    fail("recorded_at is not an ISO-8601 timestamp")
if recorded_at.tzinfo is None:
    fail("recorded_at must include a timezone")
if manifest["source_url"] != "https://driftline-ops.web.app/":
    fail("source_url is not the canonical hosted application")

sha_pattern = re.compile(r"[0-9a-f]{40}")
release_shas = [manifest[key] for key in ("release_sha", "health_sha", "public_main_sha")]
if any(not isinstance(value, str) or not sha_pattern.fullmatch(value) for value in release_shas):
    fail("release, health, and public-main SHAs must be full lowercase Git commits")
if len(set(release_shas)) != 1 or release_shas[0] == "0" * 40:
    fail("release, health, and public-main SHAs must match a non-placeholder commit")
if not re.fullmatch(r"driftline-[0-9]{5}-[a-z0-9]{3}", str(manifest["cloud_run_revision"])):
    fail("Cloud Run revision format is invalid")
if not re.fullmatch(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    str(manifest["cloud_build_id"]),
):
    fail("Cloud Build ID format is invalid")
if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(manifest["image_digest"])):
    fail("image digest format is invalid")

if manifest["video_sha256"] != sha256(video_path):
    fail("video SHA-256 does not match the manifest")
if manifest["captions_sha256"] != sha256(captions_path):
    fail("caption SHA-256 does not match the manifest")
if abs(float(manifest["duration_seconds"]) - duration) > 0.1:
    fail("manifest duration does not match the media")

for key in (
    "first_agent_action_visible",
    "preapproval_background_workflow_visible",
    "continuous_native_take",
    "setup_and_loading_omitted",
    "named_human_approval_visible",
    "bounded_action_receipt_visible",
    "generation_2_reopen_visible",
    "generation_1_lineage_visible",
    "approval_to_reopen_continuous",
    "secrets_reviewed",
    "external_writes_none_visible",
    "google_cloud_proof_visible",
    "google_cloud_proof_identity_matches_release",
    "release_proof_visible",
    "candidate_watermark_absent",
):
    if manifest[key] is not True:
        fail(f"manifest gate is not affirmed: {key}")

try:
    first_action_timestamp = float(manifest["first_agent_action_timestamp_seconds"])
    approval_timestamp = float(manifest["human_approval_timestamp_seconds"])
    receipt_timestamp = float(manifest["bounded_action_receipt_timestamp_seconds"])
    generation_2_timestamp = float(manifest["generation_2_timestamp_seconds"])
except (TypeError, ValueError):
    fail("first-action, approval, receipt, and generation-2 timestamps must be numeric")
if not 0 <= first_action_timestamp <= 15:
    fail("the first visible agent action must occur within the first 15 seconds")
if first_action_timestamp >= approval_timestamp:
    fail("the first visible agent action must precede named-human approval")
if not 60 <= approval_timestamp <= 100:
    fail("named-human approval must be visibly timestamped between 60 and 100 seconds")
if not approval_timestamp <= receipt_timestamp <= approval_timestamp + 20:
    fail("bounded action receipt must become visible within 20 seconds after approval")
if not receipt_timestamp < generation_2_timestamp <= 140:
    fail("generation-2 reopen must follow the receipt and be visible by 140 seconds")

proof_type = manifest["google_cloud_proof_type"]
if proof_type not in {"cloud_run_console", "cloud_run_url"}:
    fail(
        "google_cloud_proof_type must be cloud_run_console or cloud_run_url"
    )
try:
    proof_timestamp = float(manifest["google_cloud_proof_timestamp_seconds"])
except (TypeError, ValueError):
    fail("google_cloud_proof_timestamp_seconds must be numeric")
if not 0 <= proof_timestamp <= duration - 10:
    fail(
        "Google Cloud proof must begin at least ten seconds before the video ends"
    )

print(
    "Final demo package checks passed: "
    f"{duration:.3f}s, {integrated:.2f} LUFS, {peak:.2f} dBTP, "
    f"release {release_shas[0]}."
)
PY
