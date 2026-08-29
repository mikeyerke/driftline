#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if ! grep -Fq 'Evidence readiness: 0 of 3 checks corroborated' frontend/src/components/EvidenceCouncil.jsx \
  || ! grep -Fq 'Next validation: quantify the segment split' frontend/src/components/DecisionRoom.jsx; then
  printf 'PM intake corroboration contract is missing from the decision brief.\n' >&2
  exit 1
fi

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

# Decision Twin retains prior outcomes as history after reopening. The learning
# receipt must select only an observation whose generation-bound ID matches the
# current case generation, or a generation-1 result can look current after a
# generation-2 approval.
if { command -v rg >/dev/null 2>&1 \
      && { ! rg -q 'outcome-g\$\{decisionCase\.generation\}-' frontend/src/components/LearningReceipt.jsx \
        || ! rg -q 'observation_id\.startsWith\(currentGenerationPrefix\)' frontend/src/components/LearningReceipt.jsx \
        || rg -q 'decisionCase\.outcomes\.at\(-1\)' frontend/src/components/LearningReceipt.jsx; }; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && { ! grep -Fq 'outcome-g${decisionCase.generation}-' frontend/src/components/LearningReceipt.jsx \
        || ! grep -Eq 'observation_id\.startsWith\(currentGenerationPrefix\)' frontend/src/components/LearningReceipt.jsx \
        || grep -Eq 'decisionCase\.outcomes\.at\(-1\)' frontend/src/components/LearningReceipt.jsx; }; }; then
  printf 'Decision Twin receipt is not generation-scoped: a prior outcome could appear current.\n' >&2
  exit 1
fi

if ! grep -Fq 'trigger_observation' frontend/src/components/LearningReceipt.jsx; then
  printf 'Decision Twin receipt omits the prior-generation outcome that triggered reopening.\n' >&2
  exit 1
fi

# Approval is a compare-and-set transition. The public Decision Twin must send
# the generation displayed in the room, or the API correctly rejects the
# action as an incomplete/stale approval instead of recording the decision.
if { command -v rg >/dev/null 2>&1 \
      && ! rg -q 'decisionCase\.council\.synthesis_hash,\s*decisionCase\.generation' frontend/src/components/DecisionRoom.jsx; } \
  || { ! command -v rg >/dev/null 2>&1 \
      && ! grep -Eq 'decisionCase\.council\.synthesis_hash,[[:space:]]*decisionCase\.generation' frontend/src/components/DecisionRoom.jsx; }; then
  printf 'Decision Twin approval contract is incomplete: current generation is not sent with the synthesis hash.\n' >&2
  exit 1
fi

# The public judge lane is a PM decision review, not a generic operations
# dashboard. Keep the first viewport anchored to the real decision and make
# the technical proof an intentional secondary disclosure.
check_frontend_literal() {
  local literal="$1"
  local file="$2"
  if command -v rg >/dev/null 2>&1; then
    rg -Fq -- "$literal" "$file"
  else
    grep -Fq -- "$literal" "$file"
  fi
}

if ! check_frontend_literal '"/api": localApiTarget' frontend/vite.config.js \
  || ! check_frontend_literal '"/health": localApiTarget' frontend/vite.config.js \
  || ! check_frontend_literal 'http://127.0.0.1:8080' frontend/vite.config.js \
  || ! check_frontend_literal 'You are offline. Nothing was changed; reconnect and try again.' frontend/src/api.js \
  || ! check_frontend_literal 'Driftline could not reach the service. Nothing was changed; check your connection and try again.' frontend/src/api.js \
  || ! check_frontend_literal 'start the backend on port 8080 and try again' frontend/src/api.js; then
  printf 'Clean-checkout development routing or actionable API recovery copy is missing.\n' >&2
  exit 1
fi

if ! node --check scripts/capture_decision_twin_candidate.mjs >/dev/null \
  || ! check_frontend_literal 'Input.dispatchMouseEvent' scripts/capture_decision_twin_candidate.mjs \
  || ! check_frontend_literal 'driftline-capture-pointer' scripts/capture_decision_twin_candidate.mjs \
  || ! check_frontend_literal 'pointerClicks' scripts/capture_decision_twin_candidate.mjs; then
  printf 'Continuous candidate capture lost its visible Chrome mouse-event proof contract.\n' >&2
  exit 1
fi

if ! node --check scripts/verify_custom_decision_browser.mjs >/dev/null \
  || ! check_frontend_literal 'CUSTOM_BROWSER_ALLOW_REMOTE' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'earlyMeasurementBlocked' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'conciseDistinctTitle' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'clearApprovalLabel' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'freshContextRestored' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'keyboardRadioRoving' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'namedInteractiveControls' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'minimumControlTargets' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'validAriaReferences' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'allEvidenceReviewed' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'artifactExtracted' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'pilotStarterVerified' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'CUSTOM_BROWSER_EXPECT_RELEASE_SHA' scripts/verify_custom_decision_browser.mjs; then
  printf 'Custom-decision browser gate lost its loopback, review-window, fresh-context, or accessibility contract.\n' >&2
  exit 1
fi

if ! check_frontend_literal 'role="radiogroup"' frontend/src/components/CounterfactualCompare.jsx \
  || ! check_frontend_literal 'ArrowRight' frontend/src/components/CounterfactualCompare.jsx \
  || ! check_frontend_literal 'tabIndex={activeId === option.option_id ? 0 : -1}' frontend/src/components/CounterfactualCompare.jsx \
  || ! check_frontend_literal '@media (forced-colors: active)' frontend/src/styles.css; then
  printf 'Decision option keyboard semantics or forced-colors focus support regressed.\n' >&2
  exit 1
fi

if ! check_frontend_literal 'Public demo · no sign-in needed' frontend/src/components/OperatorAccess.jsx \
  || check_frontend_literal 'Operator sign-in unavailable' frontend/src/components/OperatorAccess.jsx; then
  printf 'Public judge lane exposes a broken-sign-in message instead of intentional no-sign-in access.\n' >&2
  exit 1
fi

if ! check_frontend_literal 'Turn conflicting evidence into a decision your team can defend.' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Background decision monitor' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Decision memory' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Continuous PM operating loop' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Evidence harvest agents' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Stakeholder alignment agent' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Commitment &amp; execution agent' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Outcome autopilot + product memory' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Memory updated or decision reopened' backend/app/product_operating_loop.py \
  || ! check_frontend_literal 'decision_debt_history' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'The alignment meeting, evidence hunt, and post-launch guesswork.' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Bring a contested decision' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'What the PM leaves with' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Guardrail + rollback' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Open source-connected workspace flow' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Run the decision workflow' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'One approval starts the autonomous monitor · no second PM prompt' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'intakeSectionRef.current?.scrollIntoView' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'prefers-reduced-motion: reduce' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'tabIndex="-1" id="decision-intake-title"' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Human approver' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'setSelectedId(latest.council.recommendation)' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'This never generates a synthetic result.' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Named human approval' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'actionApproval.approver' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Attach the PM-observed outcome' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Measurement opens' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Driftline will reject early measurements at the API boundary.' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Evaluate real measurement' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'The action completed inside its guardrail' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Observed measurement' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal '/outcomes/measured' frontend/src/api.js \
  || ! check_frontend_literal 'Bounded internal action executed' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Guardrail rolled the internal action back' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'External writes' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'Use my decision' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Build my decision brief' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Continue to operating contract' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Back to decision context' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Download private pilot starter' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'not your decision text, identity, consent, or a validation claim' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal '/pilot-evidence-starter' frontend/src/api.js \
  || ! check_frontend_literal 'strict CSP does not need to allow temporary blob: URLs' frontend/src/api.js \
  || ! check_frontend_literal '/review' frontend/src/api.js \
  || ! check_frontend_literal 'Mark source reviewed' frontend/src/components/EvidenceCouncil.jsx \
  || ! check_frontend_literal 'capability-bound review receipt' frontend/src/components/EvidenceCouncil.jsx \
  || ! check_frontend_literal 'min from complete intake' frontend/src/components/EvidenceCouncil.jsx \
  || ! check_frontend_literal 'Decision intake progress' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'error && !intakeOpen' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Define the operating contract before approval' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Primary outcome metric' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Risk guardrail metric' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Action owner' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'measurement_contract' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'PM-provided · unverified' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Corroborating evidence pack' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'up to four redacted observations' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Observed on' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'evidence_inputs' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'separately cited signals' frontend/src/components/EvidenceCouncil.jsx \
  || ! check_frontend_literal 'independently observed' frontend/src/components/EvidenceCouncil.jsx \
  || ! check_frontend_literal 'Copy decision brief' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Operating contract:' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Risk stop:' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'days after approval' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Copy view-only link' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'The copied link is view-only.' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Read-only shared view.' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'decisionCase?.can_edit !== false' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'url.searchParams.set("decision", next.case_id)' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'getDecisionTwin(caseId)' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal '/api/decision-twin/intake' frontend/src/api.js \
  || ! check_frontend_literal '/api/decision-twin/intake/stream' frontend/src/api.js \
  || ! check_frontend_literal '/api/decision-twin/demo/pinned' frontend/src/api.js \
  || ! check_frontend_literal 'Extract locally' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Analyze with Gemini' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Driftline does not retain it.' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'artifactUploadAnalyzed' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'New decision' frontend/src/components/DecisionInbox.jsx \
  || ! check_frontend_literal 'details.decision-explanation' scripts/verify_custom_decision_browser.mjs \
  || ! check_frontend_literal 'This decision has a precedent.' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'window.location.assign(destination)' frontend/src/components/OperatorAccess.jsx \
  || ! check_frontend_literal 'decision-recommendation-strip' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'What Driftline prepared' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Prepared before human approval' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'independent perspectives' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Autonomous monitor active' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'No second PM action is required.' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'monitor_status === "fallback_required"' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'Run demo measurement fallback' frontend/src/components/LearningReceipt.jsx \
  || ! check_frontend_literal 'getDecisionTwin(decisionCase.case_id)' frontend/src/components/DecisionRoom.jsx \
  || ! check_frontend_literal 'ReleaseProof compact' frontend/src/App.jsx \
  || ! check_frontend_literal 'Trace refresh needed' frontend/src/components/ReleaseProof.jsx; then
  printf 'Decision Twin judge-surface contract is incomplete: the PM-first decision or honest proof disclosure is missing.\n' >&2
  exit 1
fi

if { command -v rg >/dev/null 2>&1 && rg -Fq -- 'Stale · rerun' frontend/src/components/ReleaseProof.jsx; } \
  || { ! command -v rg >/dev/null 2>&1 && grep -Fq -- 'Stale · rerun' frontend/src/components/ReleaseProof.jsx; }; then
  printf 'Release proof still exposes the stale operator label in the public lane.\n' >&2
  exit 1
fi

printf 'Frontend literal ID contract: PASS\n'
