from datetime import UTC, datetime
from urllib.error import URLError

import pytest

from app import source
from app.snapshots import InMemorySnapshotStore


def test_pinned_https_handler_uses_context_hostname_policy(monkeypatch) -> None:
    handler = source._PinnedHTTPSHandler("93.184.216.34")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        handler,
        "do_open",
        lambda *_args, **kwargs: captured.update(kwargs) or "opened",
    )

    assert handler.https_open(object()) == "opened"
    assert captured["check_hostname"] is True


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


def test_monitor_fetch_failure_never_becomes_synthetic_change(monkeypatch) -> None:
    source._SOURCE_FAILURES_MEMORY.clear()
    monkeypatch.setenv(
        "DRIFTLINE_PUBLIC_SOURCE_URL",
        "https://raw.githubusercontent.com/mikeyerke/driftline/abc/fixtures/public-pricing-after.txt",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")

    def unavailable(_request, timeout):
        raise URLError(f"timeout after {timeout}s")

    monkeypatch.setattr(source, "urlopen", unavailable)

    result = source.inspect_allowlisted_source("public/pricing", force_replay=False)

    assert result["status"] == "source_fetch_failed"
    assert result["change_detected"] is False
    assert result["data_mode"] == "public_source"
    assert result["confidence"] == 0.0
    assert "after" not in result
    source._SOURCE_FAILURES_MEMORY.clear()


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
    source._SOURCE_FAILURES_MEMORY.clear()
    health = source.source_registry_health(now=datetime(2026, 1, 1, tzinfo=UTC))

    assert {item["source_id"] for item in health} == set(source.SOURCE_DEFINITIONS)
    assert all(item["allowlist"] == "pinned raw GitHub fixture only" for item in health)
    assert all(
        item["status"] in {"needs_baseline", "synthetic_only", "healthy", "stale"}
        for item in health
    )


def test_source_registry_health_surfaces_latest_fetch_failure() -> None:
    source._SOURCE_FAILURES_MEMORY.clear()
    definition = source.SOURCE_DEFINITIONS["competitor/pricing"]
    source._record_source_failure(
        "competitor/pricing",
        tenant_id=None,
        definition=definition,
        reason="source_challenge_page_detected",
        failed_at="2026-01-01T00:00:00+00:00",
    )

    health = source.source_registry_health(now=datetime(2026, 1, 2, tzinfo=UTC))
    pricing = next(item for item in health if item["source_id"] == "competitor/pricing")

    assert pricing["status"] == "source_failed"
    assert pricing["last_failure_reason"] == "source_challenge_page_detected"
    source._SOURCE_FAILURES_MEMORY.clear()


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
        tenant_id="tenant-acme",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setattr(source, "_resolve_public_address", lambda _host: "93.184.216.34")

    class _Opener:
        def open(self, request, timeout):
            assert request.full_url == "https://example.com/pricing"
            assert timeout == 8
            return _Response("<html><body>Pro is now $59</body></html>")

    monkeypatch.setattr(source, "build_opener", lambda *_handlers: _Opener())
    store = InMemorySnapshotStore()
    first = source.inspect_allowlisted_source("custom/example-pricing", tenant_id="tenant-acme", store=store)
    second = source.inspect_allowlisted_source("custom/example-pricing", tenant_id="tenant-acme", store=store)
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert first["status"] == "baseline_established"
    assert second["status"] == "unchanged"
    assert second["data_mode"] == "operator_registered_public"
    assert second["after"] == "Pro is now $59"


def test_anonymous_registry_never_lists_tenant_custom_source(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    source.register_operator_source(
        source_id="custom/private-pricing",
        name="Private tenant pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/private-pricing",
        owner="Tenant PMM",
        cadence="24h",
        freshness_sla_hours=48,
        parser="html",
        registered_by="Tenant owner",
        tenant_id="tenant-acme",
    )
    try:
        assert "custom/private-pricing" not in source.source_definitions()
        assert "custom/private-pricing" in source.source_definitions("tenant-acme")
        assert source.list_source_history("custom/private-pricing") == []
    finally:
        source._CUSTOM_SOURCE_DEFINITIONS.clear()


def test_operator_registered_rss_source_normalizes_entries(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/example-feed",
        name="Example product feed",
        category="Competitor narrative",
        change_type="Product announcement",
        url="https://example.com/feed.xml",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        parser="rss",
        tenant_id="tenant-acme",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setattr(source, "_resolve_public_address", lambda _host: "93.184.216.34")

    class _Opener:
        def open(self, request, timeout):
            assert request.full_url == "https://example.com/feed.xml"
            assert timeout == 8
            return _Response(
                """<?xml version="1.0"?><rss><channel>
                <item><title>Residency is now available</title>
                <pubDate>2026-08-20</pubDate><link>https://example.com/post</link>
                <description><![CDATA[<p>Regional storage is live.</p>]]></description></item>
                </channel></rss>"""
            )

    monkeypatch.setattr(source, "build_opener", lambda *_handlers: _Opener())
    result = source.inspect_allowlisted_source(
        "custom/example-feed", tenant_id="tenant-acme", store=InMemorySnapshotStore()
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert result["status"] == "baseline_established"
    assert "Residency is now available" in result["after"]
    assert "Regional storage is live" in result["after"]
    assert "<p>" not in result["after"]


def test_operator_registered_rss_rejects_malformed_xml(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/bad-feed",
        name="Bad feed",
        category="Competitor narrative",
        change_type="Announcement",
        url="https://example.com/feed.xml",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        parser="rss",
        tenant_id="tenant-acme",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setattr(source, "_resolve_public_address", lambda _host: "93.184.216.34")
    monkeypatch.setattr(
        source,
        "build_opener",
        lambda *_handlers: type(
            "_Opener",
            (),
            {"open": lambda self, request, timeout: _Response("<rss>")},
        )(),
    )
    result = source.inspect_allowlisted_source(
        "custom/bad-feed", tenant_id="tenant-acme", store=InMemorySnapshotStore()
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert result["status"] == "source_fetch_failed"
    assert result["reason"] == "source_rss_invalid"


def test_operator_sources_and_history_are_tenant_scoped() -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/shared-pricing",
        name="Acme pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://acme.example/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id="acme",
    )
    source.register_operator_source(
        source_id="custom/shared-pricing",
        name="Beta pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://beta.example/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id="beta",
    )
    assert source.source_definition("custom/shared-pricing", "acme")["url"] == "https://acme.example/pricing"
    assert source.source_definition("custom/shared-pricing", "beta")["url"] == "https://beta.example/pricing"
    assert source.source_definition("custom/shared-pricing", "other") is None
    assert source._snapshot_storage_key(
        "public/pricing", "acme", source.SOURCE_DEFINITIONS["public/pricing"]
    ) == "tenant/acme/public/pricing"
    assert source._snapshot_storage_key(
        "public/pricing", "beta", source.SOURCE_DEFINITIONS["public/pricing"]
    ) != source._snapshot_storage_key(
        "public/pricing", "acme", source.SOURCE_DEFINITIONS["public/pricing"]
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()


def test_operator_source_rejects_challenge_interstitial_without_recording_change(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/challenge-page",
        name="Challenge page",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        parser="html",
        tenant_id="tenant-acme",
    )
    monkeypatch.setenv("DRIFTLINE_SOURCE_MODE", "public")
    monkeypatch.setattr(source, "_resolve_public_address", lambda _host: "93.184.216.34")

    class _Opener:
        def open(self, request, timeout):
            return _Response(
                "<html><body>Verify you are human. Enable JavaScript and complete the captcha.</body></html>"
            )

    monkeypatch.setattr(source, "build_opener", lambda *_handlers: _Opener())
    result = source.inspect_allowlisted_source(
        "custom/challenge-page", tenant_id="tenant-acme", store=InMemorySnapshotStore()
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert result["status"] == "source_fetch_failed"
    assert result["reason"] == "source_challenge_page_detected"
    assert result["change_detected"] is False


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


def test_registered_source_dns_resolution_rejects_private_address(monkeypatch) -> None:
    monkeypatch.setattr(
        source.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (source.socket.AF_INET, source.socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ],
    )

    with pytest.raises(ValueError, match="source_url_resolved_address_rejected"):
        source._resolve_public_address("attacker.example")


def test_pinned_https_connection_dials_validated_address(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class _Socket:
        pass

    class _Context:
        def wrap_socket(self, sock, *, server_hostname):
            calls["server_hostname"] = server_hostname
            return sock

    monkeypatch.setattr(
        source.socket,
        "create_connection",
        lambda address, timeout, source_address: calls.update(
            address=address, timeout=timeout, source_address=source_address
        ) or _Socket(),
    )
    connection = source._PinnedHTTPSConnection(
        "example.com", resolved_address="93.184.216.34", timeout=8
    )
    connection._context = _Context()
    connection.connect()

    assert calls["address"] == ("93.184.216.34", 443)
    assert calls["timeout"] == 8
    assert calls["server_hostname"] == "example.com"


def test_pinned_https_connection_consumes_handler_hostname_kwarg() -> None:
    connection = source._PinnedHTTPSConnection(
        "example.com",
        resolved_address="93.184.216.34",
        check_hostname=True,
    )
    assert connection._resolved_address == "93.184.216.34"


class _Response:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, _limit: int) -> bytes:
        return self.body.encode("utf-8")
