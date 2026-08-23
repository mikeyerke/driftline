# Driftline hackathon win audit — August 23, 2026

Sources checked live through the Devpost integration on August 23: official
rules, submission requirements, judging criteria, key dates, prizes, and all six
organizer announcements. The Devpost website and official rules prevail over
this working audit.

## Executive verdict

Driftline is a credible Taskmaster and Best Architectural Design contender. Its
strongest winning idea is not “AI finds a change”; it is the inspectable,
evidence-bound transition from autonomous work to human authority to durable,
reversible action. The new crash-safe operation lifecycle directly answers the
organizer's long-running-agent emphasis on recovery, approval, and idempotency.

The build is not yet submission-ready because the final PR is intentionally not
deployed, the final public video has not been recorded/uploaded, official rules
have not been acknowledged in the local Devpost flow, registration has not been
performed, real-user validation has not been run, and bonus content is still
private. None of those gaps is being disguised as complete.

## Official requirements and evidence

| Requirement | Driftline evidence | Status |
| --- | --- | --- |
| New autonomous agent beyond chat | Async monitor → ADK/Gemini analysis → deterministic gate → owner action → reversal | Pass |
| Gemini 3.5+ | Gemini 3.5 Flash through Vertex AI, asserted and checked in runtime/evaluation gates | Pass |
| Google agent framework | Google ADK coordinator with two bounded tools | Pass |
| Google Cloud infrastructure | Cloud Run, Firestore, Cloud Tasks, Scheduler, Storage, Build, Artifact Registry, Secret Manager | Pass |
| Exactly one category | Taskmaster | Pass |
| Hosted URL encouraged | `https://driftline-ops.web.app/` | Pass |
| Repo and reproducible setup | Public repo, locked dependencies, local/cloud instructions, automated gates | Pass |
| Architecture diagram | `submission/assets/driftline-architecture.png` | Pass; refresh after final deploy |
| Demo ≤4 minutes, public YouTube/Vimeo, English/subtitles | Script/runbook/caption assets prepared | Open: final truthful recording/upload |
| Demo shows problem, value, live action, Google Cloud backend | Continuous product path and Cloud proof are scripted | Open until final video passes QA |
| Project started during submission period | Implementation start documented as August 18; earlier ideation/source package disclosed | Pass, preserve disclosure |
| Third-party rights and safe content | Open-source dependencies/lockfiles, synthetic/public evidence, no secret assets in demo | Pass; final media review required |
| Required form fields | Exact draft answers, repo, model/framework/service, architecture, start date prepared | Pass locally; not registered/submitted |

## Rubric audit

### Innovation & Operational Utility — 40%

Current evidence strength: **34/40**; attainable after real-user study and final
demo: **37–39/40**.

Winning proof:

- Solves a specific, recurring Product Marketing/RevOps chore rather than a
  generic assistant problem.
- Agent autonomously verifies evidence, maps impact, drafts bounded options,
  and routes owner-ready work before judgment is required.
- Judge Mode makes Evidence → Decision → Action → Proof legible in one path.
- Action is real, persisted, accountable, and reversible—not a chat answer.
- A no-change monitor result creates no noisy business workflow.

Remaining risk: Taskmaster explicitly rewards work completed with little to no
hand-holding. The video must show that the human contributes one consequential
decision, not step-by-step supervision. The six-participant paired study is the
only honest route to a utility claim; until run, ROI remains unmeasured.

### Architectural Discipline & Tech Stack — 30%

Current evidence strength: **28/30**; attainable: **29–30/30**.

Winning proof:

- Async Cloud Tasks worker, Firestore CAS transitions, deterministic policy,
  scoped credentials, append-only evidence/audit, isolated public/signed lanes.
- Side effects are durably claimed before execution. Approval, reversal, and
  recovery reuse one credential-free operation ID and generation.
- Ambiguous failures enter `reconciliation_required`; conflicting decisions
  fail closed; configured recovery requires signed tenant authority.
- Idempotent Jira/artifact behavior, bounded agent tools, no approval tool, and
  redacted trace evaluation make failure and authority boundaries explicit.

Remaining risk: final architecture art and narration must explain this simply.
Do not bury the operation lifecycle in implementation jargon.

### Demo & Production Readiness — 30%

Current evidence strength before final video/deploy: **22/30**; attainable:
**29–30/30**.

Winning proof already present:

- Public hosted app, clean repo, architecture asset, reproduction scripts,
  release SHA/build proof, responsive product, visible agent trace.
- Four-part proof receipt and default-on Judge Mode reduce judge search cost.
- Video script requires one continuous approval → receipt sequence and visible
  Google Cloud proof.

Blocking gap: the new UI/recovery code is on a review branch, not the serving
release. The final video cannot truthfully show it until deployment is approved
and verified. The existing 43-second MP4 is rehearsal-only and must not be used
as the final entry.

## Bonus and prize strategy

- Primary: Grand Prize and The Taskmaster.
- Secondary: Individual/Hobbyist and Best Architectural Design.
- Best Multimodal UX is possible but should not distract from the core proof.
- Build story and social post each offer up to 0.2 bonus points. Drafts are
  complete but must be publicly published and linked to count.
- Additional Google models can add 0.2 each, but adding Gemma/Veo/Lyria now is
  not recommended unless it makes the core task materially better. A decorative
  model call would weaken architectural discipline more than the bonus helps.
- Startup Excellence should remain unselected unless the entrant is submitting
  for an incorporated organization with a corporate email and independently
  confirms eligibility.

## Final-week order of operations

1. Merge only after review; deploy once; run the complete release/provenance,
   public approval/reopen, security, and responsive-browser gates.
2. Run 6–8 real-user paired sessions from `docs/VALIDATION_STUDY_KIT.md`; publish
   only the anonymized, reviewed aggregate if thresholds are honestly met.
3. Record the 3:45–3:50 demo from the verified release. Keep the approval click
   and proof receipt continuous; show Cloud Run/Firestore evidence.
4. QA captions, 720p text legibility, secrets, model/framework names, release
   SHA, and the four-minute limit; then upload publicly.
5. Update Devpost copy with the final video URL, serving SHA, validation result
   (or explicit “not measured”), and refreshed screenshots/architecture.
6. After entrant approval, publish the build story and one social post with
   `#AllThingsAgenticHackathon`; paste both public URLs into the optional fields.
7. Complete the official rules/eligibility gate and registration; render-review
   every field; submit before the deadline buffer, then verify the live project.

## Stop-ship checks

- No submission or registration without explicit rules/eligibility agreement.
- No final video over four minutes or hosted anywhere except public YouTube/Vimeo.
- No mockup, staged outage, or edited cut that implies an action occurred when it did not.
- No claim that anonymous judges can write Jira or that a packet-only run changed an external system.
- No customer ROI, time-saved, or willingness-to-pay claim without real study evidence.
- No mismatch among deployed behavior, video, Devpost text, architecture, and repository head.

Official deadline: August 31, 2026 at 5:00 PM Pacific Time. Judging begins
September 1. The official rules contain eligibility, originality, IP, content,
privacy, and prize conditions that the entrant must personally read and accept.
