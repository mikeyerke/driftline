#!/usr/bin/env bash
set -euo pipefail

# Record one aggregate pilot measurement without ever accepting or printing a
# provider credential. The operator signer is read directly from the isolated
# Driftline project and used only to compute the request HMAC in memory.

PROJECT="${DRIFTLINE_PROJECT:-driftline-hackathon-2026}"
EXPECTED_PROJECT="driftline-hackathon-2026"
BASE_URL="${DRIFTLINE_BASE_URL:-https://driftline-xvxczqg62a-uc.a.run.app}"
TENANT="${DRIFTLINE_TENANT_ID:-driftline-demo}"
OPERATOR="${DRIFTLINE_OPERATOR:-}"
SOURCE_TYPE="${DRIFTLINE_SOURCE_TYPE:-pilot_log}"
COHORT_LABEL="${DRIFTLINE_COHORT_LABEL:-}"
CHANGES_OBSERVED="${DRIFTLINE_CHANGES_OBSERVED:-}"
BASELINE_MINUTES="${DRIFTLINE_BASELINE_MINUTES:-}"
DRIFTLINE_MINUTES="${DRIFTLINE_MINUTES:-}"
EVIDENCE_REF="${DRIFTLINE_EVIDENCE_REF:-}"
REVENUE_LIFT_USD="${DRIFTLINE_REVENUE_LIFT_USD:-}"
RETENTION_LIFT_PCT="${DRIFTLINE_RETENTION_LIFT_PCT:-}"
WILLINGNESS_TO_PAY_USD="${DRIFTLINE_WILLINGNESS_TO_PAY_USD:-}"
BASELINE_OWNER_READY_WITHIN_24H="${DRIFTLINE_BASELINE_OWNER_READY_WITHIN_24H:-}"
DRIFTLINE_OWNER_READY_WITHIN_24H="${DRIFTLINE_OWNER_READY_WITHIN_24H:-}"
BASELINE_ACTIONS_COMPLETED_WITHIN_7D="${DRIFTLINE_BASELINE_ACTIONS_COMPLETED_WITHIN_7D:-}"
DRIFTLINE_ACTIONS_COMPLETED_WITHIN_7D="${DRIFTLINE_ACTIONS_COMPLETED_WITHIN_7D:-}"
BASELINE_REVERSED_OR_REOPENED="${DRIFTLINE_BASELINE_REVERSED_OR_REOPENED:-}"
DRIFTLINE_REVERSED_OR_REOPENED="${DRIFTLINE_REVERSED_OR_REOPENED:-}"

if [[ "$(gcloud config get-value project 2>/dev/null)" != "${EXPECTED_PROJECT}" ]]; then
  echo "Refusing to target a non-Driftline gcloud project." >&2
  exit 1
fi
if [[ "${PROJECT}" != "${EXPECTED_PROJECT}" ]]; then
  echo "DRIFTLINE_PROJECT must remain ${EXPECTED_PROJECT}." >&2
  exit 1
fi
for required in OPERATOR COHORT_LABEL CHANGES_OBSERVED BASELINE_MINUTES DRIFTLINE_MINUTES EVIDENCE_REF; do
  if [[ -z "${!required}" ]]; then
    echo "Missing ${required}. See docs/PILOT_PACKET.md." >&2
    exit 2
  fi
done
case "${SOURCE_TYPE}" in
  customer_interview|pilot_log|win_loss|billing_record) ;;
  *) echo "DRIFTLINE_SOURCE_TYPE is not an allowed aggregate source type." >&2; exit 2 ;;
esac
if [[ ! "${EVIDENCE_REF}" =~ ^(https://|gs://|artifact://) ]]; then
  echo "DRIFTLINE_EVIDENCE_REF must be an https://, gs://, or artifact:// reference." >&2
  exit 2
fi

signer_secret="$(gcloud secrets versions access latest \
  --secret="driftline-tenant-operator-${TENANT}" --project="${PROJECT}")"

# The secret is deliberately passed through an environment variable to a
# short-lived Python process and is never echoed or serialized into the body.
approval_token="$(SECRET_VALUE="${signer_secret}" \
  HMAC_MESSAGE="outcome:${COHORT_LABEL}:${OPERATOR}" \
  python3 -c 'import hashlib, hmac, os; print(hmac.new(os.environ["SECRET_VALUE"].encode(), os.environ["HMAC_MESSAGE"].encode(), hashlib.sha256).hexdigest())')"
unset signer_secret

json_body="$(OPERATOR="${OPERATOR}" TENANT="${TENANT}" SOURCE_TYPE="${SOURCE_TYPE}" \
  COHORT_LABEL="${COHORT_LABEL}" CHANGES_OBSERVED="${CHANGES_OBSERVED}" \
  BASELINE_MINUTES="${BASELINE_MINUTES}" DRIFTLINE_MINUTES="${DRIFTLINE_MINUTES}" \
  EVIDENCE_REF="${EVIDENCE_REF}" REVENUE_LIFT_USD="${REVENUE_LIFT_USD}" \
  RETENTION_LIFT_PCT="${RETENTION_LIFT_PCT}" WILLINGNESS_TO_PAY_USD="${WILLINGNESS_TO_PAY_USD}" \
  BASELINE_OWNER_READY_WITHIN_24H="${BASELINE_OWNER_READY_WITHIN_24H}" DRIFTLINE_OWNER_READY_WITHIN_24H="${DRIFTLINE_OWNER_READY_WITHIN_24H}" \
  BASELINE_ACTIONS_COMPLETED_WITHIN_7D="${BASELINE_ACTIONS_COMPLETED_WITHIN_7D}" DRIFTLINE_ACTIONS_COMPLETED_WITHIN_7D="${DRIFTLINE_ACTIONS_COMPLETED_WITHIN_7D}" \
  BASELINE_REVERSED_OR_REOPENED="${BASELINE_REVERSED_OR_REOPENED}" DRIFTLINE_REVERSED_OR_REOPENED="${DRIFTLINE_REVERSED_OR_REOPENED}" \
  python3 -c 'import json, os
def optional_number(name):
    value=os.environ.get(name, "")
    return float(value) if value else None
payload={"operator":os.environ["OPERATOR"],"tenant_id":os.environ["TENANT"],"source_type":os.environ["SOURCE_TYPE"],"cohort_label":os.environ["COHORT_LABEL"],"changes_observed":int(os.environ["CHANGES_OBSERVED"]),"baseline_minutes":float(os.environ["BASELINE_MINUTES"]),"driftline_minutes":float(os.environ["DRIFTLINE_MINUTES"]),"evidence_ref":os.environ["EVIDENCE_REF"]}
for key, env_name in (("revenue_lift_usd","REVENUE_LIFT_USD"),("retention_lift_pct","RETENTION_LIFT_PCT"),("willingness_to_pay_usd","WILLINGNESS_TO_PAY_USD")):
    value=optional_number(env_name)
    if value is not None: payload[key]=value
for key, env_name in (("baseline_owner_ready_within_24h","BASELINE_OWNER_READY_WITHIN_24H"),("driftline_owner_ready_within_24h","DRIFTLINE_OWNER_READY_WITHIN_24H"),("baseline_actions_completed_within_7d","BASELINE_ACTIONS_COMPLETED_WITHIN_7D"),("driftline_actions_completed_within_7d","DRIFTLINE_ACTIONS_COMPLETED_WITHIN_7D"),("baseline_reversed_or_reopened","BASELINE_REVERSED_OR_REOPENED"),("driftline_reversed_or_reopened","DRIFTLINE_REVERSED_OR_REOPENED")):
    value=optional_number(env_name)
    if value is not None: payload[key]=int(value)
print(json.dumps(payload))')"

curl --fail-with-body --silent --show-error --max-time 30 \
  -H "Content-Type: application/json" \
  -H "X-Driftline-Approval: ${approval_token}" \
  -X POST "${BASE_URL}/api/ops/outcomes" \
  --data-binary "${json_body}"
printf '\nRecorded as operator_reported_unverified; reconcile the evidence reference before making a customer claim.\n'
