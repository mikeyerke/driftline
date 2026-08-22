#!/usr/bin/env bash
# Read-only production verification for the isolated Driftline deployment.
# This script intentionally refuses to run against any other gcloud project.
set -euo pipefail

readonly expected_project="driftline-hackathon-2026"
readonly expected_project_number="724959673622"
readonly region="us-central1"
readonly service="driftline"
readonly public_url="https://driftline-xvxczqg62a-uc.a.run.app"
readonly scheduler_job="driftline-monitor"
readonly task_queue="driftline-jobs"
readonly uptime_id="driftline-health-Hmxqs16MUkY"
readonly dashboard_id="9f00a615-b74c-4567-aae9-211cd66e97fc"
readonly runtime_service_account="driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com"

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

artifact_cleanup_dry_run="$(
  gcloud artifacts repositories describe driftline \
    --project="${expected_project}" --location="${region}" \
    --format='value(cleanupPolicyDryRun)'
)"
[[ "${artifact_cleanup_dry_run}" == "False" ]]
printf 'Artifact Registry: cleanup policy active (dry-run disabled)\n'

health="$(curl --fail --silent --show-error --max-time 20 "${public_url}/health")"
printf '%s\n' "${health}" | jq -e \
  '.status == "ok" and .persistence == "firestore" and .async_jobs == true' >/dev/null
printf '%s\n' "${health}" | jq -e \
  '(.release_sha | type == "string" and test("^[0-9a-f]{40}$")) and
   (.build_id | type == "string" and length > 0)' >/dev/null
printf 'Health: %s\n' "${health}"

health_headers="$(curl --fail --silent --show-error --max-time 20 --dump-header - --output /dev/null "${public_url}/health")"
grep -Fqi 'cache-control: no-store' <<<"${health_headers}"
grep -Fqi 'permissions-policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()' <<<"${health_headers}"
printf 'Security headers: health no-store + capability deny-list\n'

auth_config="$(curl --fail --silent --show-error --max-time 20 "${public_url}/api/auth/config")"
printf '%s\n' "${auth_config}" | jq -e --arg prefix "${expected_project_number}-" \
  '.enabled == true and .mode == "google_oidc" and (.client_id | startswith($prefix)) and .credential_values_exposed == false' >/dev/null
printf 'Google operator auth: isolated project client, credential values not exposed\n'

api_headers="$(curl --fail --silent --show-error --max-time 20 --dump-header - --output /dev/null "${public_url}/api/auth/config")"
grep -Fqi 'cache-control: no-store' <<<"${api_headers}"
grep -Fqi 'permissions-policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()' <<<"${api_headers}"
printf 'Security headers: API no-store + capability deny-list\n'

# The shared runtime must not be a project-wide Secret Manager reader or
# version writer. Connector values are accessed only through the derived
# per-tenant service identity and its exact secret IAM bindings. Keep this
# check here so a future infrastructure change cannot silently widen the
# hosted credential boundary again.
runtime_secret_roles="$(
  gcloud projects get-iam-policy "${expected_project}" --format=json |
    jq -r --arg member "serviceAccount:${runtime_service_account}" '
      [.bindings[]
       | select((.members // []) | index($member))
       | .role
       | select(startswith("roles/secretmanager."))]
      | join(",")'
)"
[[ -z "${runtime_secret_roles}" ]]
printf 'Runtime IAM: no project-level Secret Manager access\n'

ops_summary="$(curl --fail --silent --show-error --max-time 20 "${public_url}/api/ops/summary")"
printf '%s\n' "${ops_summary}" | jq -e \
  '.model == "gemini-3.5-flash" and
   .persistence == "firestore" and
   .async_jobs == true and
   ((.source_health // []) | length) >= 5 and
   .approval_security.public_demo_packet_only == true and
   .approval_security.google_oidc_operator_enabled == true and
   .approval_security.external_writes_require_signed == true and
   .approval_security.credential_model.tenant_bound == true and
   .approval_security.credential_model.legacy_global_fallback == false and
   .approval_security.tenant_auth.configured == true and
   .approval_security.tenant_auth.durable_memberships == true and
   .approval_security.tenant_auth.static_operator_allowlist == false and
   .crm.salesforce.external_write == false' >/dev/null
printf 'Agent configuration: Gemini 3.5 Flash, Firestore, five bounded source monitors, OIDC tenant boundary\n'

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
