#!/usr/bin/env bash
# Deterministic fail-closed quality gate for the bounded Driftline trace contract.
set -euo pipefail

readonly root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root_dir}/backend"

if [[ -x "${root_dir}/backend/.venv/bin/python" ]]; then
  exec "${root_dir}/backend/.venv/bin/python" -m app.trace_eval
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run --locked python -m app.trace_eval
fi
printf 'A backend Python environment or uv is required for the trace-eval gate.\n' >&2
exit 2
