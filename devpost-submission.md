# Driftline — Devpost submission packet

Status: draft-ready, not release-ready or form-ready. The local candidate must
be released and reverified before its behavior can be presented as live; the
entrant-owned public video and registration answers also remain open. Do not
publish or submit without explicit entrant approval.

## Core fields

| Devpost field | Exact answer |
| --- | --- |
| Project name | Driftline |
| Tagline | Contradictory evidence becomes a reversible experiment—and the outcome can reopen the decision. |
| Submitter type | Individuals |
| Country | United States |
| Category | Taskmaster |
| Organization | N/A — individual entrant |
| Project start date | 08-18-26 |
| Repository | https://github.com/mikeyerke/driftline |
| Hosted application | https://driftline-ops.web.app/ |
| Reproducible testing | Yes |
| Google SDK | Agent Development Kit (ADK) |
| Google Cloud service selections | Cloud Run; Firestore |
| Additional Google Cloud services described in entry | Firebase Hosting; BigQuery; Vertex AI; Cloud Tasks; Cloud Scheduler; Cloud Storage; Secret Manager; Cloud Build; Artifact Registry |
| Google AI model | Gemini 3.5 Flash via Vertex AI (global endpoint) |
| Originality disclosure | **OWNER GATE:** inspect the pre-contest source package and select the factually correct disclosure branch in `submission/ORIGINALITY_PROVENANCE.md`; enumerate any incorporated implementation material rather than relying on the repository date. |
| Private testing instructions | Open https://driftline-ops.web.app/ while logged out. Click **Run the decision workflow**; inspect the five cited agents and disagreement; enter a review name; approve the segmented experiment; then stop clicking. Verify that Cloud Tasks reopens generation 2 with rollback selected, the approver cleared, 7/7 policy checks, and the original lineage preserved. Open https://driftline-ops.web.app/health to confirm the serving SHA and build. No credentials are required. |
| Architecture upload | `submission/assets/driftline-decision-twin-architecture.png` |
| Demo video | **ENTRANT TODO:** public YouTube or Vimeo URL, 4:00 maximum |
| Bonus build content | **ENTRANT TODO:** publish the reviewed Decision Twin story from `submission/BUILD_STORY.md`, then paste its verified public URL; the current public `main` URL serves an older promise-drift story and must not be used. |
| Social post | **ENTRANT TODO:** publish an approved draft from `submission/SOCIAL_POST_DRAFTS.md` and paste the public URL |
| Startup prize | Leave blank unless the entrant independently meets and confirms its eligibility requirements |

## Short description

Product teams lose the reasoning behind a roadmap call just when new evidence
makes the commitment unsafe. Driftline turns one contested call into an
evidence-bound Decision Twin. Five independent Google ADK specialists use Gemini
3.5 Flash to preserve dissent and compare ship, rollback, segment, or defer. A
named human approves one falsifiable experiment; then Cloud Tasks evaluates the
outcome with no second PM prompt. BigQuery supplies privacy-thresholded evidence,
Firestore keeps the lineage, and a breached guardrail reopens the same case
without erasing the original reasoning.

## Judge scan — the first 45 seconds

1. Open the hosted Decision Room and start the pinned onboarding council.
2. Inspect the evidence graph and five cited council positions; pause on the
   strategy and challenger dissent.
3. Compare ship, rollback, segment, and defer, then approve one falsifiable
   experiment as a named human.
4. Stop clicking after approval. Watch the Cloud Tasks monitor evaluate the
   bounded measurement and reopen the same case as generation 2 with its prior
   approval and experiment lineage intact.

The differentiator is not another summary. Driftline makes disagreement,
authority, falsifiability, and outcome learning inspectable in one live loop.

## Full submission description

Use [`submission/DEVPOST.md`](submission/DEVPOST.md) verbatim for the Devpost
story fields. It contains the inspiration, product behavior, Google technology,
architecture and safety boundaries, challenges, accomplishments, data-source
disclosure, learnings, testing instructions, and next steps.

## Custody and verification

The authoritative narrative, current production identity, testing path, Google
Cloud architecture, safety boundaries, and disclosure live in
[`submission/DEVPOST.md`](submission/DEVPOST.md). Do not duplicate those fields
from older drafts. At this checkpoint, production is the release identified in
that file; the internal-allocation card and authored custom measurement
contract remain an unreleased local candidate.

Use [`submission/DEMO_SCRIPT.md`](submission/DEMO_SCRIPT.md) for the final
continuous recording and [`submission/assets/README.md`](submission/assets/README.md)
for approved media custody. The final take is invalid unless public `main`,
`/health`, Cloud Run, Cloud Build, the image digest, live trace, and browser
proof all resolve to the same released candidate.

## Entrant-owned finalization

- Confirm registration answers, eligibility, official rules, Devpost terms,
  privacy consent, and the optional marketing answer.
- Resolve the source-package attestation in
  `submission/ORIGINALITY_PROVENANCE.md`; do not submit the generic draft as a
  final originality answer.
- Record and publish the final public video from the canonical 2:58 continuous
  script; reject at 3:56 or longer.
- Approve and publish one optional social draft if pursuing that bonus.
- Review the rendered project, attached architecture image, links, and category.
- Explicitly confirm the final Devpost submission action.
