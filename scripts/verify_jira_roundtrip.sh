#!/usr/bin/env bash
# Verify the real tenant-scoped Jira adapter against the isolated KAN project.
# This intentionally creates one marker issue, exercises idempotent reuse, and
# reverses only Driftline-owned state. It never deletes the Jira issue.
set -euo pipefail

if [[ "${DRIFTLINE_JIRA_LIVE_WRITE:-}" != "1" ]]; then
  echo "Refusing external Jira writes. Set DRIFTLINE_JIRA_LIVE_WRITE=1 explicitly." >&2
  exit 2
fi

readonly project="${DRIFTLINE_GCP_PROJECT:-driftline-hackathon-2026}"
readonly secret_name="${DRIFTLINE_JIRA_SECRET_NAME:-driftline-tenant-driftline-demo-jira}"
readonly base_url="${DRIFTLINE_JIRA_BASE_URL:-https://api.atlassian.com/ex/jira/7ed26020-ee58-470a-8fbb-3340925348ce/}"
readonly email="${DRIFTLINE_JIRA_EMAIL:-mikeyerke@gmail.com}"
readonly project_key="${DRIFTLINE_JIRA_PROJECT_KEY:-KAN}"
readonly action_id="${DRIFTLINE_JIRA_ACTION_ID:-internal-pilot-20260823-jira-roundtrip}"
readonly workflow_id="${DRIFTLINE_JIRA_WORKFLOW_ID:-pilot-jira-roundtrip-20260823}"
readonly evidence_hash="${DRIFTLINE_JIRA_EVIDENCE_HASH:-3b2df1ed8f635d1cc7ab425f675df0baa9bac941aaeddbfbca81ecada501d957}"

command -v gcloud >/dev/null
[[ -x "backend/.venv/bin/python" ]] || { echo "backend/.venv/bin/python is required" >&2; exit 1; }

token="$(gcloud secrets versions access latest --secret="${secret_name}" --project="${project}")"
export DRIFTLINE_JIRA_ENABLED=true
export DRIFTLINE_JIRA_BASE_URL="${base_url}"
export DRIFTLINE_JIRA_EMAIL="${email}"
export DRIFTLINE_JIRA_PROJECT_KEY="${project_key}"
export DRIFTLINE_JIRA_ISSUE_TYPE="Task"
export DRIFTLINE_JIRA_TOKEN="${token}"

PYTHONPATH=backend backend/.venv/bin/python - \
  "${workflow_id}" "${action_id}" "${evidence_hash}" <<'PY'
import json
import sys

from app.connectors import JiraConfig, JiraConnector

workflow_id, action_id, evidence_hash = sys.argv[1:]
connector = JiraConnector(JiraConfig.from_env())
kwargs = dict(
    workflow_id=workflow_id,
    action_id=action_id,
    source_name="Competitor pricing snapshot",
    evidence_hash=evidence_hash,
    artifact="Pricing battlecard",
    owner="Product Marketing",
    proposed=(
        "Review the competitor pricing change against current battlecard "
        "guidance; no customer-facing publication is authorized without corroboration."
    ),
)
first = connector.create_or_reuse_issue(**kwargs)
second = connector.create_or_reuse_issue(**kwargs)
issue_key = str(second.get("issue_key") or first.get("issue_key") or "")
reversed_result = connector.reverse_issue(issue_key, action_id) if issue_key else {}
print(json.dumps({
    "first_status": first.get("status"),
    "retry_status": second.get("status"),
    "retry_idempotent": second.get("idempotent"),
    "issue_key": issue_key,
    "reverse_status": reversed_result.get("status"),
}, sort_keys=True))
PY

unset DRIFTLINE_JIRA_TOKEN
