"""Allowlisted BigQuery aggregates for Decision Twin product evidence."""

from __future__ import annotations

import os
import re
from typing import Any, Literal

from google.cloud import bigquery
from pydantic import BaseModel, ConfigDict, Field

_METRIC_COLUMNS = {
    "activation_rate": "activation_relative_change",
    "setup_completion_rate": "setup_completion_relative_change",
}
_SEGMENTS = {"small_workspaces", "enterprise_workspaces"}
_TABLE_PATTERN = re.compile(
    r"^[a-z][a-z0-9-]{4,61}[a-z0-9]\.[A-Za-z_][A-Za-z0-9_]{0,1023}\."
    r"[A-Za-z_][A-Za-z0-9_]{0,1023}$"
)


class AnalyticsPolicyError(RuntimeError):
    """Raised when a query would exceed the bounded analytics contract."""


class AggregateMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: Literal["activation_rate", "setup_completion_rate"]
    segment: Literal["small_workspaces", "enterprise_workspaces"]
    value: float
    baseline: float
    sample_size: int = Field(ge=25)
    observed_at: str
    source_mode: Literal["pinned_aggregate_fixture", "bigquery_aggregate"]


class DecisionPrecedentMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    precedent_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,100}$")
    title: str = Field(min_length=1, max_length=120)
    chosen_response: Literal["ship", "rollback", "segment", "defer"]
    outcome: Literal["validated", "invalidated", "inconclusive"]
    lesson: str = Field(min_length=1, max_length=280)
    similarity: float = Field(ge=0.0, le=1.0)
    source_label: str = Field(min_length=1, max_length=160)


def fixture_aggregate_metrics() -> list[AggregateMetric]:
    return [
        AggregateMetric(
            metric_id="activation_rate",
            segment="small_workspaces",
            value=0.09,
            baseline=0.0,
            sample_size=126,
            observed_at="2026-08-23T18:00:00+00:00",
            source_mode="pinned_aggregate_fixture",
        ),
        AggregateMetric(
            metric_id="activation_rate",
            segment="enterprise_workspaces",
            value=-0.11,
            baseline=0.0,
            sample_size=84,
            observed_at="2026-08-23T18:00:00+00:00",
            source_mode="pinned_aggregate_fixture",
        ),
    ]


def _max_bytes() -> int:
    try:
        configured = int(os.getenv("DECISION_TWIN_BIGQUERY_MAX_BYTES", "50000000"))
    except ValueError as exc:
        raise AnalyticsPolicyError("BigQuery byte cap must be an integer") from exc
    return max(1_000, min(configured, 100_000_000))


def _table_id() -> str:
    table = os.getenv("DECISION_TWIN_BIGQUERY_TABLE", "")
    if not _TABLE_PATTERN.fullmatch(table):
        raise AnalyticsPolicyError("BigQuery table must be an exact project.dataset.table")
    return table


def _precedent_table_id() -> str:
    table = os.getenv("DECISION_TWIN_PRECEDENT_TABLE", "")
    if not _TABLE_PATTERN.fullmatch(table):
        raise AnalyticsPolicyError(
            "BigQuery precedent table must be an exact project.dataset.table"
        )
    return table


def _row_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row[key]
    return getattr(row, key)


def query_aggregate_metric(
    metric_id: str,
    segment: str,
    *,
    client: bigquery.Client | None = None,
) -> AggregateMetric:
    """Read one aggregate metric; models never generate or modify this SQL."""
    if os.getenv("DECISION_TWIN_BIGQUERY_ENABLED", "false").casefold() != "true":
        raise AnalyticsPolicyError("BigQuery analytics is not enabled")
    if metric_id not in _METRIC_COLUMNS:
        raise AnalyticsPolicyError("metric is outside the allowlisted aggregate set")
    if segment not in _SEGMENTS:
        raise AnalyticsPolicyError("segment is outside the allowlisted aggregate set")
    table = _table_id()
    # The column comes from a closed server-side map; segment and date window
    # remain query parameters. No caller or model controls SQL identifiers.
    column = _METRIC_COLUMNS[metric_id]
    sql = f"""
        SELECT
          SAFE_DIVIDE(
            SUM({column} * sample_size),
            SUM(sample_size)
          ) AS metric_value,
          0.0 AS baseline_value,
          SUM(sample_size) AS sample_size,
          MAX(observed_at) AS observed_at
        FROM `{table}`
        WHERE segment = @segment
          AND observed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
    """
    parameters = [
        bigquery.ScalarQueryParameter("segment", "STRING", segment),
        bigquery.ScalarQueryParameter("days", "INT64", 30),
    ]
    maximum_bytes = _max_bytes()
    query_client = client or bigquery.Client()
    dry_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
        query_parameters=parameters,
        maximum_bytes_billed=maximum_bytes,
    )
    dry_job = query_client.query(sql, job_config=dry_config)
    if int(dry_job.total_bytes_processed or 0) > maximum_bytes:
        raise AnalyticsPolicyError("BigQuery dry run exceeds the configured byte cap")
    run_config = bigquery.QueryJobConfig(
        use_query_cache=True,
        query_parameters=parameters,
        maximum_bytes_billed=maximum_bytes,
    )
    rows = list(query_client.query(sql, job_config=run_config).result())
    if len(rows) != 1 or _row_value(rows[0], "metric_value") is None:
        raise AnalyticsPolicyError("BigQuery aggregate returned no usable observation")
    row = rows[0]
    sample_size = int(_row_value(row, "sample_size") or 0)
    if sample_size < 25:
        raise AnalyticsPolicyError("BigQuery aggregate is below the privacy sample floor")
    return AggregateMetric(
        metric_id=metric_id,
        segment=segment,
        value=float(_row_value(row, "metric_value")),
        baseline=float(_row_value(row, "baseline_value") or 0.0),
        sample_size=sample_size,
        observed_at=str(_row_value(row, "observed_at")),
        source_mode="bigquery_aggregate",
    )


def query_decision_precedents(
    decision_vector: list[float],
    *,
    client: bigquery.Client | None = None,
) -> list[DecisionPrecedentMatch]:
    """Find structurally similar decisions with exact, byte-capped vector search."""
    if os.getenv("DECISION_TWIN_DECISION_MEMORY_ENABLED", "false").casefold() != "true":
        raise AnalyticsPolicyError("Decision memory is not enabled")
    if len(decision_vector) != 4 or any(not -1.0 <= float(value) <= 1.0 for value in decision_vector):
        raise AnalyticsPolicyError("Decision vector violates the bounded four-feature contract")
    table = _precedent_table_id()
    sql = f"""
        SELECT
          base.precedent_id,
          base.title,
          base.chosen_response,
          base.outcome,
          base.lesson,
          distance
        FROM VECTOR_SEARCH(
          (
            SELECT precedent_id, title, chosen_response, outcome, lesson,
                   decision_vector
            FROM `{table}`
            WHERE observed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
          ),
          'decision_vector',
          (SELECT @decision_vector AS decision_vector),
          top_k => 2,
          distance_type => 'EUCLIDEAN'
        )
        ORDER BY distance ASC
    """
    parameters = [
        bigquery.ArrayQueryParameter(
            "decision_vector", "FLOAT64", [float(value) for value in decision_vector]
        )
    ]
    maximum_bytes = _max_bytes()
    query_client = client or bigquery.Client()
    dry_job = query_client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
            query_parameters=parameters,
            maximum_bytes_billed=maximum_bytes,
        ),
    )
    if int(dry_job.total_bytes_processed or 0) > maximum_bytes:
        raise AnalyticsPolicyError("BigQuery precedent dry run exceeds the configured byte cap")
    rows = list(
        query_client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                use_query_cache=True,
                query_parameters=parameters,
                maximum_bytes_billed=maximum_bytes,
            ),
        ).result()
    )
    if not rows:
        raise AnalyticsPolicyError("BigQuery decision memory returned no usable precedent")
    return [
        DecisionPrecedentMatch(
            precedent_id=str(_row_value(row, "precedent_id")),
            title=str(_row_value(row, "title")),
            chosen_response=str(_row_value(row, "chosen_response")),
            outcome=str(_row_value(row, "outcome")),
            lesson=str(_row_value(row, "lesson")),
            similarity=max(0.0, min(1.0, 1.0 / (1.0 + float(_row_value(row, "distance"))))),
            source_label="BigQuery vector decision memory · synthetic precedent fixture",
        )
        for row in rows
    ]
