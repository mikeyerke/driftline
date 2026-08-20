#!/usr/bin/env bash
set -euo pipefail

# Create empty, deterministic Secret Manager containers for one tenant.
# Credential values are intentionally not accepted here. Add a provider token
# through a separate Secret Manager workflow, then use the signed owner
# binding endpoint to verify and activate the metadata-only binding.

PROJECT="${DRIFTLINE_PROJECT:-driftline-hackathon-2026}"
EXPECTED_PROJECT="driftline-hackathon-2026"
RUNTIME_SA="${DRIFTLINE_RUNTIME_SERVICE_ACCOUNT:-driftline-runtime@${EXPECTED_PROJECT}.iam.gserviceaccount.com}"
TENANT="${1:-}"

if [[ "$(gcloud config get-value project 2>/dev/null)" != "${EXPECTED_PROJECT}" ]]; then
  echo "Refusing to target a non-Driftline gcloud project." >&2
  exit 1
fi
if [[ "${PROJECT}" != "${EXPECTED_PROJECT}" ]]; then
  echo "DRIFTLINE_PROJECT must remain ${EXPECTED_PROJECT}." >&2
  exit 1
fi
if [[ ! "${TENANT}" =~ ^[a-z0-9][a-z0-9-]{1,62}$ ]]; then
  echo "Usage: bash scripts/provision_tenant_connector_secrets.sh TENANT_ID" >&2
  exit 2
fi

for connector in jira confluence slack github salesforce; do
  secret="driftline-tenant-${TENANT}-${connector}"
  if gcloud secrets describe "${secret}" --project="${PROJECT}" >/dev/null 2>&1; then
    echo "exists ${secret}"
  else
    gcloud secrets create "${secret}" --project="${PROJECT}" --replication-policy=automatic --labels="app=driftline,environment=production,hackathon=all-things-agentic,tenant=${TENANT},connector=${connector}" >/dev/null
    echo "created ${secret}"
  fi
  gcloud secrets update "${secret}" --project="${PROJECT}" --update-labels="app=driftline,environment=production,hackathon=all-things-agentic,tenant=${TENANT},connector=${connector}" >/dev/null
  gcloud secrets add-iam-policy-binding "${secret}" --project="${PROJECT}" --member="serviceAccount:${RUNTIME_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null
done

# Optional break-glass signer for this tenant. Normal operators should use
# Google OIDC; this deterministic secret prevents one deployment-wide HMAC key
# from authorizing every tenant. The script creates only the container; add a
# random value through a separate Secret Manager workflow.
signer_secret="driftline-tenant-operator-${TENANT}"
if gcloud secrets describe "${signer_secret}" --project="${PROJECT}" >/dev/null 2>&1; then
  echo "exists ${signer_secret}"
else
  gcloud secrets create "${signer_secret}" --project="${PROJECT}" --replication-policy=automatic --labels="app=driftline,environment=production,hackathon=all-things-agentic,tenant=${TENANT},kind=operator-signing" >/dev/null
  echo "created ${signer_secret}"
fi
gcloud secrets update "${signer_secret}" --project="${PROJECT}" --update-labels="app=driftline,environment=production,hackathon=all-things-agentic,tenant=${TENANT},kind=operator-signing" >/dev/null
gcloud secrets add-iam-policy-binding "${signer_secret}" --project="${PROJECT}" --member="serviceAccount:${RUNTIME_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null

cat <<EOF
Provisioned deterministic Secret Manager containers for tenant ${TENANT}.
No credential values were accepted or changed.
Next: add each provider value through Secret Manager, then call the signed
owner binding route for each connector. A binding stays pending until its
secret has a readable version. For break-glass signed operators, add a random
value to ${signer_secret}; normal operator traffic should use Google OIDC.
EOF
