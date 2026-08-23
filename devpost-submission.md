# Driftline — Devpost submission packet

Status: form-ready except for the entrant-owned public video/social URLs and
registration answers called out below. Do not submit until the entrant reviews
the rendered Devpost project and explicitly confirms the final action.

## Core fields

| Devpost field | Exact answer |
| --- | --- |
| Project name | Driftline |
| Tagline | Evidence-bound change becomes reversible owner action. |
| Submitter type | Individual |
| Country | United States |
| Category | Taskmaster |
| Organization | N/A — individual entrant |
| Project start date | August 18, 2026 |
| Repository | https://github.com/mikeyerke/driftline |
| Hosted application | https://driftline-xvxczqg62a-uc.a.run.app/ |
| Reproducible testing | Yes |
| Google agent framework | Google Agent Development Kit (ADK) |
| Google Cloud services | Cloud Run; Firestore |
| Additional Google Cloud services described in entry | Vertex AI; Cloud Tasks; Cloud Scheduler; Cloud Storage; Secret Manager; Cloud Build; Artifact Registry |
| Model | Gemini 3.5 Flash via Vertex AI |
| Architecture upload | `submission/assets/driftline-architecture.png` |
| Demo video | **ENTRANT TODO:** public YouTube or Vimeo URL, 4:00 maximum |
| Bonus build content | https://github.com/mikeyerke/driftline/blob/main/submission/BUILD_STORY.md |
| Social post | **ENTRANT TODO:** publish an approved draft from `submission/SOCIAL_POST_DRAFTS.md` and paste the public URL |
| Startup prize | Leave blank unless the entrant independently meets and confirms its eligibility requirements |

## Short description

Driftline turns a monitored public-source change into evidence-linked,
human-governed owner action. Google ADK and Gemini 3.5 Flash interpret an
immutable before/after diff, map affected work, and draft cited decision
options. Deterministic policy—not the model—controls authorization. The public
lane proves the complete evidence, approval, packet, audit, and reversal loop;
the signed tenant lane additionally proves one least-privilege, idempotent, and
reversible Jira action.

## Full submission description

Use [`submission/DEVPOST.md`](submission/DEVPOST.md) verbatim for the Devpost
story fields. It contains the inspiration, product behavior, Google technology,
architecture and safety boundaries, challenges, accomplishments, data-source
disclosure, learnings, testing instructions, and next steps.

## Problem, solution, and why it matters

**Problem:** A pricing or positioning change can make comparison pages,
battlecards, deal-desk rules, and executive briefs stale at once. Alerts expose
the change but leave the consequential coordination and accountability to
people.

**Solution:** Driftline creates immutable evidence, uses Gemini through ADK to
map affected work and draft bounded options, enforces deterministic approval,
then creates evidence-linked owner action with durable audit and rollback.

**Why it matters:** The valuable unit is not another notification or answer. It
is a safe, accountable transition from observed change to completed work.

## AI use

Gemini 3.5 Flash on Vertex AI performs structured evidence interpretation,
impact analysis, and Decision Copilot drafting. Google ADK coordinates two
allowlisted read/inspect tools. The model has no approval tool and cannot widen
source, tenant, connector, or action scope. Pydantic schemas, evidence-hash
checks, materiality rules, allowlists, approval policy, idempotency, tenant
membership, and rollback semantics remain deterministic code.

## Key features

- Bounded source registry with cadence and freshness health
- Immutable before/after evidence and full SHA-256 provenance
- Durable Cloud Tasks jobs and Firestore workflow recovery
- Gemini impact mapping across four named owner surfaces
- Evidence-cited decision options with tradeoffs and rollback
- Deterministic human approval outside model authority
- Public packet-safe evaluation without credentials
- Signed, tenant-scoped Jira create/reactivate/reverse proof
- Idempotent action reuse and append-only reversal history
- Fourteen-case trace evaluation for safety and usefulness

## Architecture

The browser and API run on Cloud Run. Cloud Tasks dispatches asynchronous ADK
work. Gemini 3.5 Flash on Vertex AI interprets allowlisted evidence through two
read-only tools. Deterministic policy validates identity, evidence, scope, and
approval before either the credential-free packet lane or the authenticated
Jira lane can act. Firestore persists jobs, workflows, traces, action state, and
audit history; Secret Manager holds tenant-scoped connector credentials. The
upload-ready diagram is
[`submission/assets/driftline-architecture.png`](submission/assets/driftline-architecture.png).

## Reproducible testing instructions

1. Open https://driftline-xvxczqg62a-uc.a.run.app/ while logged out.
2. Leave **Competitor pricing snapshot** selected and click **Run live agent**.
3. Wait for **Human approval required**.
4. Inspect **Evidence diff**, **Open evidence**, **Agent trace**, the impact map,
   and an artifact detail row.
5. Select an option and click **Approve action plan**.
6. Open the packet and activity history. Confirm the public lane states
   `External systems changed: No`.
7. Click **Reopen decision** and confirm reversed owner-action history and a
   return to the approval gate.
8. Open `/health` and `/api/ops/summary` to verify the serving SHA, build,
   model, persistence, async jobs, policy, and source-health posture.

Repository verification:

```bash
cd backend
uv sync --locked --extra dev
uv run ruff check .
uv run pytest -q
cd ..
./scripts/verify_trace_eval.sh
cd frontend
npm ci
npm run build
cd ..
./scripts/verify_frontend_contract.sh
./scripts/verify_live_agent.sh
./scripts/verify_public_approval_undo.sh
```

## Demo and screenshot plan

Use [`submission/DEMO_SCRIPT.md`](submission/DEMO_SCRIPT.md) as the 3:45
recording script. Required sequence: live hook, scan, evidence/hash, impact map,
deterministic gate, signed Jira action and reversal, visible Cloud proof,
architecture close. Suggested stills are documented in
[`submission/assets/README.md`](submission/assets/README.md).

## Truthful proof and disclosure

The live release serves repository-head Git SHA
`63d96995808c8b1a891abd16682d645db19986fb` from Cloud Build
`92a1fcac-7d63-4c73-8306-0dcbe18c2466`. In the signed operator lane, a hosted
Gemini/ADK workflow reached approval, reactivated Jira marker `KAN-19`, and then
reversed only Driftline-owned state; both operations returned HTTP 200. This is
engineering proof from an isolated project, not customer outcome or ROI proof.

Implementation began August 18, 2026 during the contest period. Earlier product
ideation and a source package are disclosed and are not presented as
contest-period implementation. The project uses the open-source dependencies
identified in its lockfiles and repository notices.

## Entrant-owned finalization

- Confirm registration answers, eligibility, official rules, Devpost terms,
  privacy consent, and the optional marketing answer.
- Record and publish the final public video at 3:45 or shorter.
- Approve and publish one optional social draft if pursuing that bonus.
- Review the rendered project, attached architecture image, links, and category.
- Explicitly confirm the final Devpost submission action.
