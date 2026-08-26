#!/usr/bin/env bash
# Deploy one immutable candidate, refresh its release-bound trace proof, and
# verify the complete judge journey against that same serving SHA.
set -euo pipefail

readonly project_id="driftline-hackathon-2026"
readonly base_url="${DRIFTLINE_BASE_URL:-https://driftline-ops.web.app}"
readonly release_sha="$(git rev-parse --verify HEAD)"

# Fail before the first Google Cloud mutation unless the complete local suite
# passes and HEAD is the exact public main tip of mikeyerke/driftline.
./scripts/verify_release_candidate_local.sh --release-candidate

gcloud config set project "${project_id}"
./scripts/provision_decision_twin_bigquery.sh
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
