#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'Submission packet check failed: %s\n' "$1" >&2
  exit 1
}

require_text() {
  local file="$1"
  local text="$2"
  rg -Fq -- "$text" "$file" || fail "$file is missing required text: $text"
}

for file in \
  devpost-submission.md \
  submission/DEVPOST.md \
  submission/DEMO_SCRIPT.md \
  submission/JUDGE_SCORECARD.md \
  docs/JUDGE_SCORECARD.md \
  submission/assets/driftline-decision-twin-candidate-architecture.svg \
  submission/assets/driftline-decision-twin-candidate-architecture.png; do
  [[ -s "$file" ]] || fail "$file is missing or empty"
done

cmp -s docs/JUDGE_SCORECARD.md submission/JUDGE_SCORECARD.md || \
  fail "judge scorecards have diverged"

if rg -Fq -- 'Final candidate identity is public `main`' submission/DEMO_SCRIPT.md; then
  fail "demo script mislabels the pre-candidate production release as the final candidate"
fi
require_text submission/DEMO_SCRIPT.md 'This is the pre-candidate release,'
require_text submission/DEMO_SCRIPT.md 'Reject the take unless public `main`,'
require_text submission/DEVPOST.md 'unreleased local candidate'
require_text devpost-submission.md 'Status: draft-ready, not release-ready or form-ready.'
require_text devpost-submission.md '| Architecture upload | `submission/assets/driftline-decision-twin-architecture.png` |'
require_text submission/assets/driftline-decision-twin-candidate-architecture.svg 'UNRELEASED CANDIDATE'
require_text submission/assets/driftline-decision-twin-candidate-architecture.svg 'release proof required before publication'

if rg -Fq -- 'submission/assets/driftline-architecture.png' devpost-submission.md; then
  fail "form packet still points at the historical architecture diagram"
fi

python3 - <<'PY'
import hashlib
from pathlib import Path
import re
import struct

def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"Submission packet check failed: {path} is not a PNG")
    return struct.unpack(">II", data[16:24])


expected_dimensions = {
    Path("submission/assets/driftline-decision-twin-architecture.png"): (1600, 900),
    Path("submission/assets/driftline-decision-twin-candidate-architecture.png"): (1600, 900),
    Path("submission/assets/driftline-final-slide.png"): (1440, 810),
}
for path, expected_size in expected_dimensions.items():
    if not path.is_file():
        raise SystemExit(f"Submission packet check failed: {path} is missing")
    actual_size = png_dimensions(path)
    if actual_size != expected_size:
        raise SystemExit(
            f"Submission packet check failed: {path} is "
            f"{actual_size[0]}x{actual_size[1]}, expected "
            f"{expected_size[0]}x{expected_size[1]}"
        )

path = Path("submission/assets/driftline-decision-twin-candidate-architecture.png")
data = path.read_bytes()
expected = "d03fa9106a860ce94fef5c6ca13b6cd967a0b4fa5b5c276092e233aea165c7db"
actual = hashlib.sha256(data).hexdigest()
if actual != expected:
    raise SystemExit(
        "Submission packet check failed: candidate architecture render does not "
        "match the reviewed full-frame asset; regenerate and review it before "
        f"updating the checksum (actual {actual})"
    )

link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
for document in (Path("devpost-submission.md"), Path("submission/DEVPOST.md")):
    for target in link_pattern.findall(document.read_text()):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        resolved = (document.parent / target_path).resolve()
        if not resolved.exists():
            raise SystemExit(
                f"Submission packet check failed: {document} links to missing {target}"
            )
PY

todo_lines="$(rg -n -i 'todo|placeholder|tbd|fixme|lorem' \
  devpost-submission.md submission/DEVPOST.md || true)"
unexpected_todo_lines="$(printf '%s\n' "$todo_lines" | rg -v \
  '(public YouTube or Vimeo URL|publish an approved draft from `submission/SOCIAL_POST_DRAFTS\.md`)' || true)"
[[ -z "$unexpected_todo_lines" ]] || \
  fail "unexpected placeholder text exists in the canonical submission copy"
[[ "$(printf '%s\n' "$todo_lines" | rg -c '.' || true)" == "3" ]] || \
  fail "the submission packet must contain exactly the three approved owner-only placeholders"

printf 'Submission packet checks passed.\n'
