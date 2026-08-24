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

-- Refresh only the bounded pinned-fixture partitions. This keeps demo metrics
-- inside the reader's 30-day window without accumulating repeated sample sizes.
DELETE FROM `{{PROJECT_ID}}.driftline_product.decision_twin_usage_daily`
WHERE source_mode = 'pinned_aggregate_fixture'
  AND observed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
  AND observed_at < TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);

INSERT INTO `{{PROJECT_ID}}.driftline_product.decision_twin_usage_daily`
  (observed_at, segment, activation_relative_change,
   setup_completion_relative_change, sample_size, source_mode)
VALUES
  (CURRENT_TIMESTAMP(), 'small_workspaces',
   0.09, 0.06, 126, 'pinned_aggregate_fixture'),
  (CURRENT_TIMESTAMP(), 'enterprise_workspaces',
   -0.11, -0.08, 84, 'pinned_aggregate_fixture');
