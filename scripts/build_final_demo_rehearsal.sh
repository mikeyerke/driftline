#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROOF="${1:-$ROOT_DIR/submission/assets/driftline-continuous-candidate-presentation.mp4}"
OUTPUT="${2:-$ROOT_DIR/submission/assets/driftline-final-demo-rehearsal.mp4}"
ARCHITECTURE="$ROOT_DIR/submission/assets/driftline-decision-twin-candidate-architecture.png"
NARRATION="$ROOT_DIR/submission/assets/driftline-final-rehearsal-narration.txt"
CAPTIONS="$ROOT_DIR/submission/assets/driftline-final-rehearsal.srt"
WATERMARK="$ROOT_DIR/submission/assets/driftline-final-rehearsal-watermark.svg"
CAPTION_OVERLAYS="$ROOT_DIR/submission/assets/driftline-final-rehearsal-caption-overlays.svg"

for command_name in ffmpeg ffprobe say rg sips; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 1
  }
done

for input_path in "$PROOF" "$ARCHITECTURE" "$NARRATION" "$CAPTIONS" "$WATERMARK" "$CAPTION_OVERLAYS"; do
  [[ -s "$input_path" ]] || {
    printf 'Missing required final-rehearsal input: %s\n' "$input_path" >&2
    exit 1
  }
done

python3 - "$CAPTIONS" <<'PY'
from pathlib import Path
import re
import sys

caption_path = Path(sys.argv[1])
caption_text = caption_path.read_text()
pattern = re.compile(
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


cues = [(seconds(match, "s"), seconds(match, "e")) for match in pattern.finditer(caption_text)]
if len(cues) != 15:
    raise SystemExit(f"final rehearsal captions contain {len(cues)} cues; expected 15")
previous_end = 0.0
for start, end in cues:
    if start < previous_end or end <= start:
        raise SystemExit("final rehearsal captions overlap or are not strictly increasing")
    previous_end = end
if cues[0][0] != 0 or cues[-1][1] != 178:
    raise SystemExit("final rehearsal captions must cover exactly 0–178 seconds")
PY

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

say -v Samantha -r 155 -f "$NARRATION" -o "$TMP_DIR/narration.aiff"
sips -s format png "$WATERMARK" --out "$TMP_DIR/watermark.png" >/dev/null
sips -s format png "$CAPTION_OVERLAYS" --out "$TMP_DIR/caption-overlays.png" >/dev/null
NARRATION_DURATION="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TMP_DIR/narration.aiff")"
PROOF_DURATION="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$PROOF")"

python3 - "$NARRATION_DURATION" "$PROOF_DURATION" <<'PY'
import sys

narration = float(sys.argv[1])
proof = float(sys.argv[2])
if not 165 <= narration <= 182:
    raise SystemExit(f"final rehearsal narration duration out of bounds: {narration:.3f}s")
if not 90 <= proof <= 135:
    raise SystemExit(f"presentation proof duration out of bounds: {proof:.3f}s")
PY

ffmpeg -y -v error \
  -i "$PROOF" \
  -loop 1 -t 52 -i "$ARCHITECTURE" \
  -i "$TMP_DIR/narration.aiff" \
  -loop 1 -t 178 -i "$TMP_DIR/watermark.png" \
  -loop 1 -t 178 -i "$TMP_DIR/caption-overlays.png" \
  -i "$CAPTIONS" \
  -filter_complex \
  "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease:in_range=pc:out_range=tv,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1424,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=30[proof];[1:v]scale=1920:1080,zoompan=z='min(zoom+0.00018,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1560:s=1920x1080:fps=30,setsar=1[architecture];[proof][architecture]concat=n=2:v=1:a=0[sequence];[3:v]scale=1920:42,setsar=1,fps=30[watermark];[4:v]fps=30,crop=1920:1080:0:'if(lt(t,11),0,if(lt(t,27),1080,if(lt(t,42),2160,if(lt(t,53),3240,if(lt(t,69),4320,if(lt(t,82),5400,if(lt(t,92),6480,if(lt(t,105),7560,if(lt(t,118),8640,if(lt(t,130),9720,if(lt(t,143),10800,if(lt(t,156),11880,if(lt(t,163),12960,if(lt(t,172),14040,15120))))))))))))))'[captions];[sequence][watermark]overlay=0:0:shortest=1[watermarked];[watermarked][captions]overlay=0:0:shortest=1,format=yuv420p[v];[2:a]aresample=48000,apad=pad_dur=12,loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
  -map "[v]" -map "[a]" -map 5:0 \
  -t 178 \
  -shortest \
  -c:v libx264 -preset medium -crf 18 -profile:v high -level 4.1 \
  -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -c:s mov_text -metadata:s:s:0 language=eng \
  -movflags +faststart \
  "$OUTPUT"

ffprobe -v error \
  -show_entries format=filename,duration,size:stream=codec_name,codec_type,width,height,pix_fmt,r_frame_rate,sample_rate,channels \
  -of json "$OUTPUT" >"$TMP_DIR/probe.json"

ffmpeg -hide_banner -i "$OUTPUT" -vf "blackdetect=d=0.25:pix_th=0.02" \
  -an -f null - >"$TMP_DIR/black.stdout" 2>"$TMP_DIR/black.log"
if rg -q 'black_start' "$TMP_DIR/black.log"; then
  printf 'Final rehearsal contains a black interval:\n' >&2
  rg 'black_start' "$TMP_DIR/black.log" >&2
  exit 1
fi

python3 - "$TMP_DIR/probe.json" <<'PY'
import json
from pathlib import Path
import sys

probe = json.loads(Path(sys.argv[1]).read_text())
duration = float(probe["format"]["duration"])
if not 120 <= duration <= 178.1:
    raise SystemExit(f"final rehearsal duration out of bounds: {duration:.3f}s")
streams = {stream["codec_type"]: stream for stream in probe["streams"]}
video = streams.get("video", {})
audio = streams.get("audio", {})
expected_video = {
    "codec_name": "h264",
    "width": 1920,
    "height": 1080,
    "pix_fmt": "yuv420p",
    "r_frame_rate": "30/1",
}
for key, expected in expected_video.items():
    if video.get(key) != expected:
        raise SystemExit(f"final rehearsal video {key} is {video.get(key)!r}; expected {expected!r}")
if audio.get("codec_name") != "aac" or audio.get("sample_rate") != "48000" or audio.get("channels") != 2:
    raise SystemExit(f"final rehearsal audio contract failed: {audio}")
PY

cat "$TMP_DIR/probe.json"
printf 'Final demo rehearsal checks passed: continuous browser proof, visible custody watermark, English caption track, audio, and no black intervals.\n'
