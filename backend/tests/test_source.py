from app import source
from app.snapshots import InMemorySnapshotStore


def test_public_adapter_rejects_arbitrary_host(monkeypatch) -> None:
    monkeypatch.setenv(
        "DRIFTLINE_PUBLIC_SOURCE_URL",
        "https://example.com/mikeyerke/driftline/abc/fixtures/public-pricing-after.txt",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")

    result = source.inspect_allowlisted_source("public/pricing")

    assert result["status"] == "rejected"
    assert result["reason"] == "source_url_not_allowlisted"


def test_public_adapter_records_history_and_labels_public_data(monkeypatch) -> None:
    monkeypatch.setenv(
        "DRIFTLINE_PUBLIC_SOURCE_URL",
        "https://raw.githubusercontent.com/mikeyerke/driftline/abc/fixtures/public-pricing-after.txt",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setattr(
        source,
        "urlopen",
        lambda request, timeout: _Response("current body"),
    )
    store = InMemorySnapshotStore()

    first = source.inspect_allowlisted_source("public/pricing", store=store)
    second = source.inspect_allowlisted_source("public/pricing", store=store)

    assert first["status"] == "baseline_established"
    assert second["status"] == "unchanged"
    assert second["data_mode"] == "public_source"
    assert "allowlisted" in str(second["snapshot_label"])
    assert second["confidence"] != 0.99


class _Response:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, _limit: int) -> bytes:
        return self.body.encode("utf-8")
