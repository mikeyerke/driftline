CREATE TABLE IF NOT EXISTS
  `{{PROJECT_ID}}.driftline_product.decision_twin_usage_daily`
(
  observed_at TIMESTAMP NOT NULL,
  segment STRING NOT NULL,
  activation_relative_change FLOAT64 NOT NULL,
  setup_completion_relative_change FLOAT64 NOT NULL,
  sample_size INT64 NOT NULL,
  source_mode STRING NOT NULL
)
PARTITION BY TIMESTAMP_TRUNC(observed_at, DAY)
CLUSTER BY segment
OPTIONS (
  partition_expiration_days = 45,
  require_partition_filter = TRUE,
  description = 'Aggregate-only Decision Twin demo metrics; no customer rows or identifiers.'
);

MERGE `{{PROJECT_ID}}.driftline_product.decision_twin_usage_daily` AS target
USING (
  SELECT TIMESTAMP '2026-08-23 18:00:00+00' AS observed_at,
         'small_workspaces' AS segment,
         0.09 AS activation_relative_change,
         0.06 AS setup_completion_relative_change,
         126 AS sample_size,
         'pinned_aggregate_fixture' AS source_mode
  UNION ALL
  SELECT TIMESTAMP '2026-08-23 18:00:00+00',
         'enterprise_workspaces',
         -0.11,
         -0.08,
         84,
         'pinned_aggregate_fixture'
) AS source
ON target.observed_at = source.observed_at AND target.segment = source.segment
WHEN MATCHED THEN UPDATE SET
  activation_relative_change = source.activation_relative_change,
  setup_completion_relative_change = source.setup_completion_relative_change,
  sample_size = source.sample_size,
  source_mode = source.source_mode
WHEN NOT MATCHED THEN INSERT ROW;
