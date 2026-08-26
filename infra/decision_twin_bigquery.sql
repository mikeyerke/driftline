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

CREATE TABLE IF NOT EXISTS
  `{{PROJECT_ID}}.driftline_product.decision_twin_precedents`
(
  observed_at TIMESTAMP NOT NULL,
  precedent_id STRING NOT NULL,
  title STRING NOT NULL,
  chosen_response STRING NOT NULL,
  outcome STRING NOT NULL,
  lesson STRING NOT NULL,
  -- BigQuery arrays are never NULL; the platform stores a missing array as [].
  decision_vector ARRAY<FLOAT64>,
  source_mode STRING NOT NULL
)
PARTITION BY TIMESTAMP_TRUNC(observed_at, DAY)
CLUSTER BY chosen_response, outcome
OPTIONS (
  partition_expiration_days = 365,
  require_partition_filter = TRUE,
  description = 'Synthetic Decision Twin precedents for bounded decision-shape vector retrieval.'
);

DELETE FROM `{{PROJECT_ID}}.driftline_product.decision_twin_precedents`
WHERE source_mode = 'synthetic_precedent_fixture'
  AND observed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
  AND observed_at < TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);

INSERT INTO `{{PROJECT_ID}}.driftline_product.decision_twin_precedents`
  (observed_at, precedent_id, title, chosen_response, outcome, lesson,
   decision_vector, source_mode)
VALUES
  (CURRENT_TIMESTAMP(), 'precedent-permission-preview',
   'Role-policy preview before an enterprise rollout', 'segment', 'validated',
   'Segmenting protected enterprise accounts while testing a policy preview preserved the smaller-team gain without widening the permission failure.',
   [0.08, 0.10, 1.0, 1.0], 'synthetic_precedent_fixture'),
  (CURRENT_TIMESTAMP(), 'precedent-global-rollback',
   'Global rollback after a cross-segment reliability failure', 'rollback', 'validated',
   'A global rollback was warranted only after the same severe failure appeared across every measured segment.',
   [-0.05, 0.90, 0.0, 0.8], 'synthetic_precedent_fixture'),
  (CURRENT_TIMESTAMP(), 'precedent-launch-defer',
   'Launch deferred when the evidence floor was not met', 'defer', 'inconclusive',
   'Deferral created value only because the team named the missing evidence and a fixed date for returning to the decision.',
   [0.0, 0.35, 0.2, 0.9], 'synthetic_precedent_fixture');
