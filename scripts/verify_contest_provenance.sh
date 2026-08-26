#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

EXPECTED_ROOT="b7a45f1b456f8e5e8cb630574b6e829bd4f575c4"
EXPECTED_SOURCE_ARCHIVE_SHA256="9026ee2eccc94fd925ec00a54228c8b858442baaf8ac695e2ca56f54bbce37b0"
CONTEST_START="2026-08-03T16:00:00+00:00"
CONTEST_END="2026-09-01T00:00:00+00:00"

verify_external=false
source_archive=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --external)
      verify_external=true
      shift
      ;;
    --source-archive)
      [[ $# -ge 2 ]] || {
        printf 'Contest provenance failed: --source-archive requires a path.\n' >&2
        exit 1
      }
      source_archive="$2"
      shift 2
      ;;
    *)
      printf 'Contest provenance failed: unknown argument %s.\n' "$1" >&2
      exit 1
      ;;
  esac
done

roots="$(git rev-list --max-parents=0 HEAD)"
[[ "$roots" == "$EXPECTED_ROOT" ]] || {
  printf 'Contest provenance failed: unexpected Git root(s): %s\n' "$roots" >&2
  exit 1
}

root_time="$(git show -s --format=%cI "$EXPECTED_ROOT")"
python3 - "$root_time" "$CONTEST_START" "$CONTEST_END" <<'PY'
from datetime import datetime
import sys

root = datetime.fromisoformat(sys.argv[1])
start = datetime.fromisoformat(sys.argv[2])
end = datetime.fromisoformat(sys.argv[3])
if not start <= root <= end:
    raise SystemExit(f"Contest provenance failed: root commit is outside the contest: {root.isoformat()}")
PY

printf 'Local contest provenance passed: root %s at %s.\n' "$EXPECTED_ROOT" "$root_time"

if [[ -n "$source_archive" ]]; then
  [[ -f "$source_archive" ]] || {
    printf 'Contest provenance failed: source archive not found: %s\n' "$source_archive" >&2
    exit 1
  }
  python3 - "$source_archive" "$EXPECTED_SOURCE_ARCHIVE_SHA256" \
    "$CONTEST_START" "$CONTEST_END" <<'PY'
from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePosixPath
import sys
import tarfile

archive = Path(sys.argv[1])
expected_hash = sys.argv[2]
contest_start = datetime.fromisoformat(sys.argv[3])
contest_end = datetime.fromisoformat(sys.argv[4])

actual_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual_hash != expected_hash:
    raise SystemExit(
        "Contest provenance failed: source archive hash mismatch: "
        f"{actual_hash}"
    )

required_members = {
    "driftline/backend/app/api.py",
    "driftline/backend/app/agent.py",
    "driftline/backend/app/adk_runtime.py",
    "driftline/backend/app/models.py",
    "driftline/backend/app/persistence.py",
    "driftline/backend/app/workflow.py",
    "driftline/frontend/src/App.jsx",
    "driftline/frontend/src/styles.css",
    "driftline/cloudbuild.yaml",
    "driftline/docs/concepts/change-operations-approved.png",
    "driftline/docs/concepts/change-operations-primary.png",
    "driftline/submission/DEVPOST.md",
}

with tarfile.open(archive, "r:gz") as package:
    files = [member for member in package.getmembers() if member.isfile()]
    names = {member.name for member in files}
    missing = sorted(required_members - names)
    if missing:
        raise SystemExit(
            "Contest provenance failed: source archive is missing expected "
            f"members: {', '.join(missing)}"
        )
    if len(files) != 50:
        raise SystemExit(
            "Contest provenance failed: source archive contains "
            f"{len(files)} regular files, expected 50"
        )
    for member in files:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(
                "Contest provenance failed: unsafe source archive member: "
                f"{member.name}"
            )
        timestamp = datetime.fromtimestamp(member.mtime, timezone.utc)
        if not contest_start <= timestamp <= contest_end:
            raise SystemExit(
                "Contest provenance failed: source archive member is outside "
                f"the contest window: {member.name}@{timestamp.isoformat()}"
            )

first_mtime = min(
    datetime.fromtimestamp(member.mtime, timezone.utc) for member in files
)
last_mtime = max(
    datetime.fromtimestamp(member.mtime, timezone.utc) for member in files
)
print(
    "Source archive provenance passed: "
    f"sha256={actual_hash}, files={len(files)}, "
    f"member_window={first_mtime.isoformat()}..{last_mtime.isoformat()}."
)
PY
fi

if [[ "$verify_external" != true ]]; then
  exit 0
fi

for command_name in gh gcloud; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Contest provenance failed: missing %s for external verification.\n' "$command_name" >&2
    exit 1
  }
done

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

gh api repos/mikeyerke/driftline >"$TMP_DIR/github.json"
gcloud projects describe driftline-hackathon-2026 --format=json >"$TMP_DIR/project.json"
gcloud builds list \
  --project=driftline-hackathon-2026 \
  --sort-by=createTime \
  --limit=1 \
  --format=json >"$TMP_DIR/build.json"

python3 - "$TMP_DIR/github.json" "$TMP_DIR/project.json" "$TMP_DIR/build.json" \
  "$CONTEST_START" "$CONTEST_END" <<'PY'
from datetime import datetime
import json
from pathlib import Path
import sys

github = json.loads(Path(sys.argv[1]).read_text())
project = json.loads(Path(sys.argv[2]).read_text())
builds = json.loads(Path(sys.argv[3]).read_text())
start = datetime.fromisoformat(sys.argv[4])
end = datetime.fromisoformat(sys.argv[5])


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


repo_created = parse(github["created_at"])
project_created = parse(project["createTime"])
if github["full_name"] != "mikeyerke/driftline" or github["visibility"] != "public":
    raise SystemExit("Contest provenance failed: unexpected GitHub repository identity")
if project["projectId"] != "driftline-hackathon-2026":
    raise SystemExit("Contest provenance failed: unexpected Google Cloud project identity")
if not builds:
    raise SystemExit("Contest provenance failed: no Cloud Build history returned")
first_build = builds[0]
build_created = parse(first_build["createTime"])
if first_build.get("status") != "SUCCESS":
    raise SystemExit("Contest provenance failed: earliest Cloud Build was not successful")
for label, value in (
    ("GitHub repository", repo_created),
    ("Google Cloud project", project_created),
    ("first Cloud Build", build_created),
):
    if not start <= value <= end:
        raise SystemExit(f"Contest provenance failed: {label} is outside the contest: {value.isoformat()}")

print(
    "External contest provenance passed: "
    f"repo={repo_created.isoformat()}, "
    f"project={project_created.isoformat()}, "
    f"first_build={first_build['id']}@{build_created.isoformat()}."
)
PY
