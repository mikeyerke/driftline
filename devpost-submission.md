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
| Submitter type | Individual |
| Country | United States |
| Category | Taskmaster |
| Organization | N/A — individual entrant |
| Project start date | August 18, 2026 |
| Repository | https://github.com/mikeyerke/driftline |
| Hosted application | https://driftline-ops.web.app/ |
| Reproducible testing | Yes |
| Google agent framework | Google Agent Development Kit (ADK) |
| Google Cloud services | Cloud Run; Firestore; BigQuery |
| Additional Google Cloud services described in entry | Vertex AI; Cloud Tasks; Cloud Scheduler; Cloud Storage; Secret Manager; Cloud Build; Artifact Registry |
| Model | Gemini 3.5 Flash via Vertex AI |
| Architecture upload | `submission/assets/driftline-decision-twin-architecture.png` |
| Demo video | **ENTRANT TODO:** public YouTube or Vimeo URL, 4:00 maximum |
| Bonus build content | https://github.com/mikeyerke/driftline/blob/main/submission/BUILD_STORY.md |
| Social post | **ENTRANT TODO:** publish an approved draft from `submission/SOCIAL_POST_DRAFTS.md` and paste the public URL |
| Startup prize | Leave blank unless the entrant independently meets and confirms its eligibility requirements |

## Short description

Driftline is a Decision Twin for consequential product calls. Five independent
Google ADK specialists use Gemini 3.5 Flash to evaluate bounded usage,
customer, strategy, and feasibility evidence, preserve dissent, and compare
ship, rollback, segment, or defer. A named human alone approves a falsifiable
experiment. BigQuery supplies privacy-thresholded aggregates, Firestore keeps
the decision lineage, and a measured outcome can reopen the same case without
erasing the original reasoning.

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
- Record and publish the final public video at 3:45 or shorter.
- Approve and publish one optional social draft if pursuing that bonus.
- Review the rendered project, attached architecture image, links, and category.
- Explicitly confirm the final Devpost submission action.
