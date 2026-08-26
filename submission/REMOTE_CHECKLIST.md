# Final release and submission checklist

Status: operator checklist only. Nothing here authorizes a push, merge, Cloud
mutation, registration, upload, publication, or submission.

## 1. Local candidate custody

1. Work from the isolated candidate worktree and record `git rev-parse HEAD`.
2. Move local review MP4s outside the repository; never add them to the release
   commit unless the exact asset has been separately approved for publication.
3. Run `./scripts/verify_release_candidate_local.sh --local-checks`.
4. Review the complete diff, credential scan, generated files, dependency
   changes, submission copy, and architecture asset.
5. Commit only reviewed source and reproducible submission inputs. Confirm
   `git status --short` is empty.

## 2. Public repository custody — requires authorization

1. Push the exact tested candidate to its review branch.
2. Require passing GitHub checks and review the final PR diff.
3. Merge the candidate to public `main` only after explicit authorization.
4. In a clean release worktree, update to that exact merge commit and confirm
   local `HEAD` equals the fresh public `origin/main` tip.
5. Run `./scripts/verify_release_candidate_local.sh --release-candidate`.
   This must fail if the tree is dirty, any local gate fails, the remote is not
   `mikeyerke/driftline`, or the exact public `main` commit differs.
6. Apply the reviewed description, website, and topics from
   `submission/GITHUB_REPOSITORY_METADATA.md`; then open the repository logged
   out and test the README's first-screen links. Repository metadata is a
   separate public mutation and is not authorized by this checklist.

## 3. Google Cloud release — requires authorization

1. Confirm the active project is exactly `driftline-hackathon-2026`; never use
   another project.
2. Confirm the isolated budget, runtime identity, Artifact Registry, Firestore,
   BigQuery, Tasks, Scheduler, monitoring, and current billing posture.
3. Run only `./scripts/release_and_verify.sh`. Its local/public-main preflight
   runs before provisioning or deployment.
4. Record the exact merge commit, Cloud Build ID, Cloud Run revision, immutable
   image digest, and 100% traffic result.
5. Require `/health`, Artifact Registry, Cloud Run, the release-bound ADK trace,
   Decision Twin workflow, and production verifier to resolve to that identity.
6. Rerun the logged-out desktop and 390-pixel journeys. Keep approval → outcome
   → internal rollback → generation-2 reopen continuous; require a clean console.
7. Stop and roll back if any identity, live trace, task, policy, browser, or
   error-log gate fails. Do not narrate candidate behavior as live until every
   gate passes.

## 4. Final demo — requires authorization

1. Record the native browser path in `submission/DEMO_SCRIPT.md` at 1080p.
2. Show the working product in the first 10–15 seconds. Do not cut inside the
   approval → outcome → reopen sequence.
3. Use the release architecture only after its candidate badge and pending
   proof language have been replaced with the exact verified release identity.
4. Burn in English captions; reject at 3:56 or longer. Check at 1×, muted, and
   720p for comprehension and small-text legibility.
5. Verify H.264/AAC playback compatibility, loudness, black intervals, secrets,
   customer identifiers, custody labels, final URL, repository, category, and
   Google technology. Show either the Cloud Run console or the live `*.run.app`
   backend in-frame; an architecture diagram or caption alone is insufficient.
6. Scrub the manifest timestamp for the first visible agent action and require
   it by 0:15. Then scrub named-human approval, the bounded action receipt, and
   generation-2 reopen. Require those states to be visibly distinct, with the
   approver cleared and generation-1 lineage preserved after reopening;
   narration alone does not prove the state changes. Affirm the entire take is
   continuous and that sign-up, setup, loading, and title-card waits are absent.
7. Upload publicly to YouTube or Vimeo only after entrant approval. The working
   rules snapshot says an unlisted video is insufficient; verify visibility in
   a fresh logged-out browser.

## 5. Devpost — requires authorization

1. Sign in, then perform the read-only actual-form audit described in
   `submission/DEVPOST_FORM_AUDIT.md`; do not join, create, save, upload, accept,
   or submit during that audit.
2. Reconcile exact labels, limits, selectors, and required confirmations into
   `devpost-submission.md` and rerun the packet verifier.
3. Replace only the approved video/social placeholders in
   `devpost-submission.md`; rerun `./scripts/verify_submission_packet.sh`.
4. Select only Taskmaster and enter Google ADK, the August 18 implementation
   start, repo, hosted URL, architecture, and originality/source disclosure.
5. Recheck entrant identity, eligibility, rules, terms, privacy consent, links,
   category, rendered copy, screenshots, and the exact public video.
6. Preserve the distinction between engineering proof, PM evidence, and an
   actual paying customer. Never add an outcome, quote, or attribution without
   its evidence and separate consent.
7. Submit only after a final explicit authorization of the rendered entry.

## 6. Freeze after submission

Record the submitted commit, deployment identity, video URL, architecture,
screenshots, Devpost URL, and submission timestamp. Freeze those artifacts
until judging ends unless the rules require a correction; document any allowed
change rather than silently replacing proof.
