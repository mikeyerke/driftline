from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.product_analytics import (
    AnalyticsPolicyError,
    fixture_aggregate_metrics,
    query_aggregate_metric,
)


def test_bigquery_seed_refresh_is_current_bounded_and_non_accumulating() -> None:
    sql_path = Path(__file__).parents[2] / "infra" / "decision_twin_bigquery.sql"
    sql = sql_path.read_text()

    assert "require_partition_filter = TRUE" in sql
    assert "TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)" in sql
    assert "TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)" in sql
    assert sql.count("CURRENT_TIMESTAMP()") >= 4
    assert "DELETE FROM" in sql
    assert "source_mode = 'pinned_aggregate_fixture'" in sql


def test_fixture_metrics_are_bounded_aggregates_without_customer_rows() -> None:
    metrics = fixture_aggregate_metrics()

    assert {(item.metric_id, item.segment) for item in metrics} == {
        ("activation_rate", "small_workspaces"),
        ("activation_rate", "enterprise_workspaces"),
    }
    assert all(item.source_mode == "pinned_aggregate_fixture" for item in metrics)
    assert all(item.sample_size >= 25 for item in metrics)
    assert all("customer" not in item.model_dump() for item in metrics)


def test_bigquery_adapter_rejects_unallowlisted_metric_segment_and_table(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_ENABLED", "true")
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_TABLE", "project.dataset.table")

    with pytest.raises(AnalyticsPolicyError, match="metric"):
        query_aggregate_metric("revenue", "enterprise_workspaces")
    with pytest.raises(AnalyticsPolicyError, match="segment"):
        query_aggregate_metric("activation_rate", "named_customer")

    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_TABLE", "project;DROP TABLE")
    with pytest.raises(AnalyticsPolicyError, match="table"):
        query_aggregate_metric("activation_rate", "enterprise_workspaces")


def test_bigquery_adapter_dry_runs_caps_bytes_and_uses_parameters(monkeypatch) -> None:
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_ENABLED", "true")
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_TABLE", "project.dataset.usage_daily")
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_MAX_BYTES", "50000000")
    calls = []

    class FakeClient:
        def query(self, sql, job_config):
            calls.append((sql, job_config))
            if job_config.dry_run:
                return SimpleNamespace(total_bytes_processed=1024)
            return SimpleNamespace(
                result=lambda: [
                    {
                        "metric_value": -0.11,
                        "baseline_value": 0.0,
                        "sample_size": 84,
                        "observed_at": "2026-08-23T18:00:00+00:00",
                    }
                ]
            )

    metric = query_aggregate_metric(
        "activation_rate",
        "enterprise_workspaces",
        client=FakeClient(),
    )

    assert metric.value == -0.11
    assert metric.sample_size == 84
    assert metric.source_mode == "bigquery_aggregate"
    assert len(calls) == 2
    assert calls[0][1].dry_run is True
    assert calls[1][1].maximum_bytes_billed == 50_000_000
    assert "enterprise_workspaces" not in calls[1][0]
    assert "SUM(activation_relative_change * sample_size)" in calls[1][0]
    assert "SUM(sample_size)" in calls[1][0]
    assert calls[1][1].query_parameters[0].name == "segment"


def test_bigquery_adapter_fails_closed_when_dry_run_exceeds_cap(monkeypatch) -> None:
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_ENABLED", "true")
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_TABLE", "project.dataset.usage_daily")
    monkeypatch.setenv("DECISION_TWIN_BIGQUERY_MAX_BYTES", "1000")

    class ExpensiveClient:
        def query(self, _sql, job_config):
            assert job_config.dry_run is True
            return SimpleNamespace(total_bytes_processed=1001)

    with pytest.raises(AnalyticsPolicyError, match="byte cap"):
        query_aggregate_metric(
            "activation_rate",
            "enterprise_workspaces",
            client=ExpensiveClient(),
        )
