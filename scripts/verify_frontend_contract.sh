#!/usr/bin/env bash
set -euo pipefail

# Literal IDs in the React source become document anchors. Duplicate anchors
# make the sidebar navigation and assistive-technology landmarks ambiguous.
if command -v rg >/dev/null 2>&1; then
  duplicate_matches="$(rg -o 'id="[^"]+"' frontend/src || true)"
else
  # GitHub's minimal runner image does not guarantee ripgrep. Keep this
  # release contract runnable in both the local and hosted verification
  # environments without changing what it validates.
  duplicate_matches="$(grep -RhoE 'id="[^"]+"' frontend/src || true)"
fi
duplicates="$(printf '%s\n' "$duplicate_matches" | sed -E 's/.*id="([^"]+)".*/\1/' | sort | uniq -d)"

if [[ -n "$duplicates" ]]; then
  printf 'Duplicate frontend IDs detected:\n%s\n' "$duplicates" >&2
  exit 1
fi

# ``runScan`` accepts an optional source id. Passing it directly as a React
# click handler leaks the click event into JSON.stringify and produces a
# circular DOM-object failure before the API request. Keep the event boundary
# explicit so the public golden path always sends a string source id.
if { command -v rg >/dev/null 2>&1 && rg -q 'onClick=\{runScan\}' frontend/src/App.jsx; } \
  || { ! command -v rg >/dev/null 2>&1 && grep -Eq 'onClick=\{runScan\}' frontend/src/App.jsx; }; then
  printf 'Run-scan event boundary is unsafe: pass a zero-argument callback.\n' >&2
  exit 1
fi

# A monitor disposition intentionally may have no workflow. The poller must
# terminate on every durable source outcome instead of waiting until the job
# timeout and reporting a false failure (no-op, baseline, or fetch outage).
if { command -v rg >/dev/null 2>&1 \
      && { ! rg -q 'current\.status === "complete"' frontend/src/App.jsx \
        || ! rg -q '!current\.workflow' frontend/src/App.jsx \
        || ! rg -q '"unchanged", "baseline_established"' frontend/src/App.jsx \
        || ! rg -q 'source_fetch_failed' frontend/src/App.jsx; }; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && { ! grep -Eq 'current\.status === "complete"' frontend/src/App.jsx \
        || ! grep -Eq '!current\.workflow' frontend/src/App.jsx \
        || ! grep -Eq '"unchanged", "baseline_established"' frontend/src/App.jsx \
        || ! grep -Eq 'source_fetch_failed' frontend/src/App.jsx; }; }; then
  printf 'Monitor terminal-outcome contract is incomplete: a no-workflow disposition could time out.\n' >&2
  exit 1
fi

# Starting Salesforce OAuth renders a provider URL before the operator leaves
# the console. A focus event must not immediately replace that handoff with a
# stale reauthorization status, or the connector cannot be completed from the
# product UI.
if { command -v rg >/dev/null 2>&1 && ! rg -q '!authorizing' frontend/src/components/SalesforceConnectorPanel.jsx; } \
  || { ! command -v rg >/dev/null 2>&1 && ! grep -Eq '!authorizing' frontend/src/components/SalesforceConnectorPanel.jsx; }; then
  printf 'Salesforce OAuth handoff guard is missing: focus could erase the consent URL before it is usable.\n' >&2
  exit 1
fi

# The source-registry "Check now" action is the production monitor lane. The
# repeatable synthetic replay remains available through the public/top demo
# path, but operator checks must compare the tenant's append-only ledger.
if { command -v rg >/dev/null 2>&1 \
      && ! rg -q 'return runScan\(sourceId, "monitor"\)' frontend/src/App.jsx; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && ! grep -Eq 'return runScan\(sourceId, "monitor"\)' frontend/src/App.jsx; }; then
  printf 'Monitor action contract is incomplete: source Check now is not routed to the monitor lane.\n' >&2
  exit 1
fi

# Change Memory is a tenant-sensitive view. It must forward the in-memory
# operator session so a signed operator never falls back to the anonymous
# evaluation ledger after signing in or switching tenants.
if { command -v rg >/dev/null 2>&1 \
      && ! rg -q 'getMemorySummary\(50, operatorSession\)' frontend/src/components/ChangeGenomePanel.jsx; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && ! grep -Eq 'getMemorySummary\(50, operatorSession\)' frontend/src/components/ChangeGenomePanel.jsx; } \
  || { command -v rg >/dev/null 2>&1 \
      && ! rg -q 'operatorSession=\{operatorSession\}' frontend/src/App.jsx; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && ! grep -Eq 'operatorSession=\{operatorSession\}' frontend/src/App.jsx; } \
  || { command -v rg >/dev/null 2>&1 \
      && ! rg -q 'authenticated: Boolean\(operatorSession\.identityToken\)' frontend/src/api.js; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && ! grep -Eq 'authenticated: Boolean\(operatorSession\.identityToken\)' frontend/src/api.js; }; then
  printf 'Change Memory tenant boundary is incomplete: signed session is not forwarded.\n' >&2
  exit 1
fi

# Source-health reads can overlap after a monitor run, tab return, or source
# lifecycle change. Only the newest request may update freshness state; an
# older Firestore response must not roll the card back to stale data.
if { command -v rg >/dev/null 2>&1 \
      && { ! rg -q 'sourceHealthRequestRef' frontend/src/App.jsx \
        || ! rg -q 'sourceHealthRequestRef\.current !== requestId' frontend/src/App.jsx; }; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && { ! grep -Eq 'sourceHealthRequestRef' frontend/src/App.jsx \
        || ! grep -Eq 'sourceHealthRequestRef\.current !== requestId' frontend/src/App.jsx; }; }; then
  printf 'Source-health freshness guard is missing: an older overlapping read could overwrite newer state.\n' >&2
  exit 1
fi

printf 'Frontend literal ID contract: PASS\n'
