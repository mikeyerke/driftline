from app.snapshots import InMemorySnapshotStore, SnapshotRecord, compare_and_record


def test_first_observation_establishes_a_baseline_without_claiming_change() -> None:
    result = compare_and_record(
        source_id="public/pricing",
        body="Enterprise includes 365-day audit-log retention.",
        source_url="https://raw.githubusercontent.com/mikeyerke/driftline/abc/fixtures/public-pricing-after.txt",
        data_mode="public_source",
        snapshot_label="Public GitHub snapshot",
        store=InMemorySnapshotStore(),
    )

    assert result["status"] == "baseline_established"
    assert result["change_detected"] is False
    assert result["before"] == ""
    assert result["confidence"] == 0.0
    assert result["previous_snapshot_hash"] is None


def test_identical_body_is_unchanged_and_uses_prior_snapshot() -> None:
    store = InMemorySnapshotStore()
    kwargs = {
        "source_id": "public/pricing",
        "source_url": "https://raw.githubusercontent.com/mikeyerke/driftline/abc/fixtures/public-pricing-after.txt",
        "data_mode": "public_source",
        "snapshot_label": "Public GitHub snapshot",
        "store": store,
    }
    compare_and_record(body="same", **kwargs)
    result = compare_and_record(body="same", **kwargs)

    assert result["status"] == "unchanged"
    assert result["change_detected"] is False
    assert result["before"] == "same"
    assert result["confidence"] == 1.0
    assert result["confidence"] != 0.99


def test_different_body_is_a_change_bound_to_previous_hash() -> None:
    store = InMemorySnapshotStore()
    kwargs = {
        "source_id": "public/pricing",
        "source_url": "https://raw.githubusercontent.com/mikeyerke/driftline/abc/fixtures/public-pricing-after.txt",
        "data_mode": "public_source",
        "snapshot_label": "Public GitHub snapshot",
        "store": store,
    }
    first = compare_and_record(body="old", **kwargs)
    result = compare_and_record(body="new", **kwargs)

    assert result["status"] == "changed"
    assert result["change_detected"] is True
    assert result["before"] == "old"
    assert result["previous_snapshot_hash"] == first["snapshot_hash"]
    assert result["snapshot_hash"] != result["previous_snapshot_hash"]


def test_store_rejects_mismatched_source_id() -> None:
    store = InMemorySnapshotStore()
    record = SnapshotRecord.create(
        source_id="other/source",
        body="body",
        source_url="https://example.test",
        data_mode="public_source",
        snapshot_label="test",
    )

    try:
        store.record("public/pricing", record)
    except ValueError as exc:
        assert str(exc) == "snapshot_source_id_mismatch"
    else:
        raise AssertionError("store must reject mismatched source IDs")


def test_in_memory_history_is_append_only_and_newest_first() -> None:
    store = InMemorySnapshotStore()
    kwargs = {
        "source_id": "public/pricing",
        "source_url": "https://example.test/pricing",
        "data_mode": "public_source",
        "snapshot_label": "test",
        "store": store,
    }
    compare_and_record(body="old", **kwargs, retrieved_at="2026-08-19T10:00:00+00:00")
    compare_and_record(body="new", **kwargs, retrieved_at="2026-08-19T11:00:00+00:00")

    history = store.history("public/pricing")
    assert [record.body for record in history] == ["new", "old"]
