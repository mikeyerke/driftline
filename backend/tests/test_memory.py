from app.memory import build_memory_summary, change_genome


def _observation(body: str, timestamp: str) -> dict[str, str]:
    from app.snapshots import body_hash

    return {
        "body": body,
        "snapshot_hash": body_hash(body),
        "retrieved_at": timestamp,
        "data_mode": "public_source",
        "source_id": "public/pricing",
        "source_url": "https://example.test/pricing",
        "snapshot_label": "test",
    }


def test_change_genome_is_stable_for_equivalent_whitespace() -> None:
    assert change_genome("public/pricing", "old  claim", "new\nclaim") == change_genome(
        "public/pricing", "old claim", "new claim"
    )


def test_memory_summarizes_recurring_changes_and_unresolved_work() -> None:
    observations = {
        "public/pricing": [
            _observation("old", "2026-08-01T00:00:00+00:00"),
            _observation("new", "2026-08-02T00:00:00+00:00"),
            _observation("old", "2026-08-03T00:00:00+00:00"),
            _observation("new", "2026-08-04T00:00:00+00:00"),
        ]
    }
    workflows = [
        {
            "workflow_id": "wf-1",
            "updated_at": "2026-08-04T00:00:00+00:00",
            "evidence": {"source_id": "public/pricing", "before": "old", "after": "new"},
            "action_items": [
                {"item_id": "item-1", "artifact": "FAQ", "owner": "Support", "status": "failed"},
                {"item_id": "item-2", "artifact": "CRM", "owner": "RevOps", "status": "reversed"},
            ],
        }
    ]

    summary = build_memory_summary(observations, workflows)

    assert summary["append_only"] is True
    assert summary["work_summary"]["unresolved_count"] == 1
    assert summary["work_summary"]["failed_count"] == 1
    assert summary["work_summary"]["reversed_count"] == 1
    assert summary["recurring_changes"]
    assert summary["recurring_changes"][0]["occurrences"] >= 2
