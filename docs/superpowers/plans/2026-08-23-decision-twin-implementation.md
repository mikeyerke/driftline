# Driftline Decision Twin — Implementation Plan

Design: `docs/superpowers/specs/2026-08-23-decision-twin-design.md`

## Delivery principle

Ship one complete, deterministic, judge-visible decision loop before adding live
infrastructure adapters. The public demo must work without paid credentials;
authenticated Google services enhance the same contracts without changing them.

## Task 1 — Domain contracts and deterministic fixture

**Files**

- Create `backend/app/decision_twin.py`
- Create `backend/tests/test_decision_twin.py`

**Work**

1. Write failing tests for evidence provenance, citation validation, council
   disagreement, counterfactual determinism, experiment completeness, outcome
   evaluation, and exclusive decision reopening.
2. Add strict Pydantic contracts for evidence nodes, council positions,
   synthesis, options, experiment plan, outcome observation, and decision case.
3. Add one realistic onboarding-regression fixture with text, image metadata,
   aggregate usage, support themes, and a roadmap commitment.
4. Implement deterministic fallback council results and graph validation.
5. Run the focused test file.

## Task 2 — Council orchestration and policy

**Files**

- Create `backend/app/product_council.py`
- Extend `backend/app/trace_eval.py`
- Extend `backend/tests/test_trace_eval.py`
- Extend `backend/tests/test_decision_twin.py`

**Work**

1. Define five bounded specialist response schemas.
2. Configure read-only Google ADK agents using the existing Gemini model and
   response schemas; no tools or write authority.
3. Run specialists independently and synthesize only after citation validation.
4. Provide an explicitly labeled deterministic demo fallback.
5. Add deterministic policy checks for citation coverage, challenger presence,
   disagreement preservation, falsifiability, and alternatives.
6. Add trace-eval cases for those contracts.

## Task 3 — API, durable state, and reopening

**Files**

- Extend `backend/app/api.py`
- Extend `backend/app/persistence.py`
- Extend `backend/tests/test_api.py`

**Work**

1. Add endpoints to create/read the public decision-twin demo.
2. Add a human approval endpoint that validates the current synthesis hash and
   complete experiment contract.
3. Add an outcome endpoint that appends an observation and performs an
   exclusive generation transition when a guardrail is invalidated.
4. Persist every generation and event through the existing backend abstraction.
5. Ensure public execution remains packet-safe and idempotent.
6. Test stale synthesis, duplicate approval/outcome, invalid observations,
   reopening lineage, and tenant/public boundaries.

## Task 4 — Decision Room

**Files**

- Create `frontend/src/components/DecisionRoom.jsx`
- Create `frontend/src/components/EvidenceCouncil.jsx`
- Create `frontend/src/components/CounterfactualCompare.jsx`
- Create `frontend/src/components/LearningReceipt.jsx`
- Extend `frontend/src/api.js`
- Extend `frontend/src/App.jsx`
- Extend `frontend/src/styles.css`
- Extend frontend contract tests

**Work**

1. Add Judge Mode entry to the Decision Twin case.
2. Render the four-beat narrative: decision at risk, evidence disagreement,
   recommended move, and learning receipt.
3. Keep raw hashes and infrastructure metadata behind disclosure.
4. Support keyboard option selection, live status, reduced motion, 14px minimum
   body copy, and mobile/720p-safe reflow.
5. Let the judge approve the recommended experiment and trigger a pinned later
   outcome that reopens the same decision.
6. Add literal/interaction contracts for the full story.

## Task 5 — BigQuery adapter and Google deployment controls

**Files**

- Create `backend/app/product_analytics.py`
- Create `backend/tests/test_product_analytics.py`
- Extend `requirements.txt` or project dependency manifest only if required
- Extend `scripts/deploy.sh`
- Extend deployment documentation and sample environment

**Work**

1. Implement an allowlisted aggregate query contract with parameterized inputs,
   dry-run support, and maximum bytes billed.
2. Keep BigQuery behind `DECISION_TWIN_BIGQUERY_ENABLED=false` by default.
3. Use fixtures when disabled and fail closed for a signed request that claims
   live analytics without verified configuration.
4. Add Cloud Run max-instance, timeout, token/call quota, and logging controls.
5. Document budget alerts as advisory and application quotas as enforcement.

## Task 6 — Quality, security, and PR update

**Work**

1. Run Ruff and all backend tests.
2. Run the frontend production build and contract tests.
3. Run `git diff --check` and the security diff scan.
4. Update README, architecture diagram source, judge scorecard, demo script, and
   production verifier.
5. Push the exact tested tree to the existing PR branch.
6. Confirm GitHub Actions is green and the PR remains clean/mergeable.

## Task 7 — Production, validation, and demo

**Work**

1. From an authenticated Google Cloud environment, confirm the project and
   billing account before provisioning.
2. Apply app-level quotas, Cloud Run caps, BigQuery byte limits, storage
   lifecycle, and billing alerts.
3. Deploy the exact green SHA and verify health, council, approval, outcome,
   reopening, trace evaluation, and receipts.
4. Run 6–8 real participant sessions; never fabricate missing sessions.
5. Summarize results and update the demo only with measured claims.
6. Record the 3:45–3:50 final video and verify backend/cloud proof.

Registration and Devpost submission are not authorized by this plan.

