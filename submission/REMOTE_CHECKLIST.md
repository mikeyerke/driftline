# Remote launch checklist

## Google Cloud

1. Confirm the active project is exactly driftline-hackathon-2026 before every
   mutation; never reuse an existing project.
2. Confirm billing and the isolated project. Cloud Build, Cloud Run, Artifact
   Registry, Vertex AI, Firestore, and budget APIs are enabled there; do not
   switch the active project to an existing application.
3. Create a Docker Artifact Registry repository named driftline in
   us-central1 with Driftline labels.
4. Create a Firestore Native database in us-central1 if the new project has
   none.
5. Create the dedicated runtime service account and grant only Vertex AI User
   and Datastore User.
6. Confirm the existing `$10` project-filtered budget with 25/50/75/90/100%
   current-spend thresholds in docs/RESOURCE_INVENTORY.md.
7. The verified release build is Cloud Build
   `2e07f172-3683-4b7b-868c-08c4984c17c5`, serving revision
   `driftline-00002-7ld`.
8. Open https://driftline-xvxczqg62a-uc.a.run.app/ in a logged-out browser and
   exercise scan, evidence, approval, undo, and the live agent endpoint.

## GitHub

1. Review the staged source and scan for credentials, tokens, environment
   files, generated dependencies, and local build output.
2. Create the public repository named driftline under the existing account.
3. Push the tested baseline with the verified Cloud Run URL in README.md.
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
