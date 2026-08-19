from datetime import UTC, datetime

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


def test_source_registry_health_is_bounded_and_labels_synthetic_data() -> None:
    health = source.source_registry_health(now=datetime(2026, 1, 1, tzinfo=UTC))

    assert {item["source_id"] for item in health} == set(source.SOURCE_DEFINITIONS)
    assert all(item["allowlist"] == "pinned raw GitHub fixture only" for item in health)
    assert all(item["status"] in {"needs_baseline", "synthetic_only", "healthy", "stale"} for item in health)


def test_operator_registered_source_is_exact_url_and_append_only(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/example-pricing",
        name="Example pricing page",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        parser="html",
        registered_by="Signed operator",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")

    class _Opener:
        def open(self, request, timeout):
            assert request.full_url == "https://example.com/pricing"
            assert timeout == 8
            return _Response("<html><body>Pro is now $59</body></html>")

    monkeypatch.setattr(source, "build_opener", lambda _handler: _Opener())
    store = InMemorySnapshotStore()
    first = source.inspect_allowlisted_source("custom/example-pricing", store=store)
    second = source.inspect_allowlisted_source("custom/example-pricing", store=store)
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert first["status"] == "baseline_established"
    assert second["status"] == "unchanged"
    assert second["data_mode"] == "operator_registered_public"
    assert second["after"] == "Pro is now $59"


def test_operator_registered_source_rejects_query_and_private_urls() -> None:
    for url in ("https://example.com/pricing?token=secret", "https://127.0.0.1/pricing"):
        try:
            source.register_operator_source(
                source_id="custom/rejected",
                name="Rejected",
                category="Competitor pricing",
                change_type="Pricing move",
                url=url,
                owner="Product Marketing",
                cadence="24h",
                freshness_sla_hours=48,
            )
        except ValueError as exc:
            assert "source_url" in str(exc)
        else:  # pragma: no cover - security boundary assertion.
            raise AssertionError("unsafe source URL was accepted")


class _Response:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, _limit: int) -> bytes:
        return self.body.encode("utf-8")
