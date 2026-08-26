#!/usr/bin/env bash
set -euo pipefail

readonly base_url="${DRIFTLINE_BASE_URL:-https://driftline-ops.web.app}"
readonly expected_sha="${DRIFTLINE_EXPECTED_SHA:-$(git rev-parse HEAD)}"

health_json="$(curl --fail --silent --show-error --max-time 30 \
  "${base_url}/health")"
printf '%s' "${health_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); expected=sys.argv[1]; assert p["release_sha"]==expected, (p["release_sha"], expected)' \
  "${expected_sha}"

case_json="$(curl --fail --silent --show-error --max-time 180 \
  -X POST "${base_url}/api/decision-twin/demo")"
case_id="$(printf '%s' "${case_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); assert p["status"]=="needs_approval"; assert p["council"]["mode"]=="google_adk"; assert any(e["event_id"]=="bigquery-aggregate-attached" for e in p["events"]); assert any(e["event_id"]=="decision-memory-attached" for e in p["events"]); assert any("BigQuery vector decision memory" in item["source_label"] for item in p["precedents"]); assert any(e["event_id"]=="product-council-complete" and e.get("execution_mode")=="google_adk" for e in p["events"]); print(p["case_id"])')"
synthesis_hash="$(printf '%s' "${case_json}" | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["council"]["synthesis_hash"])')"
recommendation="$(printf '%s' "${case_json}" | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["council"]["recommendation"])')"

approval_body="$(python3 -c \
  'import json,sys; print(json.dumps({"approver":"Release Verifier","option_id":sys.argv[1],"expected_synthesis_hash":sys.argv[2],"expected_generation":1}))' \
  "${recommendation}" "${synthesis_hash}")"
approved_json="$(curl --fail --silent --show-error --max-time 30 \
  -H 'Content-Type: application/json' -X POST \
  --data "${approval_body}" \
  "${base_url}/api/decision-twin/${case_id}/approve")"
printf '%s' "${approved_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); assert p["status"]=="experiment_active"; assert p["experiment_plan"]["reversible"] is True'

reopened_json=""
for _attempt in $(seq 1 30); do
  reopened_json="$(curl --fail --silent --show-error --max-time 30 \
    "${base_url}/api/decision-twin/${case_id}")"
  if printf '%s' "${reopened_json}" | python3 -c \
    'import json,sys; raise SystemExit(0 if json.load(sys.stdin)["status"]=="reopened" else 1)'; then
    break
  fi
  sleep 1
done
printf '%s' "${reopened_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); h=p["decision_history"][0]; assert p["status"]=="reopened"; assert p["generation"]==2; assert h["generation"]==1; assert h["approval"]["approved_at"]; assert h["experiment_plan"]["reversible"] is True; assert h["trigger_observation"]["evaluation"]["verdict"]=="invalidated"; assert p["outcomes"][-1]["evaluation"]["verdict"]=="invalidated"; assert any(e.get("action")=="autonomous_experiment_monitor" for e in p["events"])'

evaluation_json="$(curl --fail --silent --show-error --max-time 30 \
  "${base_url}/api/decision-twin/${case_id}/evaluation")"
printf '%s' "${evaluation_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); assert p["gate_status"]=="pass"; assert p["overall_score"]==1.0'

printf 'Decision Twin live verification: PASS (sha=%s, case=%s, generation=2, council=google_adk, analytics=bigquery, memory=bigquery_vector, monitor=cloud_tasks)\n' \
  "${expected_sha}" "${case_id}"
