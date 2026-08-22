#!/usr/bin/env bash
# Prove the anonymous, packet-safe operational loop without credentials:
# live workflow -> deterministic approval -> owner closure -> private packet -> durable undo.
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
  (.workflow.events | length) >= 5 and
  .workflow.agent_trace.execution_mode == "google_adk" and
  .workflow.agent_trace.model == "gemini-3.5-flash" and
  .workflow.agent_trace.structured_analysis.mode == "gemini_structured" and
  .workflow.agent_trace.structured_analysis.model == "gemini-3.5-flash" and
  .workflow.agent_trace.decision_copilot.mode == "gemini_structured" and
  .workflow.agent_trace.decision_copilot.model == "gemini-3.5-flash" and
  .workflow.agent_trace.decision_copilot.policy_review.status == "pass" and
  (.workflow.agent_trace.decision_copilot.options | length) >= 2 and
  (.workflow.agent_trace.decision_copilot.options | length) <= 3 and
  (.workflow.evidence.evidence_hash) as $evidence_hash |
  all(.workflow.impacts[]; .evidence_hash == $evidence_hash) and
  all(.workflow.agent_trace.decision_copilot.options[];
    .requires_human_approval == true and
    (.citations | length) >= 1 and
    all(.citations[]; .evidence_hash == $evidence_hash)
  )
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
  .action_record.reversible == true and
  (.action_record.packet_count // 0) >= 4 and
  (.action_record.action_item_count // 0) >= 4 and
  (.action_record.evidence_hash | test("^[0-9a-f]{64}$")) and
  (.action_record.external_write // false) == false and
  (.action_record.external_systems_changed // false) == false
' >/dev/null

item_id="$(printf '%s' "${approved}" | jq -er '.action_items[0].item_id')"
actor='Public approval verifier'
claimed="$(curl --fail --silent --show-error --max-time 30 \
  -X POST "${base_url}/api/workflows/${workflow_id}/actions/${item_id}/claim" \
  -H 'content-type: application/json' \
  -d "$(jq -nc --arg actor "${actor}" '{actor:$actor, approval_mode:"demo"}')")"
printf '%s\n' "${claimed}" | jq -e --arg item_id "${item_id}" --arg actor "${actor}" '
  any(.action_items[]; .item_id == $item_id and .status == "claimed" and .claimed_by == $actor) and
  ([.events[].outcome] | index(($item_id + ":claimed"))) != null
' >/dev/null

completed="$(curl --fail --silent --show-error --max-time 30 \
  -X POST "${base_url}/api/workflows/${workflow_id}/actions/${item_id}/complete" \
  -H 'content-type: application/json' \
  -d "$(jq -nc --arg actor "${actor}" '{actor:$actor, approval_mode:"demo"}')")"
printf '%s\n' "${completed}" | jq -e --arg item_id "${item_id}" --arg actor "${actor}" '
  any(.action_items[]; .item_id == $item_id and .status == "completed" and .completed_by == $actor and (.completed_at | type == "string")) and
  ([.events[].outcome] | index(($item_id + ":completed"))) != null
' >/dev/null

value_proof="$(curl --fail --silent --show-error --max-time 20 "${base_url}/api/ops/value-proof")"
printf '%s\n' "${value_proof}" | jq -e '
  (.observed.action_items_completed_historically // 0) >= 1 and
  (.observed.owner_action_cycle_seconds.sample_count // 0) >= 1 and
  (.observed.action_item_completion_rate_historically // 0) > 0
' >/dev/null

undone="$(curl --fail --silent --show-error --max-time 30 \
  -X POST "${base_url}/api/workflows/${workflow_id}/undo" \
  -H 'content-type: application/json' \
  -d '{"actor":"Public approval verifier","approval_mode":"demo"}')"
printf '%s\n' "${undone}" | jq -e --arg item_id "${item_id}" '
  .status == "needs_approval" and
  .action_record.storage_status == "persisted" and
  .action_record.operational_status == "reversed" and
  .action_record.reversible == true and
  (.action_record.packet_count // 0) >= 4 and
  (.action_record.evidence_hash | test("^[0-9a-f]{64}$")) and
  (.action_record.external_write // false) == false and
  (.action_record.external_systems_changed // false) == false and
  ([.events[].outcome] | index("decision_reopened")) != null and
  any(.action_items[]; .item_id == $item_id and .status == "reversed" and (.completed_at | type == "string"))
' >/dev/null

printf '%s\n' "${undone}" | jq -r --arg job_id "${job_id}" --arg item_id "${item_id}" \
  '"Public approval/undo verification: PASS",
   ("job=" + $job_id),
   ("workflow=" + .workflow_id),
   ("status=" + .status),
   ("packet=" + .action_record.storage_status),
   ("operational_output=" + .action_record.operational_status),
   ("owner_action=" + $item_id + " completed_then_reversed"),
   ("external_write=" + ((.action_record.external_write // false) | tostring)),
   ("external_systems_changed=" + ((.action_record.external_systems_changed // false) | tostring))'
