#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROOF="$ROOT_DIR/submission/assets/driftline-continuous-candidate-proof.mp4"
ARCHITECTURE="$ROOT_DIR/submission/assets/driftline-decision-twin-candidate-architecture.png"
NARRATION="$ROOT_DIR/submission/assets/driftline-candidate-rehearsal-narration.txt"
OVERLAYS="$ROOT_DIR/submission/assets/driftline-candidate-rehearsal-overlays.svg"
OUTPUT="${1:-$ROOT_DIR/submission/assets/driftline-candidate-rehearsal-tight.mp4}"

for command_name in ffmpeg ffprobe say sips; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 1
  }
done

for input_path in "$PROOF" "$ARCHITECTURE" "$NARRATION" "$OVERLAYS"; do
  [[ -s "$input_path" ]] || {
    printf 'Missing required candidate rehearsal input: %s\n' "$input_path" >&2
    exit 1
  }
done

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

say -v Samantha -r 235 -f "$NARRATION" -o "$TMP_DIR/narration.aiff"
sips -s format png "$OVERLAYS" --out "$TMP_DIR/overlays.png" >/dev/null

ffmpeg -y -v error \
  -i "$PROOF" \
  -loop 1 -t 20.833333 -i "$ARCHITECTURE" \
  -i "$TMP_DIR/narration.aiff" \
  -loop 1 -t 52 -i "$TMP_DIR/overlays.png" \
  -filter_complex \
  "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1424,setsar=1,fps=30[proof];[1:v]scale=1920:1080,setsar=1,fps=30[architecture];[proof][architecture]concat=n=2:v=1:a=0[base];[3:v]fps=30,crop=1920:1080:0:'if(lt(t,7),0,if(lt(t,15),1080,if(lt(t,24),2160,if(lt(t,32),3240,if(lt(t,41),4320,5400)))))'[overlay];[base][overlay]overlay=0:0:shortest=1,format=yuv420p[v];[2:a]aresample=48000,apad=pad_dur=60[a]" \
  -map "[v]" -map "[a]" \
  -t 52 \
  -c:v libx264 -preset medium -crf 18 -profile:v high -level 4.1 \
  -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -movflags +faststart \
  "$OUTPUT"

ffprobe -v error \
  -show_entries format=filename,duration,size:stream=codec_name,codec_type,width,height,pix_fmt,r_frame_rate,sample_rate,channels \
  -of json "$OUTPUT" >"$TMP_DIR/probe.json"

ffmpeg -hide_banner -i "$OUTPUT" -vf "blackdetect=d=0.25:pix_th=0.02" \
  -an -f null - >"$TMP_DIR/black.stdout" 2>"$TMP_DIR/black.log"
if rg -q 'black_start' "$TMP_DIR/black.log"; then
  printf 'Candidate rehearsal contains a black interval:\n' >&2
  rg 'black_start' "$TMP_DIR/black.log" >&2
  exit 1
fi

ffmpeg -hide_banner -i "$OUTPUT" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" \
  -f null - >"$TMP_DIR/loudness.stdout" 2>"$TMP_DIR/loudness.log"

python3 - "$TMP_DIR/probe.json" "$TMP_DIR/loudness.log" <<'PY'
import json
from pathlib import Path
import re
import sys

probe = json.loads(Path(sys.argv[1]).read_text())
duration = float(probe["format"]["duration"])
if not 51.9 <= duration <= 52.1:
    raise SystemExit(f"candidate rehearsal duration out of bounds: {duration:.3f}s")

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
        raise SystemExit(
            f"candidate rehearsal video {key} is {video.get(key)!r}; expected {expected!r}"
        )
if audio.get("codec_name") != "aac" or audio.get("sample_rate") != "48000" or audio.get("channels") != 2:
    raise SystemExit(f"candidate rehearsal audio contract failed: {audio}")

loudness_log = Path(sys.argv[2]).read_text()
match = re.search(r'"input_i"\s*:\s*"(-?[0-9.]+)"', loudness_log)
if not match:
    raise SystemExit("candidate rehearsal loudness measurement is missing")
integrated_loudness = float(match.group(1))
if not -18.0 <= integrated_loudness <= -14.0:
    raise SystemExit(
        f"candidate rehearsal loudness is {integrated_loudness:.2f} LUFS; expected -18 to -14"
    )
PY

cat "$TMP_DIR/probe.json"
printf 'Candidate rehearsal checks passed: no black intervals; loudness in range.\n'
