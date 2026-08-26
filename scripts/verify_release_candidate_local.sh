#!/usr/bin/env bash
# Prove a Driftline release candidate before any Google Cloud mutation occurs.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:---release-candidate}"
cd "$ROOT_DIR"

case "$MODE" in
  --local-checks | --release-candidate) ;;
  *)
    printf 'Usage: %s [--local-checks|--release-candidate]\n' "$0" >&2
    exit 2
    ;;
esac

for command_name in git rg uv npm python3; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Release preflight missing required command: %s\n' "$command_name" >&2
    exit 1
  }
done

release_sha="$(git rev-parse --verify HEAD)"
[[ "$release_sha" =~ ^[0-9a-f]{40}$ ]] || {
  printf 'Release preflight could not resolve a full candidate commit.\n' >&2
  exit 1
}

initial_tree_state="clean"
if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  initial_tree_state="dirty"
fi

if [[ "$MODE" == "--release-candidate" ]]; then
  if [[ "$initial_tree_state" == "dirty" ]]; then
    printf 'Release preflight refuses a dirty candidate.\n' >&2
    git status --short >&2
    exit 1
  fi

  readonly release_remote="${DRIFTLINE_RELEASE_REMOTE:-origin}"
  readonly release_ref="${DRIFTLINE_RELEASE_REF:-main}"
  remote_url="$(git remote get-url "$release_remote")"
  if [[ ! "$remote_url" =~ github\.com[:/]mikeyerke/driftline(\.git)?$ ]]; then
    printf 'Release preflight refuses remote %s (%s); expected mikeyerke/driftline.\n' \
      "$release_remote" "$remote_url" >&2
    exit 1
  fi

  remote_sha="$(git ls-remote --exit-code "$release_remote" "refs/heads/$release_ref" | awk 'NR == 1 {print $1}')"
  if [[ ! "$remote_sha" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'Release preflight could not resolve %s/%s.\n' \
      "$release_remote" "$release_ref" >&2
    exit 1
  fi
  if [[ "$release_sha" != "$remote_sha" ]]; then
    printf 'Release preflight refuses custody mismatch: local HEAD %s; %s/%s %s.\n' \
      "$release_sha" "$release_remote" "$release_ref" "$remote_sha" >&2
    exit 1
  fi
  printf 'Release custody: exact public %s/%s commit %s\n' \
    "$release_remote" "$release_ref" "$release_sha"
fi

(
  cd backend
  uv sync --locked --extra dev
  uv run ruff check app tests ../scripts/summarize_validation.py ../scripts/summarize_real_pm_pilot.py
  uv run pytest -q
  uv run python -m app.trace_eval --baseline trace_eval_baseline.json
)

(
  cd frontend
  npm ci
  npm run build
)

./scripts/verify_dependencies.sh
./scripts/verify_frontend_contract.sh
./scripts/verify_submission_packet.sh

for script in scripts/*.sh; do
  bash -n "$script"
done
git diff --check

if [[ "$MODE" == "--release-candidate" && -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  printf 'Release preflight checks changed the candidate tree; refusing release.\n' >&2
  git status --short >&2
  exit 1
fi

if [[ "$MODE" == "--release-candidate" ]]; then
  printf 'Exact release-candidate preflight: PASS (sha=%s, public_ref=%s/%s)\n' \
    "$release_sha" "$release_remote" "$release_ref"
else
  printf 'Local working-tree checks: PASS (base_head=%s, initial_tree=%s)\n' \
    "$release_sha" "$initial_tree_state"
fi
