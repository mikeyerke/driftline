# Driftline resource inventory

This inventory is intentionally scoped to the isolated Google Cloud project
`driftline-hackathon-2026`. The active gcloud configuration was checked during
the release run:

```text
core.account: mikeyerke@gmail.com
core.project: driftline-hackathon-2026
project number: 724959673622
```

Before any future mutation, verify the target explicitly:

```bash
gcloud config set project driftline-hackathon-2026
test "$(gcloud config get-value project 2>/dev/null)" = driftline-hackathon-2026
```

## Resources

| Resource | Name / scope | Verified status | Labels / notes |
| --- | --- | --- | --- |
| Google Cloud project | `driftline-hackathon-2026` (`724959673622`) | Active, created 2026-08-18 | `app=driftline`, `environment=hackathon`, `hackathon=all-things-agentic` |
| Billing account | `billingAccounts/01B9B8-321AE7-ECA02B` | Free trial linked and billing enabled | Trial credit `$300`, start 2026-08-18, end 2026-11-17; paid-account activation was not enabled |
| Billing budget | `77e23b49-d3b8-45de-91b7-f0c6172dfd9b` | Active `$10 USD` monthly guardrail filtered to project 724959673622 | Current-spend thresholds 25%, 50%, 75%, 90%, 100%; no custom notification channel created |
| Cloud Run service | `driftline` in `us-central1` | Ready, revision `driftline-00002-7ld`, 100% traffic | Public URL: https://driftline-xvxczqg62a-uc.a.run.app/; min 0, max 1, 1 CPU, 512 MiB, concurrency 20, timeout 300s |
| Cloud Run runtime identity | `driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Project roles: `roles/aiplatform.user`, `roles/datastore.user` |
| Cloud Build identity | `driftline-build@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Build, deploy, service-usage roles; can impersonate only the Driftline runtime identity |
| Artifact Registry | `driftline` Docker repo in `us-central1` | Active | Image: `us-central1-docker.pkg.dev/driftline-hackathon-2026/driftline/driftline:2e07f172-3683-4b7b-868c-08c4984c17c5`; digest `sha256:5dce7a41ce9e4529bda391b42a90399edacd7c4bd5721fd378b44e36738871d3` |
| Firestore database | `(default)` Native in `us-central1` | Active, directly write/read verified | Driftline workflow documents and `audit_events` subcollections only |
| Cloud Build logs bucket | `gs://724959673622-us-central1-cloudbuild-logs` | Created by regional Cloud Build | Labels: `app=driftline`, `environment=build`, `hackathon=all-things-agentic` |
| Cloud Build source bucket | `gs://driftline-hackathon-2026_us-central1_cloudbuild` | Created by regional Cloud Build | Labels: `app=driftline`, `environment=build`, `hackathon=all-things-agentic` |
| Cloud Build compatibility bucket | `gs://driftline-hackathon-2026_cloudbuild` | Created by Cloud Build | Labels: `app=driftline`, `environment=build`, `hackathon=all-things-agentic` |
| GitHub repository | `https://github.com/mikeyerke/driftline` | Public, source matches deployed revision | Separate repository under existing user account; no organization created |

Cloud Build ID `2e07f172-3683-4b7b-868c-08c4984c17c5` completed successfully in
`us-central1`. Its Docker image digest is the exact image serving Cloud Run.
Cloud Build and Cloud Run may enable Google-managed dependency APIs in addition
to the six explicitly requested application APIs; no Driftline code uses the
unrelated managed services. No existing project, bucket, database, service
account, API key, repository, or environment variable is reused.

## Verified live evidence

- `GET /health` returned `{"status":"ok","service":"driftline-agent","persistence":"firestore"}`.
- Public browser QA passed at desktop and 390px widths with no horizontal overflow.
- Scan, evidence modal/hash, artifact selection, approval, publish/queue/schedule,
  undo, and activity audit states passed against the public service.
- `/api/agent/run` returned `model=gemini-3.5-flash`,
  `execution_mode=google_adk`, and the allowlisted tools
  `inspect_source_change` and `get_workflow_state`.
- Firestore REST inspection found the live workflow parent and five audit
  documents for the latest live ADK invocation. The approval/undo run produced
  eight audit documents.
- Cloud Run revision logs showed successful requests and no application
  exceptions; the browser reload produced no console exceptions or log entries.

The public live-agent endpoint is configured for at most 10 calls per hour and a
2,000-character query. Demo starts and approval/undo writes share a 30-mutation
hourly cap. These are spend guards, not production authentication.

## Cleanup and disablement

The following commands target only the Driftline project. Review the inventory
before running destructive commands and never paste credentials or tokens into
the repository:

```bash
PROJECT=driftline-hackathon-2026
REGION=us-central1

gcloud run services delete driftline --project="$PROJECT" --region="$REGION"
gcloud artifacts repositories delete driftline --project="$PROJECT" --location="$REGION"
gcloud storage buckets delete gs://724959673622-us-central1-cloudbuild-logs
gcloud storage buckets delete gs://driftline-hackathon-2026_us-central1_cloudbuild
gcloud storage buckets delete gs://driftline-hackathon-2026_cloudbuild
gcloud firestore databases delete --database='(default)' --project="$PROJECT"
gcloud projects delete "$PROJECT"
```

Project deletion is irreversible and should be the final reviewed action. The
free trial closes automatically on 2026-11-17 unless the full paid account is
activated; do not click the Cloud Console “Activate” upsell while the project
is no longer needed.
