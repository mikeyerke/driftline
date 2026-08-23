# Google All Things Agentic — verified submission requirements

Checked against the official Devpost overview, rules, judging criteria,
announcements, submission form, and key-date endpoints on August 23, 2026. The
canonical sources are:

- [Contest overview](https://allthingsagentichackathon.devpost.com/)
- [Official rules](https://allthingsagentichackathon.devpost.com/rules)
- [Google Cloud free program](https://cloud.google.com/free)
- [Contest credit request](https://forms.gle/riGhgDSHkHeMx8Ca6)
- [Google Cloud Gemini 3.5 Flash model reference](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-flash)

## Dates and eligibility

- Contest and submission period: August 3, 2026 at 9:00 AM Pacific through
  August 31, 2026 at 5:00 PM Pacific (September 1, 2026 00:00 UTC).
- Judging period: September 1, 2026 at 9:00 AM Pacific through October 1,
  2026 at 11:45 PM Pacific (October 2, 2026 06:45 UTC).
- Winners are expected on or around October 8, 2026 at 10:00 AM Pacific
  (5:00 PM UTC).
- Devpost's structured key-date feed currently lists September 24 at 5:00 PM
  Pacific as the judging end, while the official rules text lists October 1 at
  11:45 PM Pacific. This does not change the entry deadline; the rules page and
  live Devpost website control if the dates continue to differ.
- Entrants must be above the age of majority in their jurisdiction and must
  not be located in Italy, Quebec, Crimea, Cuba, Iran, Syria, North Korea,
  Sudan, Belarus, or Russia, or otherwise be excluded by export controls,
  OFAC restrictions, or the government-employee conflict rules. Devpost
  registration is required.
- The entry must remain free, working, English-language, and unrestricted for
  judging and testing through the judging period.

## Required technology and materials

Every project must use Gemini 3.5 or newer through Gemini API or Vertex AI, at
least one Google agent framework (Google ADK, GenAI SDK, Antigravity SDK, or
GenKit 3), and at least one Google Cloud infrastructure service. Driftline uses
Vertex AI, Google ADK, Cloud Run, and Firestore. The rules also require a
newly-created project during the submission period, disclosure of pre-existing
work, and authorization for any third-party integrations.

The model reference lists Gemini 3.5 Flash on the `global` and `us` Vertex AI
endpoints. Driftline keeps Cloud Run and Firestore in `us-central1` but sends
the model client to the `global` location.

The Devpost form requires an English description, public or judge-accessible
repository, reproducible README.md, architecture diagram, and a demonstration
video; a hosted project URL is strongly encouraged and Driftline provides one.
The video must show the problem, value, working application, and proof that the
backend runs on Google Cloud. It should be about four minutes; if longer, only
the first four minutes are evaluated. Driftline will use a public YouTube or
Vimeo link so judge access is not dependent on account permissions.

The optional content bonus includes public build content that explicitly says
it was created for this hackathon, a separate social post using the required
`#AllThingsAgenticHackathon` hashtag on the listed social platforms, and
additional Google AI model integrations. Each contribution is optional and
scored under the rules; Driftline does not claim any bonus unless the artifact
is actually published or integrated.

## Categories and selection

The rules require selecting one category, and each project may receive only one
prize:

- Taskmaster — complete a messy, multi-step workflow and take action.
- Collaborative Partner — guide a user, ask clarifying questions, and capture
  feedback.
- Fortified Enterprise Fleet — demonstrate a governed, scalable network of
  institutional agents.

Driftline is being entered as **Taskmaster**. The category specifically values
"Bring Your Own Friction" workflows that finish background work beyond chat.
It is a single governed workflow,
not an enterprise fleet, so the Fortified Enterprise Fleet category is not
claimed. The entry will not claim Startup Excellence without verified
incorporation and corporate-email eligibility.

Prize lanes listed by the official rules include Grand Prize, Taskmaster,
Collaborative Partner, Fortified Enterprise Fleet, Startup Excellence,
Individual/Hobbyist, Best Architectural Design, Best Multimodal UX, and
Honorable Mentions. Driftline selects **Taskmaster**; Grand Prize and the
special prizes are judge-determined outcomes, not additional category
selections. The entry does not claim Startup Excellence without verified
incorporation and corporate-email eligibility.

## New-project disclosure

The rules require projects to be newly created during the submission period and
require disclosure of pre-existing code or work incorporated into the entry.
Driftline is a continuation of an earlier concept conversation and includes the
source package supplied for this build. The Devpost disclosure therefore
describes that prior ideation and identifies the current implementation work
completed during the submission period; it does not claim that earlier
ideation was created during the contest.
The repository's first commit is dated August 18, 2026, inside the August 3–31
submission period; that timestamp is a reproducible implementation-history
anchor, not a claim that the earlier concept conversation was contest work.

## Judging emphasis

Stage One checks baseline viability, category fit, and the requirements above.
Stage Two weights Innovation & Operational Utility at 40%, Architectural
Discipline & Tech Stack at 30%, and Demo & Production Readiness at 30%. The
Taskmaster rubric asks for autonomous execution beyond chat and background
workflow completion, with a distinctive “Bring Your Own Friction” problem. The
architecture rubric looks for modular agents, tools, state, and Google
technology used substantively. The demo rubric asks for an unedited “Proof of
Action,” Google Cloud deployment proof, and reproducible documentation.

## Current submission gates

- Final submission deadline: **August 31, 2026 at 5:00 PM Pacific**.
- The demo video must be publicly viewable on YouTube or Vimeo and no longer
  than four minutes; only the first four minutes are evaluated.
- The hosted project must be free and accessible to judges through judging,
  and the README must include setup instructions and an architecture diagram.
- Driftline will not submit until its live URL, repository, video, claims, and
  integration statuses are all verified. The current video remains on hold by
  the project owner.
