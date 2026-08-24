# Driftline hackathon win audit — August 24, 2026

This audit was refreshed from the live Devpost rules, eligibility, submission
requirements, judging criteria, key dates, prizes, and all seven organizer
announcements after production verification. The
[Devpost website](https://allthingsagentichackathon.devpost.com/) and
[official rules](https://allthingsagentichackathon.devpost.com/rules) prevail
over this helper.

## Official snapshot

- Eligibility: “Above legal age of majority in country of residence.”
  Devpost lists Belarus, Crimea, Cuba, Iran, Italy, North Korea, Quebec, Russia,
  Sudan, and Syria as excluded, with the official rules adding export-control,
  sanctions, conflict-of-interest, and contest-entity restrictions.
- Submission deadline: August 31, 2026 at 5:00 PM Pacific
  (September 1 at 00:00 UTC). Submissions are currently open.
- The structured feed lists judging September 1–24; the rules text lists a later
  October 1 end. This does not alter the entry deadline. The live website
  controls if the discrepancy remains.
- Mandatory stack: Gemini 3.5 or newer, at least one Google agent framework, and
  at least one Google Cloud infrastructure service.
- One category must be selected. Driftline's prepared category is Taskmaster.
- Required materials: category, hosted URL if available, text covering features,
  technology, data sources, findings/learnings, repository and spin-up
  instructions, architecture diagram, and public YouTube/Vimeo demo.
- Video: public, under four minutes, English or subtitled, working agent, visible
  Google Cloud backend proof. Only the first four minutes are evaluated.
- Final fields include the Google SDK/framework and project start date.
  Pre-existing and third-party code must be disclosed.
- After the deadline, the submitted repo, video, and linked materials must remain
  unchanged until winners are announced.
- Judging: Innovation & Operational Utility 40%; Architectural Discipline &
  Tech Stack 30%; Demo & Production Readiness 30%.
- Official prize pool: $180,000 across Grand Prize, three core tracks, Startup
  Excellence, Individual/Hobbyist, architecture, multimodal, and honorable
  mention prizes. Prize outcomes are judge-determined, not entrant claims.

## Evidence checklist

| Claim or requirement | Current evidence | Status |
| --- | --- | --- |
| Baseline production identity | August 24 snapshot: SHA `1b8a8bf...`, revision `driftline-00291-v89`, build `154547e7...`, digest `sha256:18d8...`; final identity comes from `/health` and the production verifier | Proven historical baseline |
| Hosted judge URL | `https://driftline-ops.web.app/` | Proven |
| Gemini 3.5 Flash | Live Vertex/ADK council and general agent verification | Proven |
| Google ADK | Five specialists + synthesis; coordinator/tool trace | Proven |
| Google Cloud | Cloud Run, Firestore, BigQuery, Tasks, Scheduler, Build, Artifact Registry, Storage, Secret Manager | Proven |
| Real disagreement | Live roles recommend ship/segment/defer with 24 total citations | Proven |
| BigQuery aggregate | Attached event, minimum cohort 84, weighted query/privacy/bytes contracts | Proven |
| Human authority | Named-human approval; stale generation and hash protection | Proven |
| Reversible experiment | Option-specific contract and outcome-driven reopen | Proven |
| Complete lineage | Generation-1 approval, plan, trigger, and reason survive generation 2 | Proven |
| CI/reproducibility | 386 tests; GitHub run `32757068133` all four jobs green | Proven |
| Security diff | 14 surfaces reviewed; two medium findings fixed and tested | Proven |
| Customer/PM utility | Study kit only; no genuine participant data | Unproven |
| Customer ROI/WTP | No measurements | Unproven |
| Final public video | Script/runbook/captions only | Unproven |
| Final screenshots | Existing assets need final release QA | Partial |
| Registration/rules agreement | Local state remains unacknowledged | Not performed |
| Devpost submission | No project registration or submission action taken | Not performed |
| Optional bonus posts/content | Drafts only; nothing published | Not performed |

## Rules-change response

The August 24 organizer checklist reinforces “new project,” one selected
category, public under-four-minute demo, Google Cloud proof, SDK/start-date
answers, and disclosure. It also recommends jump cuts to remove waiting. The
judging criterion still asks for a live, unedited proof of action. Driftline's
safe recording contract is therefore:

1. Begin with the working product within 10–15 seconds.
2. Edit setup, narration, and waiting for pace.
3. Keep the core council → approval → outcome → generation-2 reopen path
   continuous, tied to one visible case, with no cut that can fabricate action.
4. Finish with Cloud Run/Firestore/BigQuery/release identity proof.
5. Freeze submitted evidence after the deadline.

## Final entrant gates

1. Personally confirm eligibility and explicitly agree to the official rules.
2. Run 6–8 genuine PM validation sessions or retain “not measured.”
3. Record/upload the final public video and QA captions, timing, secrets, and
   legibility.
4. Capture and attach final screenshots/architecture.
5. Enter category, SDK, start date, disclosure, repo, hosted URL, video, and
   testing instructions.
6. Register and submit only after separate explicit authorization.
7. Freeze the submitted artifacts after the deadline.

Nothing in this audit registers, submits, emails, posts, or accepts legal terms.
