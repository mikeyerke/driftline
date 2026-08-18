# Signed-in launch checklist

## Google Cloud

1. Select or create the project that will own the contest deployment.
2. Confirm billing and enable Cloud Build, Cloud Run, Artifact Registry,
   Vertex AI, and Firestore APIs.
3. Create a Docker Artifact Registry repository named `driftline` in
   `us-central1`.
4. Create a Firestore database in Native mode if the project has none.
5. Grant the Cloud Run service identity Vertex AI User and Datastore User.
6. Run `gcloud builds submit --config cloudbuild.yaml .` from the repository
   root.
7. Open the Cloud Run URL and exercise scan, evidence, approval, undo, and the
   live agent endpoint.

## GitHub

1. Initialize the repository and review the staged source.
2. Create a public repository named `driftline`.
3. Push the tested baseline and add the final Cloud Run URL to `README.md`.
4. Confirm no credentials, generated dependency folders, or local environment
   files are present.

## Demo and submission

1. Capture the five-minute flow in `DEMO_SCRIPT.md` at 1080p.
2. Add captions and upload an unlisted video using the entrant's account.
3. Replace any remaining generic claims in `DEVPOST.md` with measured facts.
4. Add repository, live demo, architecture, and video links to Devpost.
5. Verify entrant identity, eligibility, category selections, and required
   disclosures before the final submission action.
