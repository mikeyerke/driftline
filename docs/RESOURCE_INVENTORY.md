# Driftline resource inventory

This inventory is intentionally scoped to the isolated project
driftline-hackathon-2026. No Driftline command should target an existing
project. Before any mutation:

~~~bash
gcloud config set project driftline-hackathon-2026
test "$(gcloud config get-value project 2>/dev/null)" = driftline-hackathon-2026
~~~

## Resources

The isolated project, free-tier Firestore database, and dedicated runtime
identity now exist. Cloud Run, Artifact Registry, and the budget remain blocked
by the missing billing account. Rows marked `blocked` are not claims that the
resource exists.

| Resource | Name / scope | Status | Driftline label |
| --- | --- | --- |
| Google Cloud project | driftline-hackathon-2026 (number 724959673622) | created 2026-08-18 | app=driftline,environment=hackathon,hackathon=all-things-agentic |
| Cloud Run service | driftline in us-central1 | blocked: billing required | app=driftline,environment=production,hackathon=all-things-agentic |
| Artifact Registry | driftline in us-central1 | blocked: billing required | app=driftline,environment=production,hackathon=all-things-agentic |
| Firestore database | (default) in us-central1 | created 2026-08-18, free tier | project-scoped |
| Runtime service account | driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com | created 2026-08-18 | app=driftline,role=runtime |
| Budget | $10 USD project budget with low thresholds | blocked until billing is linked | app=driftline,budget=10-usd |

Enabled in this project only: `aiplatform.googleapis.com`,
`firestore.googleapis.com`, and `billingbudgets.googleapis.com`. A direct
Vertex `gemini-3.5-flash` request returned `BILLING_DISABLED`; enabling Cloud
Run, Artifact Registry, and Cloud Build returned the same project-billing
precondition. The runtime identity has only `roles/datastore.user` and
`roles/aiplatform.user` at this checkpoint. No service-account key was created.

The intended deployment uses Cloud Run scale-to-zero and a bounded maximum
instance count. Firestore was directly write/read/delete verified with a
temporary Driftline-only document; the document was removed after the check.
Once deployed, Firestore will be used only for Driftline workflow documents and
their audit_events subcollections. No existing bucket,
database, service account, API key, repository, or environment variable is
reused. The public live-agent endpoint is configured for at most 10 calls per
hour and a 2,000-character query. Demo starts and approval/undo writes share a
30-mutation hourly cap. These are spend guards, not authentication.

## Evidence and cleanup

Record the project number, Cloud Run URL, Artifact Registry image digest,
Firestore database location, service-account email, and budget name here after
creation. Do not record access tokens, private keys, or billing credentials.

To disable the application without touching another project:

~~~bash
gcloud run services update driftline --project=driftline-hackathon-2026 \
  --region=us-central1 --max=0
gcloud run services delete driftline --project=driftline-hackathon-2026 \
  --region=us-central1
gcloud artifacts repositories delete driftline --project=driftline-hackathon-2026 \
  --location=us-central1
gcloud firestore databases delete '(default)' \
  --project=driftline-hackathon-2026
~~~

The final project-level deletion command, if ever needed, must be reviewed
against this inventory first because it is irreversible:

~~~bash
gcloud projects delete driftline-hackathon-2026
~~~
