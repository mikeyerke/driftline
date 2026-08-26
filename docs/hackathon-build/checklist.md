# Driftline autonomous winning checklist

Mode: autonomous
Verification: enabled at release checkpoints; no participant pause for local checks
Comprehension checks: disabled
Git cadence: one focused planning/package commit, then one final proof commit if needed
Check-in cadence: report blockers requiring identity, publication, or final submission
Wow moment: signed evidence-bound Jira action, idempotent reuse, and scoped reversal

- [x] **1. Reconcile the exact release truth**
  Spec ref: `spec.md > Release contract`
  What to build: Compare repository head, serving SHA, live health, current proof records, and every submission claim; remove stale or contradictory release statements.
  Acceptance: One canonical current-release section remains and all public claims are reproducible.
  Verify: `curl /health`, `git diff <serving-sha>..HEAD`, and repository claim search.

- [x] **2. Pass the complete local quality gate**
  Spec ref: `spec.md > Release contract`
  What to build: Run backend tests/lint, trace evaluation, frontend build/contract, dependency audit, shell validation, and repository hygiene.
  Acceptance: Every required command passes without weakening a test.
  Verify: Commands in `docs/DEFINITION_OF_DONE.md`.

- [x] **3. Verify the public judge journey**
  Spec ref: `spec.md > Judge surface — PRD Epic 5`
  What to build: Inspect the deployed first viewport and one complete public workflow for clarity, accessibility, console errors, evidence, approval, and reversal.
  Acceptance: A judge can reach and understand the core action without credentials.
  Verify: Browser DOM/screenshot review plus public live-agent and approval/undo scripts.

- [x] **4. Lock the Taskmaster narrative**
  Spec ref: `scope.md > What we are shipping`
  What to build: Rewrite the canonical Devpost copy around one Taskmaster proof-of-action story; remove duplicated history and secondary connector detail from the main narrative.
  Acceptance: The first 300 words clearly state problem, autonomous action, Google technology, human gate, real Jira proof, and limitations.
  Verify: Rubric-by-rubric read against the official 40/30/30 criteria.

- [x] **5. Produce the architecture upload**
  Spec ref: `spec.md > Submission artifacts`
  What to build: Create an exact, judge-readable PNG showing source/Cloud Tasks/ADK+Gemini/policy/Firestore/signed Jira/UI boundaries.
  Acceptance: PNG is legible at Devpost preview size and contains no aspirational services.
  Verify: Open the rendered image and compare every node to deployed code/proof.

- [ ] **6. Finalize the sub-four-minute proof-of-action package**
  Spec ref: `spec.md > Demo failure strategy`
  What to build: Tighten the script to a 3:45 target, create matching shot list/captions, and clearly separate public packet-safe and signed Jira action lanes.
  Acceptance: The plan shows live action and Google Cloud proof before 3:20 and closes by 3:45.
  Verify: Timestamp sum and asset inspection.

- [x] **7. Publish the optional build-content artifact**
  Spec ref: `spec.md > Submission artifacts`
  What to build: Write a concise public build story stating it was created for this hackathon, focused on the evidence/authorization/action architecture.
  Acceptance: Public-repo URL is usable in the bonus-content field after merge.
  Verify: Markdown links and disclosure text pass inspection.

- [x] **8. Create the exact Devpost form packet**
  Spec ref: `spec.md > Submission artifacts`
  What to build: Create `devpost-submission.md` with exact form answers, testing instructions, links, model/framework/services, disclosure, shot list, and only genuine placeholders.
  Acceptance: Every required official field has either final copy or one explicit owner-only TODO.
  Verify: Compare with the live Devpost submission requirements.

- [x] **9. Push the reviewed branch and open one PR**
  Spec ref: `spec.md > Release contract`
  What to build: Commit the package, push the branch, open a focused PR, and let GitHub verification complete.
  Acceptance: Public diff is reviewable and all CI checks pass.
  Verify: GitHub PR checks and changed-file audit.

- [ ] **10. Complete Devpost registration, project setup, and handoff**
  Spec ref: `scope.md > Definition of done`
  What to build: Register only after explicit answers/agreements, create or update the Driftline project, attach the thumbnail and final links, and stop before final submission unless Mike explicitly confirms the completed packet.
  Acceptance: Devpost project is complete, registered to Taskmaster, and only final confirmation remains.
  Verify: Live Devpost project read plus official submission requirement check.
