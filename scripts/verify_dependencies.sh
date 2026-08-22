#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to export the frozen backend lockfile" >&2
  exit 2
fi
if ! command -v pip-audit >/dev/null 2>&1; then
  echo "pip-audit is required; install it outside the application environment" >&2
  exit 2
fi

requirements_file="$(mktemp "${TMPDIR:-/tmp}/driftline-requirements.XXXXXX")"
trap 'rm -f "$requirements_file"' EXIT

# uv's requirements export includes the local editable project itself. The
# application has no runtime code dependency beyond the locked packages, so
# omit that editable line and audit the complete transitive resolution.
uv export \
  --locked \
  --no-dev \
  --format requirements-txt \
  --directory "$ROOT_DIR/backend" \
  | sed '/^-e \.[[:space:]]*$/d' > "$requirements_file"

pip-audit --requirement "$requirements_file" --progress-spinner off
