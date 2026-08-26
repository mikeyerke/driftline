#!/usr/bin/env bash
set -euo pipefail

VIDEO_PATH="${1:-}"
MANIFEST_PATH="${2:-}"
OUTPUT_PATH="${3:-}"

if [[ -z "$VIDEO_PATH" || -z "$MANIFEST_PATH" || -z "$OUTPUT_PATH" ]]; then
  printf 'Usage: %s VIDEO.mp4 MANIFEST.json OUTPUT.png\n' "$0" >&2
  exit 2
fi

for command_name in ffmpeg python3; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Final demo review sheet failed: missing %s.\n' "$command_name" >&2
    exit 1
  }
done

for input_path in "$VIDEO_PATH" "$MANIFEST_PATH"; do
  [[ -s "$input_path" ]] || {
    printf 'Final demo review sheet failed: missing or empty input %s.\n' \
      "$input_path" >&2
    exit 1
  }
done

[[ -d "$(dirname "$OUTPUT_PATH")" ]] || {
  printf 'Final demo review sheet failed: output directory does not exist.\n' >&2
  exit 1
}

TIMESTAMPS="$({
  python3 - "$MANIFEST_PATH" <<'PY'
import json
from pathlib import Path
import sys

manifest = json.loads(Path(sys.argv[1]).read_text())
keys = (
    "human_approval_timestamp_seconds",
    "bounded_action_receipt_timestamp_seconds",
    "generation_2_timestamp_seconds",
    "google_cloud_proof_timestamp_seconds",
)
values = []
for key in keys:
    try:
        value = float(manifest[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(
            f"Final demo review sheet failed: invalid manifest timestamp {key}"
        ) from exc
    if value < 0:
        raise SystemExit(
            f"Final demo review sheet failed: negative manifest timestamp {key}"
        )
    values.append(f"{value:.3f}")
print(" ".join(values))
PY
} 2>&1)" || {
  printf '%s\n' "$TIMESTAMPS" >&2
  exit 1
}

read -r APPROVAL_TS RECEIPT_TS GENERATION_TS CLOUD_TS <<EOF
$TIMESTAMPS
EOF

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

extract_frame() {
  local timestamp="$1"
  local output="$2"
  ffmpeg -y -v error -ss "$timestamp" -i "$VIDEO_PATH" -frames:v 1 \
    -vf "scale=954:534,pad=960:540:3:3:color=white" \
    "$output"
}

extract_frame "$APPROVAL_TS" "$TMP_DIR/1.png"
extract_frame "$RECEIPT_TS" "$TMP_DIR/2.png"
extract_frame "$GENERATION_TS" "$TMP_DIR/3.png"
extract_frame "$CLOUD_TS" "$TMP_DIR/4.png"

ffmpeg -y -v error \
  -i "$TMP_DIR/1.png" -i "$TMP_DIR/2.png" \
  -i "$TMP_DIR/3.png" -i "$TMP_DIR/4.png" \
  -filter_complex "xstack=inputs=4:layout=0_0|960_0|0_540|960_540" \
  -frames:v 1 "$OUTPUT_PATH"

printf 'Final demo review sheet created: %s\n' "$OUTPUT_PATH"
printf 'Panels: 1 NAMED HUMAN APPROVAL @ %ss; 2 BOUNDED ACTION RECEIPT @ %ss; 3 GENERATION 2 REOPEN @ %ss; 4 VISIBLE GOOGLE CLOUD PROOF @ %ss.\n' \
  "$APPROVAL_TS" "$RECEIPT_TS" "$GENERATION_TS" "$CLOUD_TS"
