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


def test_demo_replay_compares_public_body_to_published_baseline(monkeypatch) -> None:
    monkeypatch.setenv(
        "DRIFTLINE_PUBLIC_SOURCE_URL",
        "https://raw.githubusercontent.com/mikeyerke/driftline/abc/fixtures/public-pricing-after.txt",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setattr(
        source,
        "urlopen",
        lambda request, timeout: _Response(
            "Enterprise includes 365-day audit-log retention."
        ),
    )

    result = source.inspect_allowlisted_source("public/pricing", force_replay=True)

    assert result["status"] == "changed"
    assert result["change_detected"] is True
    assert result["before"] == "Enterprise includes unlimited audit-log retention."
    assert result["data_mode"] == "public_source"
    assert "demo replay" in str(result["snapshot_label"])


def test_terms_source_is_a_separate_allowlisted_snapshot(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setenv(
        "DRIFTLINE_TERMS_SOURCE_URL",
        "https://raw.githubusercontent.com/mikeyerke/driftline/abc/fixtures/public-terms-after.txt",
    )
    monkeypatch.setattr(
        source,
        "urlopen",
        lambda request, timeout: _Response(
            "Enterprise contracts renew annually with 365-day audit history."
        ),
    )
    store = InMemorySnapshotStore()
    result = source.inspect_allowlisted_source("public/terms", store=store)

    assert result["status"] == "baseline_established"
    assert result["source_id"] == "public/terms"
    assert result["data_mode"] == "public_source"


def test_competitor_sources_are_allowlisted_and_synthetic_by_default() -> None:
    result = source.inspect_allowlisted_source("competitor/blog")

    assert result["status"] == "changed"
    assert result["source_id"] == "competitor/blog"
    assert result["data_mode"] == "synthetic_demo"
    assert "competitor/blog" in result["snapshot_label"]


class _Response:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, _limit: int) -> bytes:
        return self.body.encode("utf-8")
