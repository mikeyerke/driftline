# Remote launch checklist

## Google Cloud

1. Confirm the active project is exactly driftline-hackathon-2026 before every
   mutation; never reuse an existing project.
2. Confirm billing and enable only Cloud Build, Cloud Run, Artifact Registry,
   Vertex AI, Firestore, and budget APIs required by the deployment.
3. Create a Docker Artifact Registry repository named driftline in
   us-central1 with Driftline labels.
4. Create a Firestore Native database in us-central1 if the new project has
   none.
5. Create the dedicated runtime service account and grant only Vertex AI User
   and Datastore User.
6. Create the $10 project budget with low-threshold alerts and record it in
   docs/RESOURCE_INVENTORY.md.
7. Run gcloud builds submit --project=driftline-hackathon-2026
   --config cloudbuild.yaml . from the repository root.
8. Open the Cloud Run URL in a logged-out browser and exercise scan, evidence,
   approval, undo, and the live agent endpoint.

## GitHub

1. Review the staged source and scan for credentials, tokens, environment
   files, generated dependencies, and local build output.
2. Create the public repository named driftline under the existing account.
3. Push the tested baseline and add the final Cloud Run URL to README.md.
4. Confirm the public repository accurately describes the deployed revision.

## Demo and submission

1. Capture the four-minute flow in DEMO_SCRIPT.md at 1080p.
2. Add captions and upload a publicly visible video using the entrant's
   account; unlisted YouTube videos do not satisfy the official rules.
3. Replace every pending link in DEVPOST.md with a verified public URL.
4. Select only Taskmaster and disclose the earlier concept/source package as
   required by the new-project rule.
5. Verify entrant identity, eligibility, category selection, and required
   disclosures before the final submission action.
