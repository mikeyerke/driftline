# Driftline hackathon win audit — August 23, 2026

This is the evidence-backed go/no-go audit for the All Things Agentic
Hackathon. It does not authorize registration or submission. The official
Devpost website and rules control if any helper document differs.

## Executive verdict

Driftline is a credible Taskmaster and Best Architectural Design contender.
Its strongest proof is not the number of integrations: it is the complete,
bounded workflow from source change to evidence, autonomous impact analysis,
human policy gate, persisted owner action, and scoped reversal. The public app
reproduces that path without credentials.

Current readiness is **strong build, incomplete entry**. Code and live product
proof are substantially ready; the final public four-minute video, fresh
post-release screenshots, and entrant confirmations are not. Do not submit
until every red gate below is closed.

## Official requirement matrix

| Requirement | Driftline proof | Status |
| --- | --- | --- |
| New project during Aug 3–31 | First implementation commit is Aug 18; earlier ideation/source package is disclosed | Ready |
| Gemini 3.5 or newer | Vertex AI `gemini-3.5-flash`, asserted by live verifier | Ready |
| Google agent framework | Google ADK with bounded tools and structured turns | Ready |
| Google Cloud infrastructure | Cloud Run, Firestore, Cloud Tasks, Cloud Storage, Scheduler, Secret Manager | Ready |
| Beyond a chat loop | Source-to-action workflow with durable job state, approval, packet, owner queue, and reversal | Ready |
| Function as depicted | Public judge path completed end to end on Aug 23 | Ready; repeat before recording |
| Authorized third-party use | Allowlisted public fixtures; signed connector credentials are tenant-scoped | Ready; preserve disclosures |
| Free, unrestricted judge access | Public Cloud Run lane needs no login or connector secret | Ready; keep available through judging |
| English submission | Product, README, form copy, and captions are English | Ready |
| Repository and setup | Public repository with locked setup and verification commands | Ready |
| Architecture diagram | 1600×900 PNG plus editable SVG | Ready |
| Public demo video | Current MP4 is a 43-second proof clip, not the final entry | **Blocked** |
| Required Devpost fields | Drafted; entrant eligibility, organization value, and consent still need human confirmation | **Blocked** |

## Winning lane

Select **Taskmaster**. Position for Grand Prize, Taskmaster, Best Architectural
Design, and Individual/Hobbyist. Treat Best Multimodal UX as an upside only if
the final entry demonstrates a meaningful multimodal interaction; do not force
that claim from ordinary visual evidence cards.

The four judging minutes should spend roughly the rubric weights:

1. **40% operational utility:** show the messy chore and the full action loop.
2. **30% architecture:** prove bounded ADK tools, durable state, credential
   isolation, idempotency, failure handling, and reversal.
3. **30% production readiness:** one continuous public run, serving SHA/build,
   reproducible commands, cloud records, and architecture image.

## Judge-risk register

1. **Final video is absent — critical.** Record one continuous take at 3:45 or
   shorter, publish it publicly on YouTube or Vimeo, and verify it signed out.
2. **Polish branch is not deployed — high.** PR #16 simplifies the judge lane,
   but the public screenshots still show the earlier header and duplicated CTA.
   Deploy only after reviewer approval, then recapture every submission frame.
3. **Release proof had drifted — fixed in the draft.** `/health` reported
   `e38facc43745eab267eacd2da4aa28914dff383b` and build
   `96dbf2d7-7ee3-490a-a854-bef5c9615efc` on Aug 23; the form-ready copy now
   matches. Historical deployment records remain historical.
4. **Taskmaster action could be misunderstood — high.** Narration must call out
   that approval writes a real evidence packet, owner queue, audit operation,
   and reversal to Google Cloud. External Jira proof is optional, signed, and
   must never become a dependency for judge reproduction.
5. **Claims can outrun evidence — medium.** Do not claim customers, ROI, revenue
   lift, arbitrary crawling, autonomous approval, or anonymous external writes.
6. **Bonus points are drafted, not earned — medium.** Publish build content and
   a separate social post with `#AllThingsAgenticHackathon` only after owner
   review; link the public artifacts in Devpost.
7. **Date feed discrepancy — low.** The judging-end date differs between the
   structured Devpost feed and rules text. The Aug 31 5:00 PM Pacific submission
   deadline agrees; the live website and official rules prevail.

## Security hardening completed in this audit

The source review found and fixed a high-confidence concurrency flaw in the
approval/reversal boundary. Approval and reversal now claim durable
`approval_executing` and `reversal_executing` states before connector or
artifact side effects, reject a conflicting request, check the final Firestore
compare-and-set, and reload durable truth on failure. Two regression tests
exercise the raced approval/undo paths. Visual asset requests also fetch only
the requested allowlisted side instead of downloading the complete pair.

The public judge lane's immutable Cloud Storage output is intentional product
behavior, not a customer-system write: it is rate-bounded, returns no signed
URL, records `external_systems_changed=false`, and is the reproducible
Taskmaster action shown to judges. Configured customer connectors still require
a signed tenant identity.

## Final go/no-go gates

- [ ] Reviewer approves PR #16; no merge is performed by the automation agent.
- [ ] Approved polish release is deployed and `/health` proof is updated.
- [ ] Fresh desktop and mobile captures replace pre-release submission images.
- [ ] One continuous 3:45-or-shorter video passes the recording checklist.
- [ ] Public video works in a signed-out browser and shows Google Cloud proof.
- [ ] Live agent, public approval/undo, production, and trace-eval scripts pass
      against the exact serving SHA.
- [ ] Final form values and eligibility are confirmed by the entrant.
- [ ] Architecture image, repository, hosted URL, and testing instructions are
      rendered and clicked from the Devpost preview.
- [ ] No draft language claims unpublished bonus content or unverified outcomes.
- [ ] Entrant explicitly authorizes registration and the final submission.

## Recommended final-week order

1. Review and approve the polish PR; deploy once authorized.
2. Run the full local and live release gates against the serving revision.
3. Capture the continuous demo and fresh stills from that exact revision.
4. Publish optional build/social artifacts after owner review.
5. Perform a signed-out judge rehearsal with a strict four-minute timer.
6. Complete registration and preview the entry only when the owner authorizes.
7. Submit early enough to recover from upload or permissions failures, while
   retaining the option to polish before the official deadline.
