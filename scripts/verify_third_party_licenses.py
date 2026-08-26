from __future__ import annotations

import json
import re
import tomllib
from collections import Counter
from importlib.metadata import Distribution, distributions
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_PROJECT = ROOT / "backend" / "pyproject.toml"
FRONTEND_PACKAGE = ROOT / "frontend" / "package.json"
FRONTEND_LOCK = ROOT / "frontend" / "package-lock.json"
DENIED_LICENSE = re.compile(
    r"(?:^|[^A-Z])(?:A?GPL|SSPL|BUSL)(?:-|[^A-Z]|$)", re.IGNORECASE
)


def fail(message: str) -> None:
    raise SystemExit(f"Third-party license check failed: {message}")


def normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).casefold()


def declared_name(requirement: str) -> str:
    return normalized_name(re.split(r"[<>=!~\[ ;]", requirement, maxsplit=1)[0])


def python_license(dist: Distribution) -> tuple[str, str]:
    metadata = dist.metadata
    expression = (metadata.get("License-Expression") or "").strip()
    license_value = (metadata.get("License") or "").strip()
    classifiers = [
        value.removeprefix("License :: ").strip()
        for value in metadata.get_all("Classifier") or []
        if value.startswith("License ::")
    ]
    if expression:
        return expression, "metadata:License-Expression"
    if license_value and license_value.casefold() not in {"unknown", "dual license"}:
        return " ".join(license_value.split()), "metadata:License"
    if classifiers:
        return " | ".join(classifiers), "metadata:Classifier"
    for entry in dist.files or []:
        entry_text = str(entry).casefold()
        if "license" not in entry_text and "copying" not in entry_text:
            continue
        path = Path(dist.locate_file(entry))
        text = path.read_text(errors="replace")[:1200].casefold()
        if "apache license" in text and "version 2.0" in text:
            return "Apache-2.0", f"license-file:{entry}"
        if "mit license" in text:
            return "MIT", f"license-file:{entry}"
        if "mozilla public license" in text and "2.0" in text:
            return "MPL-2.0", f"license-file:{entry}"
        if "bsd" in text:
            return "BSD", f"license-file:{entry}"
    return "", "missing"


project = tomllib.loads(BACKEND_PROJECT.read_text())
declared_backend = {
    declared_name(requirement)
    for requirement in (
        list(project["project"]["dependencies"])
        + [
            requirement
            for group in project["project"].get("optional-dependencies", {}).values()
            for requirement in group
        ]
    )
}

python_inventory: list[tuple[str, str, str, str]] = []
installed_backend: set[str] = set()
for dist in distributions():
    name = dist.metadata.get("Name") or ""
    if normalized_name(name) == "driftline-agent":
        continue
    license_value, source = python_license(dist)
    if not license_value:
        fail(f"Python package {name} {dist.version} has no resolvable license")
    if DENIED_LICENSE.search(license_value):
        fail(
            f"Python package {name} {dist.version} uses review-required license {license_value}"
        )
    installed_backend.add(normalized_name(name))
    python_inventory.append((name, dist.version, license_value, source))

missing_backend = sorted(declared_backend - installed_backend)
if missing_backend:
    fail(f"declared backend dependencies are not installed: {missing_backend}")

frontend = json.loads(FRONTEND_PACKAGE.read_text())
lock = json.loads(FRONTEND_LOCK.read_text())
declared_frontend = set(frontend.get("dependencies", {})) | set(
    frontend.get("devDependencies", {})
)
locked_frontend = {
    path.removeprefix("node_modules/"): metadata
    for path, metadata in lock.get("packages", {}).items()
    if path.startswith("node_modules/") and "/node_modules/" not in path
}
missing_frontend = sorted(declared_frontend - set(locked_frontend))
if missing_frontend:
    fail(
        f"declared frontend dependencies are absent from the lockfile: {missing_frontend}"
    )

node_inventory: list[tuple[str, str, str]] = []
for path, metadata in lock.get("packages", {}).items():
    if not path:
        continue
    license_value = str(metadata.get("license") or "").strip()
    if not license_value:
        fail(f"Node lock entry {path} {metadata.get('version')} has no license")
    if DENIED_LICENSE.search(license_value):
        fail(
            f"Node lock entry {path} {metadata.get('version')} uses "
            f"review-required license {license_value}"
        )
    node_inventory.append((path, str(metadata.get("version") or ""), license_value))

python_classes = Counter(item[2] for item in python_inventory)
node_classes = Counter(item[2] for item in node_inventory)
print(
    "Third-party license checks passed: "
    f"{len(python_inventory)} Python distributions, "
    f"{len(node_inventory)} Node lock entries, "
    f"{len(declared_backend)} declared backend packages, "
    f"{len(declared_frontend)} declared frontend packages."
)
print(
    "Python license classes:",
    json.dumps(dict(sorted(python_classes.items())), sort_keys=True),
)
print(
    "Node license classes:",
    json.dumps(dict(sorted(node_classes.items())), sort_keys=True),
)
