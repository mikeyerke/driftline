from __future__ import annotations

from typing import Any

from app import artifacts


class _Blob:
    def __init__(self) -> None:
        self.generation: int | None = None
        self.uploads: list[dict[str, Any]] = []
        self.reloads = 0

    def upload_from_string(self, body: bytes, **kwargs: Any) -> None:
        self.uploads.append({"body": body, **kwargs})
        if len(self.uploads) > 1:
            raise artifacts.PreconditionFailed("already exists")
        self.generation = 17

    def reload(self) -> None:
        self.reloads += 1
        self.generation = 17


def test_immutable_upload_uses_create_precondition_and_reuses_existing(monkeypatch) -> None:
    class _PreconditionFailed(Exception):
        pass

    monkeypatch.setattr(artifacts, "PreconditionFailed", _PreconditionFailed)
    blob = _Blob()

    first_generation, first_reused = artifacts._upload_immutable(
        blob, b"packet", content_type="text/markdown"
    )
    second_generation, second_reused = artifacts._upload_immutable(
        blob, b"packet", content_type="text/markdown"
    )

    assert first_generation == "17"
    assert first_reused is False
    assert second_generation == "17"
    assert second_reused is True
    assert blob.reloads == 1
    assert all(upload["if_generation_match"] == 0 for upload in blob.uploads)
