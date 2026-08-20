#!/usr/bin/env bash
set -euo pipefail

readonly project_id="driftline-hackathon-2026"
readonly build_service_account="driftline-build@driftline-hackathon-2026.iam.gserviceaccount.com"

active_project="$(gcloud config get-value project 2>/dev/null)"
if [[ "$active_project" != "$project_id" ]]; then
  printf 'Refusing deployment: active gcloud project is %s, expected %s.\n' \
    "$active_project" "$project_id" >&2
  exit 1
fi

exec gcloud builds submit \
  --project="$project_id" \
  --service-account="projects/$project_id/serviceAccounts/$build_service_account" \
  --config=cloudbuild.yaml \
  .
