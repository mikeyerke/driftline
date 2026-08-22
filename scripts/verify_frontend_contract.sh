#!/usr/bin/env bash
set -euo pipefail

# Literal IDs in the React source become document anchors. Duplicate anchors
# make the sidebar navigation and assistive-technology landmarks ambiguous.
duplicates="$({
  rg -o 'id="[^"]+"' frontend/src || true
} | sed -E 's/.*id="([^"]+)".*/\1/' | sort | uniq -d)"

if [[ -n "$duplicates" ]]; then
  printf 'Duplicate frontend IDs detected:\n%s\n' "$duplicates" >&2
  exit 1
fi

# ``runScan`` accepts an optional source id. Passing it directly as a React
# click handler leaks the click event into JSON.stringify and produces a
# circular DOM-object failure before the API request. Keep the event boundary
# explicit so the public golden path always sends a string source id.
if rg -q 'onClick=\{runScan\}' frontend/src/App.jsx; then
  printf 'Run-scan event boundary is unsafe: pass a zero-argument callback.\n' >&2
  exit 1
fi

printf 'Frontend literal ID contract: PASS\n'
