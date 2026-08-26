#!/usr/bin/env bash
set -euo pipefail

PROJECT="driftline-hackathon-2026"
BILLING_ACCOUNT="01B9B8-321AE7-ECA02B"
BUDGET_ID="77e23b49-d3b8-45de-91b7-f0c6172dfd9b"

if [[ "$(gcloud config get-value project 2>/dev/null)" != "${PROJECT}" ]]; then
  echo "Refusing to update a non-Driftline gcloud project." >&2
  exit 2
fi

gcloud billing budgets update "${BUDGET_ID}" \
  --billing-account="${BILLING_ACCOUNT}" \
  --display-name='Driftline $300 Guardrail' \
  --budget-amount=300USD \
  --clear-threshold-rules \
  --add-threshold-rule=percent=0.083333 \
  --add-threshold-rule=percent=0.25 \
  --add-threshold-rule=percent=0.5 \
  --add-threshold-rule=percent=0.75 \
  --add-threshold-rule=percent=0.95 \
  --add-threshold-rule=percent=1.0 \
  --quiet

gcloud billing budgets describe "${BUDGET_ID}" \
  --billing-account="${BILLING_ACCOUNT}" \
  --format='yaml(displayName,amount,budgetFilter,thresholdRules,notificationsRule)'
