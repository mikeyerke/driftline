# Devpost form audit

Status: authoritative read-only form audit, August 26, 2026 at 10:00:50 UTC.
Devpost's authenticated MCP returned the live submission requirements for
hackathon `30845` (**All Things Agentic Hackathon**). No registration, project
creation, field entry, draft save, upload, publication, or submission occurred.

## Live deliverable contract

- Submission object: project submission.
- Demo video: required.
- Hosted website: optional, but the host strongly recommends it.
- ZIP upload: not required.
- Repository: required; public or private GitHub, GitLab, or Bitbucket is
  accepted. A private repository must be shared with `testing@devpost.com` and
  `cloudhackathons@google.com`.
- Architecture: required file upload. Accepted extensions are PDF, PPT, PPTX,
  PNG, JPG, and JPEG; maximum size is 36,700,160 bytes (35 MiB).
- Reproducible local or deployment instructions must be in `README.md`.

Driftline's prepared architecture is a 1600 × 900 PNG at 733,971 bytes, safely
inside the live upload contract. The repository has **Run locally** and
**Reproducible verification** sections in `README.md`.

## Exact live custom fields

| Position | ID | Live label | Required | Live control or options | Prepared answer/custody |
| ---: | ---: | --- | :---: | --- | --- |
| 0 | 28083 | Submitter Type | Yes | Individuals; Team of individuals; Organization | **Individuals** |
| 1 | 28084 | Submitter country of residence | Yes | Country dropdown | **United States** |
| 2 | 28085 | Which Category are you submitting to? | Yes | Taskmaster; Collaborative Partner; Fortified Enterprise Fleet | **Taskmaster** |
| 3 | 28086 | If submitting on behalf of an Organization, what is the Organization name? | Yes | Text | **N/A — individual entrant**; re-check live validation before submission because the conditional-looking field is marked required. |
| 4 | 28087 | What date did you start this project? | Yes | Text; `MM-DD-YY`; project must be newly created during the submission period | **08-18-26**, supported by `submission/ORIGINALITY_PROVENANCE.md`; entrant attestation remains required. |
| 5 | 28141 | URL to your public or private code repo | Yes | Text area | `https://github.com/mikeyerke/driftline`; public-release custody must be current before use. |
| 6 | 28089 | Did you add Reproducible Testing instructions to your README? | Yes | Yes; No | **Yes** |
| 7 | 28088 | Hosted project URL if available | No | URL | `https://driftline-ops.web.app/`; reverify after the authorized candidate release. |
| 8 | 28090 | Testing instructions optional (these are seen by Devpost and judges, not publicly shared) | No | Text | Prepared in `devpost-submission.md`; no credentials required. |
| 9 | 28091 | Which Google SDK did you use? | Yes | Multi-select: ADK; Google GenAI SDK; Antigravity SDK; Genkit; Other | **Agent Development Kit (ADK)** |
| 10 | 28142 | Which Google Cloud Service(s) did you use? | Yes | Multi-select: Cloud Run; Cloud SQL; Firestore; GKE; Pub/Sub | **Cloud Run; Firestore**. Other used services are named in the narrative because the live selector does not offer them. |
| 11 | 28092 | Architecture diagram | Yes | File; 35 MiB; PDF/PPT/PPTX/PNG/JPG/JPEG | `submission/assets/driftline-decision-twin-architecture.png`; currently valid PNG and size. |
| 12 | 28093 | Startup Prize incorporated organization name | No | Text | Leave blank unless Mike independently confirms eligibility. |
| 13 | 28101 | Startup Prize corporate email address | No | Text | Leave blank unless Mike independently confirms eligibility. |
| 14 | 28143 | Which Google AI Models did you use? | Yes | Text; Gemini 3.5 or newer required; additional Google models can boost score | **Gemini 3.5 Flash via Vertex AI (global endpoint)**. Do not claim Gemma, Veo, or Lyria without a real demonstrated integration. |
| 15 | 28106 | OPTIONAL for Bonus Points: public build-content link | No | URL | Prepared story in `submission/BUILD_STORY.md`; URL remains blank until separately approved publication. |
| 16 | 28107 | OPTIONAL for Bonus Points: social-media post link | No | URL | Prepared drafts in `submission/SOCIAL_POST_DRAFTS.md`; URL remains blank until separately approved publication. Use the organizer-stated `#AllThingsAgenticHackathon` hashtag. |

The standard Devpost project record also needs the prepared name, tagline,
description, built-with tags, public video URL, and gallery media. Those values
are centralized in `devpost-submission.md` and `submission/DEVPOST.md`.

## Remaining entrant and release gates

1. Release and freshly reverify the exact candidate before replacing any live
   URL, screenshot, testing, or behavior claim.
2. Record the exact-release continuous browser demo, verify the final package,
   obtain entrant review, and only then upload it publicly to YouTube or Vimeo.
3. Confirm the individual-entrant organization-field behavior in the rendered
   form; do not guess past a live validation error.
4. Personally confirm the start date, originality disclosure, ownership,
   eligibility, official terms, and privacy/marketing choices.
5. Review the final rendered project, architecture attachment, media order,
   links, and category before a separately authorized submission.
6. Publish bonus content or social media only after separate approval; a local
   draft is not a bonus URL.

## Truth boundary

This audit proves the live field schema and the local packet's compatibility.
It does not prove registration, saved-form rendering, project creation,
publication, upload, submission, customer adoption, or judge acceptance.
