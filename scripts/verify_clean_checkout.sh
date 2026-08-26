#!/usr/bin/env bash
# Prove that the committed candidate is reproducible from tracked files alone.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

for command_name in git tar uv npm; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Clean-checkout verification missing required command: %s\n' "$command_name" >&2
    exit 1
  }
done

candidate_sha="$(git rev-parse --verify HEAD)"
[[ "$candidate_sha" =~ ^[0-9a-f]{40}$ ]] || {
  printf 'Clean-checkout verification could not resolve HEAD.\n' >&2
  exit 1
}

temp_root="${TMPDIR:-/tmp}"
clean_checkout="$(mktemp -d "$temp_root/driftline-clean-checkout.XXXXXX")"
case "$clean_checkout" in
  "$temp_root"/driftline-clean-checkout.*) ;;
  *)
    printf 'Clean-checkout verification received an unsafe temporary path.\n' >&2
    exit 1
    ;;
esac

cleanup() {
  rm -rf -- "$clean_checkout"
}
trap cleanup EXIT

git archive --format=tar "$candidate_sha" | tar -xf - -C "$clean_checkout"

(
  cd "$clean_checkout/backend"
  uv sync --locked --extra dev
  uv run ruff check \
    app tests \
    ../scripts/summarize_validation.py \
    ../scripts/summarize_real_pm_pilot.py \
    ../scripts/verify_third_party_licenses.py
  uv run pytest -q
  uv run python -m app.trace_eval --baseline trace_eval_baseline.json
)

(
  cd "$clean_checkout/frontend"
  npm ci
  npm run build
)

(
  cd "$clean_checkout"
  ./scripts/verify_frontend_contract.sh
  ./scripts/verify_submission_packet.sh
  for script in scripts/*.sh; do
    bash -n "$script"
  done
)

printf 'Clean-checkout verification: PASS (sha=%s)\n' "$candidate_sha"
