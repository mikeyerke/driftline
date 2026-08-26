#!/usr/bin/env bash
set -euo pipefail

readonly project_id="driftline-hackathon-2026"
readonly dataset_id="driftline_product"
readonly table_id="decision_twin_usage_daily"
readonly precedent_table_id="decision_twin_precedents"
readonly location="US"
readonly runtime_service_account="driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com"
readonly root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for command in gcloud bq; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "${command}" >&2
    exit 1
  fi
done

active_project="$(gcloud config get-value project 2>/dev/null)"
if [[ "${active_project}" != "${project_id}" ]]; then
  printf 'Refusing provisioning: active project is %s, expected %s.\n' \
    "${active_project}" "${project_id}" >&2
  exit 1
fi

gcloud services enable bigquery.googleapis.com --project="${project_id}"

if ! bq show --project_id="${project_id}" "${project_id}:${dataset_id}" >/dev/null 2>&1; then
  bq mk --dataset --project_id="${project_id}" --location="${location}" \
    --description="Aggregate-only Driftline Decision Twin analytics" \
    "${project_id}:${dataset_id}"
fi

sql="$(sed "s/{{PROJECT_ID}}/${project_id}/g" "${root_dir}/infra/decision_twin_bigquery.sql")"
bq query --project_id="${project_id}" --location="${location}" \
  --use_legacy_sql=false --maximum_bytes_billed=50000000 "${sql}"

# Query jobs require project authority; data access is restricted to the one
# aggregate-only table rather than the project or entire dataset.
gcloud projects add-iam-policy-binding "${project_id}" \
  --member="serviceAccount:${runtime_service_account}" \
  --role="roles/bigquery.jobUser" \
  --condition=None --quiet
bq add-iam-policy-binding \
  --member="serviceAccount:${runtime_service_account}" \
  --role="roles/bigquery.dataViewer" \
  "${project_id}:${dataset_id}.${table_id}"
bq add-iam-policy-binding \
  --member="serviceAccount:${runtime_service_account}" \
  --role="roles/bigquery.dataViewer" \
  "${project_id}:${dataset_id}.${precedent_table_id}"

bq show --project_id="${project_id}" \
  "${project_id}:${dataset_id}.${table_id}" >/dev/null
bq show --project_id="${project_id}" \
  "${project_id}:${dataset_id}.${precedent_table_id}" >/dev/null
printf 'Decision Twin BigQuery provisioning: PASS (%s.%s.%s + %s)\n' \
  "${project_id}" "${dataset_id}" "${table_id}" "${precedent_table_id}"
