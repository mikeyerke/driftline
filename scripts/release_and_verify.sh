#!/usr/bin/env bash
# Deploy one immutable candidate, refresh its release-bound trace proof, and
# verify the complete judge journey against that same serving SHA.
set -euo pipefail

readonly project_id="driftline-hackathon-2026"
readonly base_url="${DRIFTLINE_BASE_URL:-https://driftline-ops.web.app}"
readonly release_sha="$(git rev-parse --verify HEAD)"

if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  printf 'Refusing release: working tree is not clean.\n' >&2
  git status --short >&2
  exit 1
fi

gcloud config set project "${project_id}"
./scripts/deploy.sh

# This live ADK run writes the redacted, append-only trace evaluation that the
# judge-facing release proof binds to the serving SHA. It must precede the
# read-only production verifier or the UI will honestly report a stale trace.
DRIFTLINE_BASE_URL="${base_url}" \
  DRIFTLINE_EXPECTED_SHA="${release_sha}" \
  ./scripts/verify_live_agent.sh

DRIFTLINE_BASE_URL="${base_url}" \
  DRIFTLINE_EXPECTED_SHA="${release_sha}" \
  ./scripts/verify_decision_twin.sh

DRIFTLINE_BASE_URL="${base_url}" \
  DRIFTLINE_EXPECTED_SHA="${release_sha}" \
  ./scripts/verify_production.sh

printf 'Winning release verification: PASS (sha=%s)\n' "${release_sha}"
