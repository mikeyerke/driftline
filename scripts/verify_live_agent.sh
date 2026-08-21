#!/usr/bin/env bash
# Run one bounded, identity-free production scan and verify that the deployed
# agent actually used ADK + Gemini, evidence, and the deterministic gate.
set -euo pipefail

readonly base_url="${DRIFTLINE_BASE_URL:-https://driftline-xvxczqg62a-uc.a.run.app}"
readonly max_attempts="${DRIFTLINE_LIVE_VERIFY_ATTEMPTS:-90}"
readonly max_runs="${DRIFTLINE_LIVE_VERIFY_RUNS:-3}"

health="$(curl --fail --silent --show-error --max-time 20 "${base_url}/health")"
printf '%s\n' "${health}" | jq -e \
  '.status == "ok" and .persistence == "firestore" and .async_jobs == true' >/dev/null

job="$(curl --fail --silent --show-error --max-time 20 \
  -X POST "${base_url}/api/jobs/demo" \
  -H 'content-type: application/json' \
  -d '{"query":"Inspect the selected allowlisted source change, verify the evidence, map the affected offerings and downstream artifacts, and stop at the human approval gate.","user_id":"public-verifier","source_id":"competitor/pricing"}')"
job_id="$(printf '%s' "${job}" | jq -er '.job_id')"

result=''
verified=false
for run in $(seq 1 "${max_runs}"); do
  if [[ "${run}" != "1" ]]; then
    # Anonymous evaluation may legitimately use the deterministic replay when
    # Vertex quota is temporarily unavailable. Give a fresh durable run a
    # chance to prove the live path without weakening the assertion below.
    sleep 2
    job="$(curl --fail --silent --show-error --max-time 20 \
      -X POST "${base_url}/api/jobs/demo" \
      -H 'content-type: application/json' \
      -d '{"query":"Inspect the selected allowlisted source change, verify the evidence, map the affected offerings and downstream artifacts, and stop at the human approval gate.","user_id":"public-verifier","source_id":"competitor/pricing"}')"
    job_id="$(printf '%s' "${job}" | jq -er '.job_id')"
  fi

  result=''
  for _ in $(seq 1 "${max_attempts}"); do
    result="$(curl --fail --silent --show-error --max-time 20 "${base_url}/api/jobs/${job_id}")"
    status="$(printf '%s' "${result}" | jq -r '.status // "unknown"')"
    case "${status}" in
      needs_approval|complete|failed) break ;;
    esac
    sleep 1
  done

  if printf '%s\n' "${result}" | jq -e '
    .status == "needs_approval" and
    .model == "gemini-3.5-flash" and
    .workflow.data_mode == "public_source" and
    .workflow.status == "needs_approval" and
    (.workflow.impacts | length) >= 4 and
    (.workflow.events | length) >= 5 and
    .workflow.agent_trace.execution_mode == "google_adk" and
    .workflow.agent_trace.model == "gemini-3.5-flash" and
    .workflow.agent_trace.structured_analysis.mode == "gemini_structured" and
    .workflow.agent_trace.decision_copilot.mode == "gemini_structured" and
    .workflow.agent_trace.decision_copilot.model == "gemini-3.5-flash" and
    .workflow.agent_trace.decision_copilot.policy_review.status == "pass" and
    (.workflow.agent_trace.decision_copilot.options | length) >= 2 and
    (.workflow.agent_trace.decision_copilot.options | length) <= 3 and
    ([.workflow.agent_trace.tool_calls[].name] | index("inspect_source_change")) != null and
    ([.workflow.agent_trace.tool_calls[].name] | index("get_workflow_state")) != null
  ' >/dev/null; then
    verified=true
    break
  fi

  fallback_mode="$(printf '%s' "${result}" | jq -r '.workflow.agent_trace.structured_analysis.mode // "unavailable"')"
  printf 'Live agent verification attempt %s/%s did not prove Gemini (%s); retrying.\n' \
    "${run}" "${max_runs}" "${fallback_mode}" >&2
done

if [[ "${verified}" != "true" ]]; then
  printf 'Live agent verification: FAIL after %s bounded runs\n' "${max_runs}" >&2
  exit 1
fi

printf '%s\n' "${result}" | jq -r '
  "Live agent verification: PASS",
  ("job=" + .job_id),
  ("workflow=" + .workflow.workflow_id),
  ("status=" + .status),
  ("data_mode=" + .workflow.data_mode),
  ("model=" + .model),
  ("execution_mode=" + .workflow.agent_trace.execution_mode),
  ("tools=" + ([.workflow.agent_trace.tool_calls[].name] | join(","))),
  ("artifacts=" + ((.workflow.impacts | length) | tostring)),
  ("audit_events=" + ((.workflow.events | length) | tostring)),
  ("decision_options=" + ((.workflow.agent_trace.decision_copilot.options | length) | tostring))
'
