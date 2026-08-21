#!/usr/bin/env bash
# Read-only production verification for the isolated Driftline deployment.
# This script intentionally refuses to run against any other gcloud project.
set -euo pipefail

readonly expected_project="driftline-hackathon-2026"
readonly region="us-central1"
readonly service="driftline"
readonly public_url="https://driftline-xvxczqg62a-uc.a.run.app"
readonly scheduler_job="driftline-monitor"
readonly task_queue="driftline-jobs"
readonly uptime_id="driftline-health-Hmxqs16MUkY"
readonly dashboard_id="9f00a615-b74c-4567-aae9-211cd66e97fc"

actual_project="$(gcloud config get-value project 2>/dev/null)"
if [[ "${actual_project}" != "${expected_project}" ]]; then
  printf 'Refusing to verify: active gcloud project is %s (expected %s)\n' \
    "${actual_project:-<unset>}" "${expected_project}" >&2
  exit 2
fi

printf 'Project: %s\n' "${actual_project}"

read -r revision traffic < <(
  gcloud run services describe "${service}" \
    --project="${expected_project}" --region="${region}" \
    --format='value(status.latestReadyRevisionName,status.traffic[0].percent)'
)
[[ -n "${revision}" && "${traffic}" == "100" ]]
printf 'Cloud Run: %s (%s%% traffic)\n' "${revision}" "${traffic}"

health="$(curl --fail --silent --show-error --max-time 20 "${public_url}/health")"
printf '%s\n' "${health}" | jq -e \
  '.status == "ok" and .persistence == "firestore" and .async_jobs == true' >/dev/null
printf 'Health: %s\n' "${health}"

read -r scheduler_state scheduler_last_attempt < <(
  gcloud scheduler jobs describe "${scheduler_job}" \
    --project="${expected_project}" --location="${region}" \
    --format='value(state,lastAttemptTime)'
)
[[ "${scheduler_state}" == "ENABLED" ]]
printf 'Scheduler: %s (last attempt %s)\n' "${scheduler_state}" "${scheduler_last_attempt:-not reported}"

read -r queue_state max_concurrency max_attempts < <(
  gcloud tasks queues describe "${task_queue}" \
    --project="${expected_project}" --location="${region}" \
    --format='value(state,rateLimits.maxConcurrentDispatches,retryConfig.maxAttempts)'
)
[[ "${queue_state}" == "RUNNING" && "${max_concurrency}" == "1" && "${max_attempts}" == "3" ]]
printf 'Tasks: %s (concurrency %s, max attempts %s)\n' \
  "${queue_state}" "${max_concurrency}" "${max_attempts}"

uptime_path="$(gcloud monitoring uptime describe \
  "projects/${expected_project}/uptimeCheckConfigs/${uptime_id}" \
  --project="${expected_project}" --format='value(httpCheck.path)')"
[[ "${uptime_path}" == "/health" ]]
printf 'Uptime check: %s\n' "${uptime_id} (${uptime_path})"

policy_enabled="$(gcloud monitoring policies describe 17375876853888551854 \
  --project="${expected_project}" --format='value(enabled)')"
[[ "${policy_enabled}" == "True" ]]
printf 'Alert policy: enabled\n'

gcloud monitoring dashboards describe "${dashboard_id}" \
  --project="${expected_project}" --format='value(displayName)' | \
  grep -Fxq 'Driftline production control plane'
printf 'Dashboard: Driftline production control plane\n'

error_count="$(gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="driftline" AND severity>=ERROR' \
  --project="${expected_project}" --freshness=15m --limit=100 \
  --format='value(timestamp)' | sed '/^$/d' | wc -l | tr -d ' ')"
[[ "${error_count}" == "0" ]]
printf 'Recent Cloud Run errors: %s\n' "${error_count}"

printf 'Production verification: PASS\n'
