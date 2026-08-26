#!/usr/bin/env bash
# Deploy one immutable candidate, refresh its release-bound trace proof, and
# verify the complete judge journey against that same serving SHA.
set -euo pipefail

readonly project_id="driftline-hackathon-2026"
readonly base_url="${DRIFTLINE_BASE_URL:-https://driftline-ops.web.app}"
readonly release_sha="$(git rev-parse --verify HEAD)"
readonly release_identity_out="${DRIFTLINE_RELEASE_IDENTITY_OUT:-/tmp/driftline-release-identity-${release_sha}.json}"
readonly manifest_seed_out="${DRIFTLINE_FINAL_DEMO_MANIFEST_SEED_OUT:-/tmp/driftline-final-demo-manifest-${release_sha}.seed.json}"
readonly repository_root="$(git rev-parse --show-toplevel)"

[[ "${base_url}" == "https://driftline-ops.web.app" ]] || {
  printf 'Release-and-capture custody requires the canonical Firebase judge URL.\n' >&2
  exit 2
}

for output_path in "${release_identity_out}" "${manifest_seed_out}"; do
  [[ "${output_path}" == /* ]] || {
    printf 'Release evidence output paths must be absolute.\n' >&2
    exit 2
  }
  [[ ! -e "${output_path}" ]] || {
    printf 'Release evidence output already exists: %s\n' "${output_path}" >&2
    exit 2
  }
  case "${output_path}" in
    "${repository_root}"|"${repository_root}"/*)
      printf 'Release evidence output must be outside the repository: %s\n' "${output_path}" >&2
      exit 2
      ;;
  esac
  [[ -d "$(dirname "${output_path}")" ]] || {
    printf 'Release evidence output parent does not exist: %s\n' "${output_path}" >&2
    exit 2
  }
done

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
  DRIFTLINE_RELEASE_IDENTITY_OUT="${release_identity_out}" \
  ./scripts/verify_production.sh

python3 scripts/prepare_final_demo_manifest.py \
  --release-identity "${release_identity_out}" \
  --output "${manifest_seed_out}"

printf 'Winning release verification: PASS (sha=%s, identity=%s, manifest_seed=%s)\n' \
  "${release_sha}" "${release_identity_out}" "${manifest_seed_out}"
