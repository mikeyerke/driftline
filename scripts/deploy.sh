#!/usr/bin/env bash
set -euo pipefail

readonly project_id="driftline-hackathon-2026"
readonly build_service_account="driftline-build@driftline-hackathon-2026.iam.gserviceaccount.com"

release_sha="$(git rev-parse --verify HEAD 2>/dev/null)"
if [[ ! "$release_sha" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'Refusing deployment: unable to resolve a full Git release SHA.\n' >&2
  exit 1
fi

# Cloud Build uploads the working tree, not a Git object. Refuse to let
# uncommitted or untracked bytes ship under a misleading release SHA.
if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  printf 'Refusing deployment: working tree is not clean; commit or remove local changes first.\n' >&2
  git status --short >&2
  exit 1
fi

active_project="$(gcloud config get-value project 2>/dev/null)"
if [[ "$active_project" != "$project_id" ]]; then
  printf 'Refusing deployment: active gcloud project is %s, expected %s.\n' \
    "$active_project" "$project_id" >&2
  exit 1
fi

exec gcloud builds submit \
  --project="$project_id" \
  --service-account="projects/$project_id/serviceAccounts/$build_service_account" \
  --substitutions="_RELEASE_SHA=$release_sha" \
  --config=cloudbuild.yaml \
  .
