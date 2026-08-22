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

printf 'Frontend literal ID contract: PASS\n'
