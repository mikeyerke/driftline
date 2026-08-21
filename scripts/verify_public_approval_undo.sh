#!/usr/bin/env bash
# Prove the anonymous, packet-safe operational loop without credentials:
# live workflow -> deterministic approval -> private packet -> durable undo.
set -euo pipefail

readonly base_url="${DRIFTLINE_BASE_URL:-https://driftline-xvxczqg62a-uc.a.run.app}"
readonly max_attempts="${DRIFTLINE_APPROVAL_VERIFY_ATTEMPTS:-90}"
readonly source_id="competitor/pricing"

curl --fail --silent --show-error --max-time 20 "${base_url}/health" | jq -e \
  '.status == "ok" and .persistence == "firestore" and .async_jobs == true' >/dev/null

job="$(curl --fail --silent --show-error --max-time 20 \
  -X POST "${base_url}/api/jobs/demo" \
  -H 'content-type: application/json' \
  -d '{"query":"Inspect the selected allowlisted source change, verify the evidence, map the affected offerings and downstream artifacts, and stop at the human approval gate.","user_id":"public-approval-verifier","source_id":"competitor/pricing"}')"
job_id="$(printf '%s' "${job}" | jq -er '.job_id')"

result=''
for _ in $(seq 1 "${max_attempts}"); do
  result="$(curl --fail --silent --show-error --max-time 20 "${base_url}/api/jobs/${job_id}")"
  status="$(printf '%s' "${result}" | jq -r '.status // "unknown"')"
  case "${status}" in
    needs_approval|complete|failed) break ;;
  esac
  sleep 1
done

if [[ "${status}" != "needs_approval" ]]; then
  printf 'Approval/undo verification failed: expected needs_approval, got %s\n' "${status}" >&2
  printf '%s\n' "${result}" | jq '{job_id, status, workflow_id, model, execution_mode, error}' >&2
  exit 1
fi

printf '%s\n' "${result}" | jq -e '
  .status == "needs_approval" and
  .workflow.status == "needs_approval" and
  (.workflow.impacts | length) >= 4 and
  (.workflow.events | length) >= 5
' >/dev/null

workflow_id="$(printf '%s' "${result}" | jq -er '.workflow.workflow_id')"
option="$(printf '%s' "${result}" | jq -er '.workflow.agent_trace.decision_copilot.options[0]')"
decision="$(printf '%s' "${option}" | jq -er '.workflow_decision')"
option_id="$(printf '%s' "${option}" | jq -er '.option_id')"
artifact_decisions="$(printf '%s' "${option}" | jq -ec '.artifact_decisions')"
approve_body="$(jq -n \
  --arg decision "${decision}" \
  --arg option_id "${option_id}" \
  --argjson artifact_decisions "${artifact_decisions}" \
  '{approver:"Public approval verifier", approval_mode:"demo", decision:$decision, copilot_option_id:$option_id, artifact_decisions:$artifact_decisions}')"

approved="$(curl --fail --silent --show-error --max-time 30 \
  -X POST "${base_url}/api/workflows/${workflow_id}/approve" \
  -H 'content-type: application/json' \
  -d "${approve_body}")"
printf '%s\n' "${approved}" | jq -e '
  .status == "complete" and
  .action_record.storage_status == "persisted" and
  .action_record.operational_status == "active" and
  (.action_record.external_write // false) == false and
  (.action_record.external_systems_changed // false) == false
' >/dev/null

undone="$(curl --fail --silent --show-error --max-time 30 \
  -X POST "${base_url}/api/workflows/${workflow_id}/undo" \
  -H 'content-type: application/json' \
  -d '{"actor":"Public approval verifier","approval_mode":"demo"}')"
printf '%s\n' "${undone}" | jq -e '
  .status == "needs_approval" and
  .action_record.storage_status == "persisted" and
  .action_record.operational_status == "reversed" and
  (.action_record.external_write // false) == false and
  (.action_record.external_systems_changed // false) == false and
  ([.events[].outcome] | index("decision_reopened")) != null
' >/dev/null

printf '%s\n' "${undone}" | jq -r --arg job_id "${job_id}" \
  '"Public approval/undo verification: PASS",
   ("job=" + $job_id),
   ("workflow=" + .workflow_id),
   ("status=" + .status),
   ("packet=" + .action_record.storage_status),
   ("operational_output=" + .action_record.operational_status),
   ("external_write=" + ((.action_record.external_write // false) | tostring)),
   ("external_systems_changed=" + ((.action_record.external_systems_changed // false) | tostring))'
