#!/usr/bin/env bash
set -euo pipefail

readonly base_url="${DRIFTLINE_BASE_URL:-https://driftline-ops.web.app}"

case_json="$(curl --fail --silent --show-error --max-time 180 \
  -X POST "${base_url}/api/decision-twin/demo")"
case_id="$(printf '%s' "${case_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); assert p["status"]=="needs_approval"; assert p["council"]["mode"]=="google_adk"; assert any("BigQuery aggregate" in n["source_label"] for n in p["evidence_nodes"]); print(p["case_id"])')"
synthesis_hash="$(printf '%s' "${case_json}" | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["council"]["synthesis_hash"])')"
recommendation="$(printf '%s' "${case_json}" | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["council"]["recommendation"])')"

approval_body="$(python3 -c \
  'import json,sys; print(json.dumps({"approver":"Release Verifier","option_id":sys.argv[1],"expected_synthesis_hash":sys.argv[2]}))' \
  "${recommendation}" "${synthesis_hash}")"
approved_json="$(curl --fail --silent --show-error --max-time 30 \
  -H 'Content-Type: application/json' -X POST \
  --data "${approval_body}" \
  "${base_url}/api/decision-twin/${case_id}/approve")"
printf '%s' "${approved_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); assert p["status"]=="experiment_active"; assert p["experiment_plan"]["reversible"] is True'

reopened_json="$(curl --fail --silent --show-error --max-time 30 \
  -H 'Content-Type: application/json' -X POST \
  --data '{"expected_generation":1,"scenario":"guardrail_breach"}' \
  "${base_url}/api/decision-twin/${case_id}/outcomes/demo")"
printf '%s' "${reopened_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); assert p["status"]=="reopened"; assert p["generation"]==2; assert p["decision_history"][0]["generation"]==1; assert p["outcomes"][-1]["evaluation"]["verdict"]=="invalidated"'

evaluation_json="$(curl --fail --silent --show-error --max-time 30 \
  "${base_url}/api/decision-twin/${case_id}/evaluation")"
printf '%s' "${evaluation_json}" | python3 -c \
  'import json,sys; p=json.load(sys.stdin); assert p["gate_status"]=="pass"; assert p["overall_score"]==1.0'

printf 'Decision Twin live verification: PASS (case=%s, generation=2, council=google_adk, analytics=bigquery)\n' \
  "${case_id}"
