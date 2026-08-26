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

for command_name in ffmpeg ffprobe python3 rg; do
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

case "$(basename "$VIDEO_PATH")" in
  driftline-final-demo-candidate.mp4|driftline-candidate-rehearsal-tight.mp4|driftline-continuous-candidate-proof.mp4|driftline-live-demo.mp4)
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
    "approval_to_reopen_continuous",
    "secrets_reviewed",
    "external_writes_none_visible",
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
    "approval_to_reopen_continuous",
    "secrets_reviewed",
    "external_writes_none_visible",
    "release_proof_visible",
    "candidate_watermark_absent",
):
    if manifest[key] is not True:
        fail(f"manifest gate is not affirmed: {key}")

print(
    "Final demo package checks passed: "
    f"{duration:.3f}s, {integrated:.2f} LUFS, {peak:.2f} dBTP, "
    f"release {release_shas[0]}."
)
PY
