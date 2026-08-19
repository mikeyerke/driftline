"""Allowlisted visual evidence and strict Gemini vision analysis.

Visual inputs are intentionally separate from the text snapshot ledger.  The
registry contains only Driftline-owned public fixtures, and every response is
bound to the SHA-256 digest of both observed byte payloads.  Synthetic visual
replay is available only when the caller explicitly selects demo mode.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError

MAX_ASSET_BYTES = 2_500_000
_REF_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
}


class MultimodalUnavailable(RuntimeError):
    """Raised when visual evidence cannot be safely fetched or analyzed."""


@dataclass(frozen=True)
class VisualDefinition:
    asset_id: str
    name: str
    before_path: str
    after_path: str


@dataclass(frozen=True)
class VisualAsset:
    asset_id: str
    side: str
    label: str
    source_url: str
    mime_type: str
    body: bytes
    snapshot_hash: str
    retrieved_at: str
    data_mode: str

    def metadata(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "side": self.side,
            "label": self.label,
            "source_url": self.source_url,
            "mime_type": self.mime_type,
            "size_bytes": len(self.body),
            "snapshot_hash": self.snapshot_hash,
            "retrieved_at": self.retrieved_at,
            "data_mode": self.data_mode,
        }


@dataclass(frozen=True)
class VisualEvidence:
    asset_id: str
    name: str
    before: VisualAsset
    after: VisualAsset
    evidence_hash: str
    data_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "data_mode": self.data_mode,
            "evidence_hash": self.evidence_hash,
            "before": self.before.metadata(),
            "after": self.after.metadata(),
        }


class VisionAnalysis(BaseModel):
    """Strict model output; no unvalidated prose may enter the evidence chain."""

    model_config = ConfigDict(extra="forbid")

    evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary: str = Field(min_length=1, max_length=300)
    before_observation: str = Field(min_length=1, max_length=300)
    after_observation: str = Field(min_length=1, max_length=300)
    material_change: bool
    confidence: float = Field(ge=0.0, le=1.0)


# These are concept images already present in the public Driftline repository.
# They make the visual seam real without accepting arbitrary user URLs.  The
# ref is pinned by deployment when possible; tests use a deterministic ref.
VISUAL_DEFINITIONS: dict[str, VisualDefinition] = {
    "promise-card": VisualDefinition(
        asset_id="promise-card",
        name="Promise operations console",
        before_path="docs/concepts/change-operations-primary.png",
        after_path="docs/concepts/change-operations-approved.png",
    ),
}


def _visual_url(path: str) -> str:
    ref = os.getenv("DRIFTLINE_VISUAL_ASSET_REF", "main")
    if not _REF_PATTERN.fullmatch(ref):
        raise MultimodalUnavailable("visual_asset_ref_not_allowlisted")
    return f"https://raw.githubusercontent.com/mikeyerke/driftline/{ref}/{path}"


def _allowlisted_url(url: str, expected_path: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "raw.githubusercontent.com":
        return False
    if parsed.query or parsed.fragment or parse_qs(parsed.query):
        return False
    parts = parsed.path.strip("/").split("/")
    expected = expected_path.strip("/").split("/")
    if len(parts) != 3 + len(expected):
        return False
    if parts[:2] != ["mikeyerke", "driftline"] or not _REF_PATTERN.fullmatch(parts[2]):
        return False
    return parts[3:] == expected


def _asset_url(definition: VisualDefinition, side: str) -> str:
    if side not in {"before", "after"}:
        raise MultimodalUnavailable("visual_side_not_allowlisted")
    path = definition.before_path if side == "before" else definition.after_path
    url = _visual_url(path)
    if not _allowlisted_url(url, path):
        raise MultimodalUnavailable("visual_asset_url_not_allowlisted")
    return url


def _synthetic_asset(asset_id: str, side: str) -> VisualAsset:
    # SVG is intentionally only a demo fallback; public/live mode accepts
    # image/png, image/jpeg, and application/pdf bytes from the registry.
    phrase = (
        "Before · unlimited retention"
        if side == "before"
        else "After · 365-day retention"
    )
    body = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="260" '
        'viewBox="0 0 900 260"><rect width="900" height="260" fill="#f4f7fb"/>'
        '<text x="48" y="145" font-family="Arial,sans-serif" font-size="42" '
        'fill="#152238">'
        f"{phrase}</text></svg>"
    ).encode()
    return VisualAsset(
        asset_id=asset_id,
        side=side,
        label=f"Synthetic visual replay · {side}",
        source_url=f"synthetic://{asset_id}/{side}",
        mime_type="image/svg+xml",
        body=body,
        snapshot_hash=hashlib.sha256(body).hexdigest(),
        retrieved_at=datetime.now(UTC).isoformat(),
        data_mode="synthetic_demo",
    )


def _fetch_asset(definition: VisualDefinition, side: str) -> VisualAsset:
    url = _asset_url(definition, side)
    suffix = "." + url.rsplit(".", 1)[-1].casefold()
    mime_type = _MIME_BY_SUFFIX.get(suffix)
    if mime_type is None:
        raise MultimodalUnavailable("visual_asset_type_not_allowlisted")
    request = Request(
        url,
        headers={"User-Agent": "Driftline-visual-evidence/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read(MAX_ASSET_BYTES + 1)
        if not body or len(body) > MAX_ASSET_BYTES:
            raise MultimodalUnavailable("visual_asset_out_of_bounds")
    except (OSError, UnicodeDecodeError, URLError, ValueError) as exc:
        raise MultimodalUnavailable("visual_asset_fetch_failed") from exc
    return VisualAsset(
        asset_id=definition.asset_id,
        side=side,
        label=f"Public visual snapshot · {side}",
        source_url=url,
        mime_type=mime_type,
        body=body,
        snapshot_hash=hashlib.sha256(body).hexdigest(),
        retrieved_at=datetime.now(UTC).isoformat(),
        data_mode="public_source",
    )


def get_visual_evidence(asset_id: str, mode: str = "live") -> VisualEvidence:
    """Fetch both sides and hash them together; synthetic fallback is demo-only."""
    definition = VISUAL_DEFINITIONS.get(asset_id)
    if definition is None:
        raise MultimodalUnavailable("visual_asset_not_allowlisted")
    try:
        before = _fetch_asset(definition, "before")
        after = _fetch_asset(definition, "after")
    except MultimodalUnavailable:
        if mode != "demo":
            raise
        before = _synthetic_asset(asset_id, "before")
        after = _synthetic_asset(asset_id, "after")
    evidence_hash = hashlib.sha256(
        f"{before.snapshot_hash}\n{after.snapshot_hash}".encode("ascii")
    ).hexdigest()
    return VisualEvidence(
        asset_id=asset_id,
        name=definition.name,
        before=before,
        after=after,
        evidence_hash=evidence_hash,
        data_mode=before.data_mode,
    )


def visual_asset_bytes(asset_id: str, side: str, mode: str = "live") -> VisualAsset:
    evidence = get_visual_evidence(asset_id, mode)
    if side == "before":
        return evidence.before
    if side == "after":
        return evidence.after
    raise MultimodalUnavailable("visual_side_not_allowlisted")


def _parse_model_json(raw: str) -> dict[str, Any]:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = candidate.removeprefix("```").removeprefix("json").strip()
        if candidate.endswith("```"):
            candidate = candidate[:-3].strip()
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        # Keep the model seam strict while tolerating a single explanatory
        # prefix/suffix around the requested JSON object.
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise MultimodalUnavailable("vision_analysis_not_json") from exc
        try:
            payload = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as nested_exc:
            raise MultimodalUnavailable("vision_analysis_not_json") from nested_exc
    if not isinstance(payload, dict):
        raise MultimodalUnavailable("vision_analysis_not_object")
    return payload


def validate_vision_analysis(payload: Any, evidence_hash: str) -> VisionAnalysis:
    try:
        result = (
            payload
            if isinstance(payload, VisionAnalysis)
            else VisionAnalysis.model_validate(payload)
        )
    except (ValidationError, TypeError, ValueError) as exc:
        raise MultimodalUnavailable("vision_analysis_schema_invalid") from exc
    if result.evidence_hash != evidence_hash:
        raise MultimodalUnavailable("vision_analysis_evidence_hash_mismatch")
    return result


def _run_vision_model(evidence: VisualEvidence) -> VisionAnalysis:
    from google import genai
    from google.genai import types

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    kwargs: dict[str, Any] = {"vertexai": True, "location": location}
    if project:
        kwargs["project"] = project
    client = genai.Client(**kwargs)
    prompt = (
        "Compare the before and after visual evidence. Return only the JSON "
        "schema. Describe observable operational differences, do not infer "
        f"hidden pixels, and set evidence_hash exactly to {evidence.evidence_hash}."
    )
    contents = [
        types.Part.from_text(text=prompt),
        types.Part.from_text(text="BEFORE VISUAL"),
        types.Part.from_bytes(
            data=evidence.before.body, mime_type=evidence.before.mime_type
        ),
        types.Part.from_text(text="AFTER VISUAL"),
        types.Part.from_bytes(
            data=evidence.after.body, mime_type=evidence.after.mime_type
        ),
    ]
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=VisionAnalysis.model_json_schema(),
        max_output_tokens=700,
    )
    try:
        response = client.models.generate_content(
            model=os.getenv("MODEL_NAME", "gemini-3.5-flash"),
            contents=contents,
            config=config,
        )
        raw = getattr(response, "text", "") or ""
        if not raw:
            # Some Vertex responses expose structured JSON only through the
            # candidate parts even when the convenience `.text` property is
            # empty. Read those parts without accepting prose or hidden state.
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", []) or []:
                    part_text = getattr(part, "text", None)
                    if part_text:
                        raw += part_text
        return validate_vision_analysis(_parse_model_json(raw), evidence.evidence_hash)
    except MultimodalUnavailable:
        raise
    except Exception as exc:
        raise MultimodalUnavailable("vision_analysis_request_failed") from exc


def analyze_visual_evidence(asset_id: str, mode: str = "live") -> dict[str, Any]:
    evidence = get_visual_evidence(asset_id, mode)
    if evidence.data_mode == "synthetic_demo":
        if mode != "demo":
            raise MultimodalUnavailable("synthetic_visual_not_allowed")
        analysis = VisionAnalysis(
            evidence_hash=evidence.evidence_hash,
            summary="Synthetic visual replay shows the review state moving from observed change to approval.",
            before_observation="The pre-approval console is waiting for a human decision.",
            after_observation="The post-approval console shows bounded outputs and a recorded decision.",
            material_change=True,
            confidence=0.0,
        )
        return {
            "mode": "synthetic_demo",
            "model": "synthetic",
            "analysis": analysis.model_dump(),
            "evidence": evidence.to_dict(),
        }
    analysis = _run_vision_model(evidence)
    return {
        "mode": "gemini_vision",
        "model": os.getenv("MODEL_NAME", "gemini-3.5-flash"),
        "analysis": analysis.model_dump(),
        "evidence": evidence.to_dict(),
    }
