# Driftline resource inventory

This inventory is intentionally scoped to the isolated Google Cloud project
`driftline-hackathon-2026`. The active gcloud configuration was checked during
the release run:

```text
core.account: mikeyerke@gmail.com
core.project: driftline-hackathon-2026
project number: 724959673622
```

## Current active release (authoritative check)

Checked `2026-08-21T22:07Z` with the active gcloud project set to
`driftline-hackathon-2026`:

- Cloud Run service `driftline` in `us-central1` serves revision
  `driftline-00144-k89` at 100% traffic. Its immutable serving image is
  `sha256:bd92080f10b6e8ecef912b4f0d6e8db79bff420067ff9d02fc6be44048b20a52`.
- The public alias is
  `https://driftline-xvxczqg62a-uc.a.run.app/`.
- `/health` reports Firestore persistence and async jobs; `/api/auth/config`
  reports Google OIDC enabled with the isolated project-owned client,
  `anonymous_lane=packet_only`, and no credential values exposed.
- The live production verifier also checks `Cache-Control: no-store` and the
  fail-closed `Permissions-Policy` deny-list on both health and API responses.
- The Settings surface exposes the tenant-scoped Salesforce OAuth handoff and
  aggregate read probe without exposing credentials or CRM records; final
  authorization remains an owner-controlled Salesforce consent action.
- Entries below are append-only release evidence. Some refer to earlier
  service lifecycles and are not claims about the currently serving revision;
  direct `gcloud run services describe` output above is the current-state
  authority.

## 2026-08-21 map utility and no-op monitoring release (current serving revision)

- Source commits `f6ba47f` and `584715b` passed GitHub Actions run
  `32531130663` (259 backend tests, Ruff, frontend production build,
  standalone image build, and repository hygiene) and deployed through Cloud
  Build `85d14b55-0389-409e-b98f-edc15edc42ea` (`SUCCESS`, 3m39s).
- Cloud Run revision `driftline-00144-k89` serves 100% traffic with immutable
  image digest
  `sha256:bd92080f10b6e8ecef912b4f0d6e8db79bff420067ff9d02fc6be44048b20a52`.
- The impact map now exposes per-stage link counts, focused link counts,
  connected-node counts, keyboard-selected state, and a worklist handoff. At
  the 1280px judge viewport the map received the full 1024px control-plane
  width rather than being squeezed beside approval; the browser reported
  `scrollWidth=1280`. Selecting Pricing battlecard produced 5 connected nodes,
  5 focused links, 7 dimmed siblings, and the next handoffs Confluence and
  Slack. A 390x844 check retained the map in a 362px panel with
  `scrollWidth=390`.
- The append-only source history now derives and shows `baseline_established`,
  `unchanged`, or `changed` from adjacent immutable snapshot hashes. The live
  source registry displayed five healthy sources with “Last check · No
  material change”, making the monitor's no-op behavior visible rather than
  implying every poll is an action.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors.
  Fresh live-agent proof returned `job-3678579224eb` / workflow
  `28d67b19-85e2-40a3-a805-f158a50747e7`, `needs_approval`, public-source mode,
  Gemini 3.5 Flash through Google ADK, two allowlisted tools, four artifacts,
  five audit events, and two decision options. Approval/undo proof returned
  `job-61cadd411f63` / workflow `baeadd42-4c0b-4012-980e-15bae6b64850`,
  persisted the packet, reversed the operational output, and recorded
  `external_write=false` and `external_systems_changed=false`.

## 2026-08-21 focused-map readability release (historical serving revision)

- Source commit `48ca9f8` passed GitHub Actions run `32529461064` (258 backend
  tests, Ruff, frontend production build, standalone image build, and
  repository hygiene) and deployed through Cloud Build
  `0b9e4e54-b87b-4527-9376-0748a19a7710` (`SUCCESS`, 2m56s).
- Cloud Run revision `driftline-00142-657` serves 100% traffic with immutable
  image digest
  `sha256:d3ec8b1aaa2e8973b3d1f33bfde7ea31215e09cbc15babb741ea7770903b9100`.
- Focused impact-map secondary nodes retain readable contrast while remaining
  visually subordinate; fresh desktop QA showed seven dimmed siblings, a
  prominent selected work surface, and no horizontal overflow. A final 390x844
  mobile check reported `scrollWidth=390` and retained the map/inspector.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors.
  Fresh live-agent proof returned `job-0386cee0979b` / workflow
  `0cf5ae56-19af-449a-87cd-9cfcfbafa18b`, `needs_approval`, public-source mode,
  Gemini 3.5 Flash through Google ADK, two allowlisted tools, four artifacts,
  five audit events, and two decision options. Approval/undo proof passed on
  the same workflow, persisting the packet and reversing the operational output
  with `external_write=false` and `external_systems_changed=false`.

## 2026-08-21 directional impact-focus release (historical serving revision)

- Source commit `5e51bec` passed GitHub Actions run `32528922025` (258 backend
  tests, Ruff, frontend production build, standalone image build, and
  repository hygiene) and deployed through Cloud Build
  `facf9edd-5d63-49e0-acab-1c51614ca9b8` (`SUCCESS`, 3m22s).
- Cloud Run revision `driftline-00141-x97` serves 100% traffic with immutable
  image digest
  `sha256:b291820568db59bf60f51ae5b81ec39279e325dd6016e6da70ab474cecdac9d5`.
- Impact-map focus now follows directed evidence semantics: a source fans out
  through every downstream stage, while an artifact highlights only its source
  path and downstream handoffs and dims sibling work. Fresh desktop browser QA
  verified source fan-out and pricing-battlecard isolation with no horizontal
  overflow.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors.
  Fresh live-agent proof returned `job-01ef54f988fe` / workflow
  `a14384b1-a3b5-45e9-ae80-78144e336ea5`, `needs_approval`, public-source mode,
  Gemini 3.5 Flash through Google ADK, two allowlisted tools, four artifacts,
  five audit events, and two decision options. Approval/undo proof passed on
  the same workflow, persisting the packet and reversing the operational output
  with `external_write=false` and `external_systems_changed=false`.

## 2026-08-21 full pre-scan graph release (historical serving revision)

- Source commit `9a23fd4` passed GitHub Actions run `32527512451` (258 backend
  tests, Ruff, frontend production build, standalone image build, and
  repository hygiene) and deployed through Cloud Build
  `c00e383c-7868-47b8-b7b2-af49a5e6f670` (`SUCCESS`, 3m14s).
- Cloud Run revision `driftline-00138-bcf` serves 100% traffic with immutable
  image digest
  `sha256:00852752feb22432f4dc1b14d85e969263cb89da1af3f47266a0760b610b6323`.
- The impact map is an accessible interactive graph before and after a scan:
  the deterministic pre-scan state now shows source, offering, impact area,
  work surface, and prepared handoff stages; selecting a node focuses its
  evidence path, dims unrelated nodes, and exposes a bounded inspector with
  owner, risk, and worklist handoff. Desktop and 390x844 mobile browser QA
  showed no horizontal overflow.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors.
  Fresh live-agent proof returned `job-41c4329adae2` / workflow
  `3e30298a-9465-4e4a-a6a2-681cdace0f8d`, `needs_approval`, public-source mode,
  Gemini 3.5 Flash through Google ADK, two allowlisted tools, four artifacts,
  five audit events, and two decision options. Approval/undo proof passed on
  the same workflow, persisting the packet and reversing the operational output
  with `external_write=false` and `external_systems_changed=false`.

## 2026-08-21 interactive decision-surface release (historical serving revision)

- Source commit `ce2b5ca` passed GitHub Actions run `32524543240` (258 backend
  tests, Ruff, frontend production build, standalone image build, and
  repository hygiene) and deployed through Cloud Build
  `4998dd62-a9aa-4b48-a815-52dd4934c5df` (`SUCCESS`, 3m24s).
- Cloud Run revision `driftline-00136-fzq` serves 100% traffic with immutable
  image digest
  `sha256:59b30f1b7b8dd39e57c202d923e61062e4d3fb012b1e25c4d6d46a7d20a1c50e`.
- Operator source registration now fails closed at 25 enabled custom sources
  per tenant, allows updates to existing source IDs at the limit, and remains
  separate from the deployment-wide scheduler cap of 25 selected sources.
  Persistence failures fail closed rather than silently bypassing the limit.
- `scripts/verify_production.sh`, `scripts/verify_live_agent.sh`, and
  `scripts/verify_public_approval_undo.sh` all passed on this revision. The
  live agent proof returned `job-af119fe3e0d3` / workflow
  `16c65c2c-6341-4dbc-8d5f-3afd99cf0596`, Gemini 3.5 Flash through Google ADK,
  two allowlisted tools, four artifacts, five audit events, and two decision
  options; approval/undo persisted the packet and reversed the operational
  output with no external connector writes.

## 2026-08-21 cadence-aware monitor verification

- The real isolated Cloud Scheduler job `driftline-monitor` was manually run
  through Google Cloud at `2026-08-21T20:31:32Z` using its existing OIDC
  service identity; no IAM permissions or deployment settings were widened.
- The deployed `/api/scheduler/tick` returned HTTP 200 and selected only the
  two sources whose cadence deadlines had arrived. It created monitor jobs
  `job-ab0c901478e7` (`public/pricing`) and `job-5b317c2f1c7d`
  (`competitor/pricing`); both completed with Gemini 3.5 Flash and no
  dead-lettered task.
- Firestore source history advanced to `2026-08-21T20:31:36Z` for
  `public/pricing` and `2026-08-21T20:31:41Z` for `competitor/pricing`. The
  other three sources were correctly deferred until their separate cadence
  deadlines, proving that the always-on path is cadence-aware rather than a
  blind five-source spend spike.
- The post-run operations summary reported `dead_lettered=0`; Cloud Logging
  showed zero `ERROR` entries for the run window. This is operational monitor
  evidence, not customer outcome or ROI evidence.

## 2026-08-21 Salesforce authorization-state UX release

- Source commit `b1d60e8` deployed successfully through Cloud Build
  `d80208cf-532e-420e-a832-b65d34d91762` (`SUCCESS`, 3m27s) as revision
  `driftline-00135-dv2` at 100% traffic. The serving image is pinned to
  `sha256:db707393bf53a4052501c807ea6dc34d96b895550db9328ad2b2fd6a0dbb3977`.
- Signed context now renders Salesforce as “Authorization required” and “OAuth
  consent required” rather than a generic not-configured state. The state is
  still redacted and read-only until the owner completes consent.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors.
  Fresh live proof returned job `job-6cee02e8b4cf` / workflow
  `2997be46-f313-43d0-9a3d-89a9524cfa48`; approval/undo returned job
  `job-bb0ae6f8abfa` / workflow `0c062253-a31e-46b6-ad72-9ee7351d392e`.

## 2026-08-21 Salesforce OAuth read-lane correction release

- Source commit `c5587fa` deployed successfully through Cloud Build
  `afcea230-b6e9-40a5-bbd8-cdc0631738c8` (`SUCCESS`, 3m7s) as revision
  `driftline-00134-rfk` at 100% traffic. The serving image is pinned to
  `sha256:1f3f419b54589fddabfd01d71267be97ef99e971304934a10cf1652b04efea2c`.
- The Salesforce read-only client now accepts the tenant OAuth access token
  returned after refresh and no longer requires a deployment-wide Salesforce
  bearer token. The allowlisted instance host and API version remain enforced.
- Local verification passed 257 backend tests, Ruff, frontend build
  (`317.12 kB`, `93.24 kB` gzip), and `git diff --check`. GitHub Actions run
  `32521842231` passed all repository gates.
- `scripts/verify_production.sh` passed; fresh live proof returned job
  `job-f9e53621237e` / workflow `fbcbe6a0-aebe-481a-8a91-574f9875fa4a` with
  `needs_approval`, public-source evidence, Gemini 3.5 Flash, Google ADK,
  two allowlisted tools, four artifacts, five audit events, and two options.
- `scripts/verify_public_approval_undo.sh` passed with job
  `job-1bcfe167c869` / workflow `a56f7902-c614-4d68-b0ca-01e64050df11`:
  packet persisted, output reversed, `external_write=false`, and
  `external_systems_changed=false`.

## 2026-08-21 Salesforce context release

- Source commit `2ed984a` deployed successfully through Cloud Build
  `cfc8ad87-78c4-48be-9168-9e1ba4592027` (`SUCCESS`, 2m48s) as revision
  `driftline-00133-clc` at 100% traffic. The serving image is pinned to
  `sha256:eb05baa0ff2348d7ce95d2d14d481832b907f46cad0377b4195f2f71057bcf6c`.
- The signed internal context summary now includes a fifth Salesforce card. It
  remains `not_configured`/`authorization_required` until the owner completes
  the OAuth callback; after connection it reads only the fixed CRM object
  aggregates and preserves `external_read=false` before consent.
- Local verification passed 256 backend tests, Ruff, frontend build
  (`317.12 kB`, `93.24 kB` gzip), and `git diff --check`. GitHub Actions run
  `32521205835` passed all repository gates.
- `scripts/verify_production.sh` passed; fresh live proof returned job
  `job-26c1f709be05` / workflow `e8228bee-ed23-4e63-b05d-1b7009ed91a7` with
  `needs_approval`, public-source evidence, Gemini 3.5 Flash, Google ADK,
  two allowlisted tools, four artifacts, five audit events, and two options.
- `scripts/verify_public_approval_undo.sh` passed with job
  `job-a3712845c7c2` / workflow `09d097bc-66f1-43f8-a796-1112ed5a819c`:
  packet persisted, output reversed, `external_write=false`, and
  `external_systems_changed=false`.

## 2026-08-21 Salesforce control-surface release

- Source commit `c41b8dc` deployed successfully through Cloud Build
  `bb7442af-0893-4f3c-8a4a-570b3b59f180` (`SUCCESS`, 3m2s) as revision
  `driftline-00132-ldk` at 100% traffic. The serving image is pinned to
  `sha256:9882f48fac7db8bc9ab090d98ff03459308b489b0690900a4b1a006a06801310`.
- The new owner-only Settings panel starts the existing PKCE OAuth flow,
  renders the returned consent URL without logging it, and offers a separate
  aggregate-only Salesforce read probe after callback completion. The route
  returns tenant metadata only (`credential_values_exposed=false`).
- The signed internal context summary now includes a fifth Salesforce card. It
  remains `not_configured`/`authorization_required` until the owner completes
  the OAuth callback; after connection it reads only the fixed CRM object
  aggregates and preserves `external_read=false` before consent.
- Local verification passed 253 backend tests, Ruff, frontend build
  (`316.74 kB`, `93.09 kB` gzip), and `git diff --check`. GitHub Actions run
  `32519809024` passed all repository gates.
- `scripts/verify_production.sh` passed; fresh live proof returned job
  `job-063b75f4c617` / workflow `2f1ce3f7-d6e3-4d4c-9bed-b9445b3b6c50` with
  `needs_approval`, public-source evidence, Gemini 3.5 Flash, Google ADK,
  two allowlisted tools, four artifacts, five audit events, and two options.
- The same durable job/workflow passed approval/undo verification: packet
  persisted, output reversed, `external_write=false`, and
  `external_systems_changed=false`.

## 2026-08-21 header-only operator credential proof

- Source commit `7a26522` deployed successfully through Cloud Build
  `5375841c-f3cc-43fb-a839-56a8784f5008` (`SUCCESS`, 3m28s) as revision
  `driftline-00131-5tn` at 100% traffic. The serving image is pinned to
  `sha256:61d4edfcd7502bc1ec5710e18d81b91f4939dc9960a3d7b80245effa5b49b542`.
- Signed browser calls now send the short-lived Google ID token only in the
  `Authorization` header; it is not duplicated into JSON bodies or URLs. A
  repository-hygiene CI check fails if that client-side pattern returns.
- `scripts/verify_production.sh` passed on this revision. Fresh live proof
  returned job `job-bf32f027a99f` / workflow
  `41fda217-a32d-49dc-b58b-4cf88e2b4fe2` with `needs_approval`, public-source
  evidence, Gemini 3.5 Flash, Google ADK, two allowlisted tools, four
  artifacts, five audit events, and two Decision Copilot options.
- The same durable job/workflow passed the approval/undo verifier: packet
  persisted, operational output reversed, `external_write=false`, and
  `external_systems_changed=false`. The verifier deduplicated the concurrent
  public proof request by design.
- The first build attempt was not deployed: Cloud Build
  `41e567d8-8f81-486a-a4e4-fc6de4c63179` failed only on a transient PyPI
  extraction timeout. Root and standalone Dockerfiles now use bounded UV
  timeout/retry settings; the successful rebuild proves the fix.

## 2026-08-21 latest production proof refresh

- The isolated Cloud Scheduler job `driftline-monitor` was manually triggered
  at `2026-08-21T17:51:29Z`. Cloud Logging recorded an
  OIDC-authenticated `Google-Cloud-Scheduler` request to `/api/scheduler/tick`
  on `driftline-00130-9cn` with HTTP 200 and 2.29 seconds latency. This proves
  the background delivery path is live; the cadence-aware scheduler correctly
  deferred healthy sources that were not yet due.
- `scripts/verify_production.sh` passed against the same revision at
  `2026-08-21T17:55Z`: Firestore, Tasks, Scheduler, uptime, alerting, IAM,
  security headers, tenant boundary, and zero recent Cloud Run errors.
- Fresh exact-revision live agent proof passed on job
  `job-9dfaae082328` / workflow `6aa95f1c-df5a-4ae7-9a2d-f0d5416705ca` with
  `needs_approval`, `public_source`, Gemini 3.5 Flash, Google ADK, two
  allowlisted tools, four artifacts, five audit events, and two Decision
  Copilot options.
- Fresh exact-revision approval/undo proof passed on job
  `job-645b96127b2d` / workflow `0b350ff6-9cf8-460a-b4d2-b2cca879339e`;
  the packet persisted, the operational output reversed, and both
  external-write flags were false.
- Artifact Registry cleanup retained the newest ten image digests, including
  the serving digest, and removed eleven older unreferenced tagged builds from
  this isolated repository. No Cloud Run revision or serving image was
  deleted; the 30-day cleanup policy remains active.

## 2026-08-21 evaluation-boundary and proof-of-action polish (live)

- Source commit `453169b` was deployed by Cloud Build
  `fbb439be-dbad-48f7-b203-feaaf96d4a54` (`SUCCESS`, 3m22s) as Cloud Run
  revision `driftline-00130-9cn` at 100% traffic. The immutable image digest is
  `sha256:91d62c9823f66ed9360bc5d9397023094e736adf2c6e76a0bfb096ffab16f219`.
- The public banner and value-proof panel now call the lane what it is:
  pinned synthetic scenarios and evaluation-only deployment records, not
  customer usage or ROI. The approved state adds a compact proof-of-action
  receipt for the Firestore action, Cloud Storage persistence, rollback path,
  and external-write posture. The exact demo replay evidence label is also
  `Pinned synthetic fixture`, so the public source card cannot be mistaken for
  a live customer or competitor feed. Decision Copilot citations now label
  whether a quote is `Observed after` or `Prior baseline` rather than hiding
  that distinction behind a generic citation label.
- Local verification passed 252 backend tests, Ruff, `git diff --check`, and
  the frontend production build (`311.51 kB`, `91.96 kB` gzip). GitHub Actions
  run `32518704117` passed the repository gates.
- Fresh exact-revision live agent proof passed on job `job-575414fcb95f` /
  workflow `da2044fe-60ae-4cae-9d95-47a22ccf8761` with `needs_approval`,
  `public_source`, Gemini 3.5 Flash, Google ADK, two allowlisted tools, four
  artifacts, five audit events, and two Decision Copilot options.
- Fresh exact-revision approval/undo proof passed on job `job-29d033086f51` /
  workflow `46df9083-4ab9-4d96-821a-a9ebe6a359aa`; the packet persisted, the
  operational output reversed, and both external-write flags were false.

## 2026-08-21 cadence-aware monitor release (live)

- Source commit `5f06bb2` was deployed by Cloud Build
  `b915d84b-7b4b-4b22-8153-b316dde951de` (`SUCCESS`) as Cloud Run revision
  `driftline-00125-2bl` at 100% traffic. The immutable image digest is
  `sha256:8507753c033b6060b3ab3f1dbff0119521883930b5989bf9b6662ba0fa7004d1`.
- Scheduler selection is now cadence-aware: healthy sources wait for their
  observation cadence, while missing baselines, stale sources, source-fetch
  failures, and synthetic-only records are eligible for recovery. Due work is
  round-robined across tenant buckets before the hard 25-source cap, and the
  response includes deferred source IDs with `not_due` or `source_cap` reasons.
  Freshness SLA remains a separate staleness signal.
- The live Cloud Scheduler job `driftline-monitor` remains `ENABLED` on
  `0 */6 * * *` UTC. A manual canary at `2026-08-21T16:37:43Z` returned HTTP
  200 in Cloud Logging on `driftline-00125-2bl`. The post-canary registry read
  reported all five pinned sources `healthy`, with cadence-based next-due
  times (`6h`, `12h`, `24h`) and no source failures.
- Fresh current-revision live agent proof: job `job-33759ee5113c`, workflow
  `52e0ee7c-a806-4132-92fd-43a9a4749864`, `needs_approval`, public source,
  Gemini 3.5 Flash, Google ADK, two allowlisted tools, four artifacts, and
  five audit events. Fresh approval/undo proof: job `job-71eca3498a3f`,
  workflow `e0c28b2d-4e22-43f9-8e94-3d56cc42639e`, persisted packet and
  reversed operational output with both external-write flags false.
- The full local gate passed 250 backend tests, Ruff, frontend production
  build, and diff hygiene. GitHub Actions run `32503511174` passed backend
  tests/lint, frontend build, standalone image build, and repository hygiene.

## 2026-08-21 capability-policy hardening (live)

- Source commit `887ceaa` was deployed by Cloud Build
  `90eed893-e082-4724-85ca-39528f67107c` (`SUCCESS`) as Cloud Run revision
  `driftline-00127-wf9` at 100% traffic. The immutable image digest is
  `sha256:2aa709595bc2c9f37e7fffe6e1c704501afa772145c9b2fda40968b323a7358d`.
- `Permissions-Policy` is now assigned unconditionally by the API middleware;
  a route cannot widen the public browser capability deny-list. The production
  verifier asserts the same deny-list and `Cache-Control: no-store` on health
  and API responses. The local suite passed 252 tests, Ruff, and the frontend
  production build; GitHub Actions run `32505563228` passed all jobs.
- Fresh exact-revision proofs passed: live agent job `job-563c82fb47bf` /
  workflow `e254512d-7085-46fd-94cd-7ed06175ada1`, and approval/undo job
  `job-5b8e690aa57b` / workflow `1aae0abf-1cde-4783-884a-b0719718ff1b`.
  The latter persisted and reversed the packet with external writes false.

## 2026-08-21 Google OIDC tenant-discovery fix (live)

- Source commit `4610a22` was deployed by Cloud Build
  `c17c3151-54a3-430b-931f-036e1630b641` (`SUCCESS`) as Cloud Run revision
  `driftline-00126-zgv` at 100% traffic. The immutable image digest is
  `sha256:132a91d8d9c26cf196cc98a88a91e7a4184d1c06209a4314d23cee3494fa179d`.
- Fixed a real hosted operator defect: the browser's Google Identity Services
  callback sends its short-lived ID token in `Authorization`, while tenant
  discovery previously read only a query field. The route now consumes the
  request-scoped bearer header without placing the token in a URL; a regression
  test covers the header path.
- `scripts/verify_production.sh` passed on this revision with zero recent
  Cloud Run errors. Fresh exact-revision proofs passed: live agent job
  `job-cb310ff6bb06` / workflow `12b67e30-9575-40fe-8061-ed65c98cd24a`, and
  approval/undo job `job-d4aa36eea2c1` / workflow
  `a7a2b536-65ee-4ced-8e0d-d0d486eb1e90`.
- GitHub Actions run `32504592582` passed 251 backend tests, Ruff, frontend
  build, standalone image build, and repository hygiene.

## 2026-08-21 release-proof hardening (live verification)

- The read-only `scripts/verify_production.sh` gate now fails closed unless
  the deployed control plane reports Firestore + async jobs, Google OIDC
  operator auth, durable Firestore tenant membership, tenant-bound credentials,
  no legacy global credential fallback, signed-only external writes, and a
  read-only Salesforce contract. It passed against `driftline-00124-ln5` with
  zero recent Cloud Run errors.
- The packet-safety verifier now requires the same live
  `google_adk`/`gemini-3.5-flash` structured impact and Decision Copilot trace,
  passing deterministic policy review, matching evidence hashes on all four
  artifacts and citations, four reversible packets, and no external write.
  Fresh run: job `job-c09b8c068d9a` / workflow
  `aa77cd13-282a-436a-9929-dcb47ad91cc7`; packet persisted and reversed with
  `external_write=false` and `external_systems_changed=false`.
- A separate fresh live-agent proof passed on job `job-90b4b6737841` /
  workflow `5c48a344-f05e-4655-baf8-02f1ac54809b` with
  `data_mode=public_source`, `needs_approval`, both allowlisted tools, four
  artifacts, five audit events, and two Decision Copilot options. No
  connector write was attempted.
- Local verification passed 248 backend tests, Ruff, and the frontend
  production build. The current serving release is recorded above; older
  release entries below remain append-only historical evidence.

## 2026-08-21 deferred-read UX release (historical serving revision)

- Source commit `7747baa` (`Clarify deferred production reads`) was deployed
  by Cloud Build `ea1e7339-533b-4109-8128-7f166efd1603` (`SUCCESS`, about
  3m01s) as Cloud Run revision `driftline-00124-ln5` at 100% traffic. The
  immutable image digest is
  `sha256:86769ded2dd5d53d3ad585757c957471e53afdefeca0f3a0b0d6f64ec12ab84d`.
- Below-fold source history, freshness, multimodal evidence, change memory,
  value proof, run history, and deployment telemetry now state explicitly that
  their bounded reads load when the panel enters view. This is a copy-level
  truthfulness improvement; connector, policy, and persistence behavior did
  not change.
- `scripts/verify_production.sh` passed on this revision with zero recent
  Cloud Run errors. `scripts/verify_live_agent.sh` created job
  `job-90b4b6737841` / workflow `5c48a344-f05e-4655-baf8-02f1ac54809b` and
  proved `needs_approval`, `public_source`, Gemini 3.5 Flash, Google ADK, two
  allowlisted tools, four artifacts, five audit events, and two decision
  options. `scripts/verify_public_approval_undo.sh` created job
  `job-c09b8c068d9a` / workflow `aa77cd13-282a-436a-9929-dcb47ad91cc7` and
  proved persisted packet -> reversal with both external-write flags false.
- GitHub Actions run `32500963459` passed 248 backend tests, Ruff, the
  frontend production build, standalone image build, and repository hygiene.
  Desktop and mobile Lighthouse navigation on the public alias passed 100 for
  accessibility, best practices, SEO, and agentic browsing (53/53 checks,
  zero failures on each device).
- A current-revision browser journey (job `job-f1bfaa9665c9`, workflow
  `38da400c-5581-47cc-9210-5126061006bc`) completed scan -> approval -> undo.
  The UI rendered the change card, Decision Copilot, four owner actions,
  packet record, and timeline. The undo response persisted
  `action-63355af11e1c35cb5150` as `reversed`, with Jira, Confluence, and
  Slack `external_write=false` in the public packet-safe lane.
- Additional current-revision breadth probes reached `needs_approval` with
  Gemini structured analysis, four impacts, and five events for competitor
  offerings (`job-82ac284398b6`, workflow
  `a1190503-0c2f-4182-83c9-22e4879fc6e1`), competitor narrative/blog
  (`job-b8a7d0ebcf6d`, workflow `7a63eea4-7dec-4626-8b2b-1834a4542716`), and
  own terms (`job-ee66d880b4eb`, workflow
  `d5f75932-3a41-48a8-8765-d629abae9441`).

## 2026-08-21 Gemini structured-impact reliability release (live)

- Source commit `8e71062` (`Prevent Gemini impact analysis truncation`) was
  deployed by Cloud Build `993e7216-0077-4099-8957-0d52e103e9e7` (`SUCCESS`,
  3m09s) as Cloud Run revision `driftline-00123-h4m` at 100% traffic. The
  active gcloud project remained `driftline-hackathon-2026`; no existing
  project was targeted.
- The impact analyst's bounded Gemini output ceiling increased from 1,200 to
  2,400 tokens. The strict Pydantic schema, evidence-hash checks, artifact
  allowlist, and deterministic approval policy are unchanged. This removed a
  real truncation path that could otherwise surface the explicit deterministic
  demo fallback even though the coordinator and tools had run.
- A fresh logged-out browser scan on this revision created job
  `job-294bb65b6ed9` / workflow `3b82535d-14a8-48cc-88b3-24e3e6c3c9f8` and
  visibly rendered `Impact analysis · gemini structured`, a Gemini summary and
  rationale, two Gemini Decision Copilot options, four evidence-bound
  artifacts, and a deterministic human approval gate. The persisted trace
  records `model=gemini-3.5-flash`, `execution_mode=google_adk`, both
  allowlisted tools, and policy `pass`.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors.
  `scripts/verify_live_agent.sh` created job `job-34d426fd0971` / workflow
  `7c9d1281-299b-461f-b393-70334205c9bb` and again proved `needs_approval`,
  `public_source`, Gemini 3.5 Flash, Google ADK, four artifacts, five audit
  events, and two decision options. `scripts/verify_public_approval_undo.sh`
  created job `job-9737925000a9` / workflow
  `b5f6b828-7cd1-4541-b947-bdbb6cbdab52` and proved persisted packet ->
  reversal with `external_write=false` and
  `external_systems_changed=false`.
- GitHub Actions run `32498604630` passed for `8e71062` (248 backend tests,
  Ruff, frontend production build, standalone image, and repository hygiene).
  Desktop and mobile Lighthouse navigation on the public alias passed 100 for
  accessibility, best practices, SEO, and agentic browsing (53/53 checks,
  zero failures on each device).

## 2026-08-21 below-fold request deferral release (live)

- Source commit `5f6833b` (`Clarify deferred panel states`) was deployed by
  Cloud Build `a3f2539a-a6df-4696-9e7d-6a29a5c4506a` (`SUCCESS`, about 3m29s)
  as Cloud Run revision `driftline-00122-kqq` at 100% traffic. The active
  gcloud project remained `driftline-hackathon-2026`; no existing project was
  targeted.
- The console now defers below-fold source history, monitor freshness, visual
  evidence, change memory, value proof, run history, and deployment telemetry
  reads until their panels approach the viewport. Logged-out Chrome QA on the
  public alias observed six initial requests (document, JS, CSS, auth config,
  sources, favicon), then loaded the bounded reads after scrolling into view.
  Deferred copy stayed truthful before loading; after the panels entered view,
  all five source cards reported `Healthy`, and no application alert appeared.
- Desktop and mobile browser checks found no console messages or document
  overflow. At 390x844, body and document widths both equaled 390px; a
  sequential scroll through every deferred panel loaded the ledger, visual
  evidence, memory, value proof, run history, and trust telemetry successfully.
  Lighthouse navigation audits passed 100 for accessibility, best practices,
  SEO, and agentic browsing on both desktop and mobile (53/53 checks, zero
  failures).
- The independent local gate passed 248 backend tests, Ruff, and the frontend
  production build. GitHub Actions run `32497129930` passed for `5f6833b`.
- `scripts/verify_production.sh` passed on this revision with zero recent Cloud
  Run errors. `scripts/verify_live_agent.sh` created job
  `job-2f8c3dee0d57` / workflow `8ee00767-b885-4a60-894f-91be0448b6ea` and
  proved `needs_approval`, `public_source`, `gemini-3.5-flash`, Google ADK,
  both allowlisted tools, four artifacts, five audit events, and two Decision
  Copilot options. `scripts/verify_public_approval_undo.sh` created job
  `job-657e0e6abe70` / workflow `99cb5f0a-81f0-4de8-bf20-6eee0c64effe` and
  proved persisted packet -> reversal with both external-write flags false.
- A direct anonymous `POST /api/agent/run` also persisted a new
  `public_source` Google ADK/Gemini workflow
  `4e3e048f-9488-4db4-89e0-bd568604fe71` with five audit events. The public
  lane made no external connector write.

## 2026-08-21 bounded read performance release (live)

- Source commit `8166f64` (`Speed up bounded source health reads`) was deployed
  by Cloud Build `0487bcd0-0798-4d8a-8ae9-e105aa3384a1` (`SUCCESS`, 3m36s) as
  Cloud Run revision `driftline-00120-xnw` at 100% traffic. The active gcloud
  project remained `driftline-hackathon-2026`; no existing project was targeted.
- Firestore history reads now request only the newest bounded page, and the
  five-source monitor/memory panels share one client and overlap only their
  allowlisted reads. Direct public measurements after the rollout were
  approximately `0.94s` for `/api/monitor/registry`, `0.91s` for
  `/api/memory/summary?limit=50`, and `0.26s` for the selected source history,
  compared with the earlier cold-path pressure trace of roughly `4.5s`, `4.3s`,
  and `2.2s` respectively. The append-only and tenant boundaries are unchanged.
  `/health` is now explicitly `Cache-Control: no-store`.
- GitHub Actions run `32495446128` passed for `8166f64` (248 backend tests,
  Ruff, frontend production build, standalone image, and repository hygiene).
  `scripts/verify_production.sh` passed against `driftline-00120-xnw`, including
  IAM, Artifact Registry retention, scheduler, Cloud Tasks, uptime, dashboard,
  and zero recent Cloud Run errors.
- Sequential live proofs on this exact revision created job
  `job-bf4c55cea0f1` / workflow `578e6409-e195-4188-84b6-59c75fd5598a` and
  proved `needs_approval`, `public_source`, `gemini-3.5-flash`, Google ADK,
  both allowlisted tools, four artifacts, five audit events, and two structured
  Decision Copilot options. The separate packet-safety proof created job
  `job-f198ece08fb3` / workflow `acdceb49-b9c8-4ace-8f3f-3ce1cbd6bebd` and
  proved persisted packet -> reversal with both external-write flags false.
- A direct anonymous `POST /api/agent/run` on this revision returned
  `execution_mode=google_adk`, `model=gemini-3.5-flash`,
  `data_mode=public_source`, `persisted=true`, the two allowlisted tools,
  `gemini_structured` analysis and Decision Copilot traces, policy `pass`, and
  two options (workflow `2155fec0-d09d-48b6-8861-fa7715768d82`).
- Fresh Chrome QA on the public alias found no console messages. Lighthouse
  navigation remained 100 for accessibility, best practices, SEO, and agentic
  browsing with 58/58 checks passed; at a 390px emulated viewport document and
  body widths both equaled the viewport and horizontal overflow remained
  clipped. The public lane stayed packet-only and no external connector was
  called.

## 2026-08-21 final live pressure pass (current revision)

- `scripts/verify_production.sh` passed against `driftline-00119-xck`: the
  isolated project, Firestore persistence, asynchronous Cloud Tasks, signed
  scheduler, uptime check, alert policy, and zero recent Cloud Run errors were
  all confirmed.
- The proofs were run sequentially to avoid source-job deduplication hiding a
  boundary: `scripts/verify_live_agent.sh` created job
  `job-d65cdc6bc772` / workflow `4a88bf26-8703-4101-a4c9-ffcd7e88bb26` and
  directly proved `status=needs_approval`, `data_mode=public_source`,
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, both allowlisted
  tools, four artifacts, five audit events, and two Decision Copilot options.
  The separate packet-safety verifier created job `job-9d822a772cee` /
  workflow `f1d3b824-e7d3-4092-b422-30da31bad164` and proved persisted
  packet → reversal with `external_write=false` and
  `external_systems_changed=false`.
- In logged-out Chrome on the public alias, the real UI **Approve action plan**
  transition recorded a packet and the **Reopen decision** transition returned
  to the deterministic gate with the visible status
  `Decision reopened · no external systems were changed`. Desktop and mobile
  checks found no document overflow; the current page had no console messages.
  Lighthouse snapshot checks were 100 for accessibility, best practices, SEO,
  and agentic browsing on both device profiles (40/40 each).
- This pass made no connector call and no external-system mutation. The public
  lane remains packet-only by design.
- A least-privilege IAM audit found an obsolete conditional project-level
  `roles/secretmanager.secretVersionAdder` grant on the shared runtime for the
  legacy `driftline-sf-driftline-demo` secret. It was removed from
  `driftline-hackathon-2026`; the runtime now retains only its intended
  project roles (`roles/aiplatform.user`, `roles/datastore.user`, and
  `roles/cloudtasks.enqueuer`). The per-tenant impersonated identity still
  owns the exact connector-secret accessor/version-adder grants provisioned by
  `scripts/provision_tenant_connector_secrets.sh`. `/health` remained 200
  immediately after the change, and `scripts/verify_production.sh` now fails
  closed if a future release reintroduces any project-level
  `roles/secretmanager.*` grant for the shared runtime.
- Artifact Registry was rechecked at 75 image versions and approximately
  8.66 GB before cleanup. The retention policy is now active with dry-run
  disabled; 65 older exact digests were deleted after verifying that the
  serving digest `sha256:2c1a03c2a010f50d6031097823cfe9ffe9b5b318fd8f843680a1e3042ba53403`
  was in the newest ten. Exactly 10 rollback candidates remain; the current
  displayed repository size is 7.67 GB while blob garbage collection catches
  up. The private Cloud Storage artifact bucket was also confirmed with the
  Driftline production labels. The production verifier now checks that the
  repository cleanup policy remains active with dry-run disabled.
- Post-cleanup smoke remained green: `scripts/verify_production.sh` still
  reported revision `driftline-00119-xck`, 100% traffic, no recent Cloud Run
  errors, and the new IAM/retention checks. A fresh live ADK/Gemini proof then
  created job `job-ed93c4af7c56` / workflow
  `cf2eb65d-6a24-4c74-a212-c43d780911bf` with the same model, tools, artifacts,
  audit events, and `needs_approval` contract. The separate packet-safety
  proof created job `job-d136450305b6` / workflow
  `d5d64316-12c0-4c1c-a977-323a048df5d4` and again proved persisted packet →
  reversal with both external-write flags false.

## 2026-08-21 Gemini structured-output resilience release (live)

- Source commit `d9cbba4` (including the mobile operator sign-in visibility
  fix from `e07a4c3`) was deployed by Cloud Build
  `7ab4cf4e-89ad-4feb-a3e5-77d205d3db09` (`SUCCESS`, 3m36s) as Cloud Run
  revision `driftline-00119-xck` at 100% traffic.
- A fresh browser scan on the preceding revision exposed an intermittent
  Gemini response with `summary` wrapped as an object, which correctly took
  the UI's visible deterministic fallback. The final analyst hardening keeps
  the first two attempts strict, then on the third and final bounded attempt
  unwraps only a known single-key `{text|value|content}` envelope for the two
  display-only fields before applying the unchanged evidence/artifact policy
  validator. Unknown shapes still fail closed. The local suite now reports
  `247 passed`; the regression covers both transient repair and persistent
  wrapper output.
- Two fresh logged-out browser scans on this exact revision both displayed
  `Gemini impact analysis` and a Gemini Decision Copilot with no deterministic
  impact fallback. The live agent trace showed `gemini-3.5-flash`, Google ADK,
  both allowlisted tools, four artifacts, five audit events, and the
  deterministic `needs_approval` gate.
- `scripts/verify_production.sh` passed with Firestore persistence, async
  tasks, scheduler/uptime monitoring, and zero recent Cloud Run errors.
  `scripts/verify_live_agent.sh` created job `job-280ccb206fb2` / workflow
  `2072fcea-2360-47c5-9769-1d258769d57e`; the credential-free
  `scripts/verify_public_approval_undo.sh` created job `job-d7b39f3a9e44` /
  workflow `7067534b-9f5f-4245-b219-b786ef2ed1ab` and proved
  `packet=persisted`, `operational_output=reversed`, `external_write=false`,
  and `external_systems_changed=false`.
- The live multimodal probe on this revision returned
  `data_mode=public_source`, `mode=gemini_vision`,
  `model=gemini-3.5-flash`, `material_change=true`, `confidence=1.0`, and
  evidence hash
  `a78e9f0acb5b471a9500a51bb462c52aa8a13f021f0f48886105e4924523d250`.
- GitHub Actions run `32491820540` passed for source `d9cbba4` across backend
  tests/lint, frontend build, standalone lockfile-pinned image, and shell
  release-helper hygiene.

## 2026-08-21 lazy operator identity and resilient copilot release (live)

- Source commit `558dd20` was deployed by Cloud Build
  `0092680e-68f3-4293-9592-787bf70c05bc` (`SUCCESS`, 3m04s) as Cloud Run
  revision `driftline-00117-8l4` at 100% traffic. The active gcloud project
  and dedicated runtime identity remained
  `driftline-hackathon-2026` /
  `driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com`.
- Google Identity Services is now lazy-loaded only after an explicit
  **Sign in with Google** action. A fresh anonymous navigation requested no
  `accounts.google.com` resources or iframe, while the click path loaded the
  real GIS script and provider button on demand. This keeps the packet-safe
  judge lane free of an unnecessary third-party cookie without weakening the
  signed operator path. No browser console errors or warnings were recorded
  in either state.
- Fresh logged-out Chrome QA at 1440x900 and 390x844 found document width
  equal to the viewport (1440px and 390px), a fully visible vertical impact
  graph, and a non-clipping mobile sign-in trigger. Lighthouse navigation
  scored 100 for accessibility, best practices, SEO, and agentic browsing on
  both desktop and mobile (58/58 checks, 0 failures).
- GitHub Actions run `32490298913` passed for source `558dd20` across backend
  tests/lint, frontend production build, standalone lockfile-pinned image,
  and shell release-helper hygiene.
- `scripts/verify_production.sh` passed on this revision with Firestore
  persistence, asynchronous tasks, enabled scheduler/uptime monitoring, and
  zero recent Cloud Run errors. `scripts/verify_live_agent.sh` created job
  `job-217f63827d5b` / workflow
  `4c5ee096-e579-4ac7-8994-e83402ff6122` and proved
  `gemini-3.5-flash`, Google ADK, both allowlisted tools, four artifacts, five
  audit events, two decision-copilot options, and the deterministic
  `needs_approval` gate.
- `scripts/verify_public_approval_undo.sh` separately created job
  `job-69aad98115aa` / workflow `166730c9-1247-467b-8ce8-5ea7945c89cc` and
  proved `packet=persisted`, `operational_output=reversed`,
  `external_write=false`, and `external_systems_changed=false`.
- The live multimodal route returned `data_mode=public_source` and the
  Gemini vision route returned `mode=gemini_vision`,
  `model=gemini-3.5-flash`, `material_change=true`, `confidence=1.0`, and
  evidence hash
  `a78e9f0acb5b471a9500a51bb462c52aa8a13f021f0f48886105e4924523d250`.

## 2026-08-21 responsive judge-surface release (live)

- Source commit `a78733a` was deployed by Cloud Build
  `717b402a-355d-4009-8b14-2c67e2a5cc81` (`SUCCESS`, 3m05s) as Cloud Run
  revision `driftline-00115-2dm` at 100% traffic. The release fixes the
  desktop Google Identity button/workspace-label collision at the default
  1440px judge viewport and converts the five-stage impact graph to a readable
  vertical sequence on tablet/mobile instead of an undiscoverable horizontal
  scroller.
- `scripts/verify_production.sh` passed on this exact revision with Firestore
  persistence, async jobs, enabled scheduler/tasks, uptime check, alert policy,
  and zero recent Cloud Run errors. A fresh `scripts/verify_live_agent.sh`
  created job `job-6e4a0ea771e3` / workflow
  `f5e50006-1d6f-470f-8e54-9f17c9f6495f` and proved
  `gemini-3.5-flash`, Google ADK, both allowlisted tools, four artifacts, five
  audit events, two decision-copilot options, and the deterministic
  `needs_approval` gate.
- `scripts/verify_public_approval_undo.sh` separately created job
  `job-529cbf59b1ad` / workflow `bbc40bfd-5de2-44ec-a654-f1230615a560` and
  proved a persisted packet followed by a durable reversal with
  `external_write=false` and `external_systems_changed=false`.
- The live multimodal route returned `data_mode=public_source` for the pinned
  before/after pair, and Gemini vision returned
  `mode=gemini_vision`, `model=gemini-3.5-flash`,
  `material_change=true`, `confidence=1.0`, and evidence hash
  `a78e9f0acb5b471a9500a51bb462c52aa8a13f021f0f48886105e4924523d250`.
- GitHub Actions run `32488146746` passed for source `a78733a` across backend
  tests/lint, frontend production build, standalone lockfile-pinned image,
  and shell release-helper hygiene. Local frontend build and `git diff --check`
  also passed. Logged-out Chrome QA at 1440×900 and 390×844 found no document
  overflow or application console errors; the worklist table remains an
  intentional horizontal-scroll region for its dense columns. Lighthouse
  snapshots remain 100 for accessibility, best practices, SEO, and agentic
  browsing.

## 2026-08-21 public-console clarity and resilient proof release (live)

- Source commit `ec65176` was deployed by Cloud Build
  `aa5659ff-045f-44e2-ac47-e24add7a2d76` (`SUCCESS`, 3m14s) as Cloud Run
  revision `driftline-00111-xr2` at 100% traffic. The anonymous console now
  labels the pre-run evidence as a deterministic fixture rather than a
  preview, shows only the latest three tenantless runs, and makes the signed
  tenant history boundary explicit. After approval, the owner queue reports
  closed versus outstanding work; no synthetic data is hidden or relabeled as
  customer activity.
- `scripts/verify_production.sh` passed with Firestore persistence, async
  jobs, scheduler/tasks, monitoring, and zero recent Cloud Run errors. The
  hardened `scripts/verify_live_agent.sh` passed after a fresh bounded run:
  job `job-0bdc79f38683` / workflow
  `08342970-299c-480f-8827-bb68582c91ac` reached `needs_approval` through
  `gemini-3.5-flash`, Google ADK, both allowlisted tools, four artifacts, and
  five audit events. The verifier now retries a permitted deterministic
  anonymous fallback up to three bounded runs, but still fails unless a real
  Gemini structured turn is proven.
- The same deployed workflow completed an approval → private Cloud Storage
  packet → undo journey. Approval returned `storage_status=persisted`,
  `operational_status=active`, `external_write=false`, and
  `external_systems_changed=false`; undo returned `status=needs_approval`,
  persisted a rollback marker, and kept external systems unchanged.
- The credential-free `scripts/verify_public_approval_undo.sh` reproduced that
  public packet-safety contract on a fresh workflow: job
  `job-65a058652155` / workflow `a8bbf0df-40d4-4004-befe-e570459ab673` passed
  approval → persisted packet → undo. The final response reported
  `storage_status=persisted`, `operational_status=reversed`,
  `external_write=false`, and `external_systems_changed=false`; no connector
  credential or third-party write was involved.
- After the verifier received clearer timeout diagnostics, a second fresh run
  also passed: job `job-bf2ff1ed5385` / workflow
  `a801162e-eae5-40c9-a4b0-3fc7e6cf8e8a` returned
  `packet=persisted`, `operational_output=reversed`,
  `external_write=false`, and `external_systems_changed=false`.
- GitHub Actions run `32483785937` passed for source `ec65176`; local
  verification for this source also passed 244 backend
  tests, Ruff, the frontend production build, and `git diff --check`.
- GitHub Actions run `32485267469` passed for repository HEAD `7728ed6`
  (backend tests/lint, frontend production build, standalone lockfile-pinned
  image, and shell release-helper hygiene).
- A final control-plane check passed against the same serving revision:
  `scripts/verify_production.sh` reported Firestore persistence, running
  scheduler/tasks, enabled monitoring, and zero recent Cloud Run errors. A
  fresh `scripts/verify_live_agent.sh` run proved job `job-b3bd92a2bece` /
  workflow `9ac6363b-dbcd-4f53-87d8-dabebe496b69` reached `needs_approval`
  through `gemini-3.5-flash`, Google ADK, both allowlisted tools, four
  artifacts, and five audit events.
- Fresh logged-out Chrome QA against the live alias verified the new copy,
  three-row public history, live scan, Gemini trace, and no console errors.
  At 390×844 mobile width, body/document scroll width remained 390px and the
  Lighthouse snapshot scored 100 for accessibility, best practices, SEO, and
  agentic browsing.

## 2026-08-21 public quota and dual-Gemini proof release (live)

- Source commit `e68b55b` was deployed by Cloud Build
  `277d5f06-cac9-4395-bc90-3d1682f1260b` (`SUCCESS`, 3m01s) as Cloud Run
  revision `driftline-00112-v69` at 100% traffic. The anonymous evaluation
  lane now has its own bounded `20 calls / 3600s` Gemini bucket, separate from
  the signed tenant allowance of `10 calls / 3600s`; this prevents repeated
  evaluator runs from starving an authenticated pilot without opening an
  unbounded public model proxy.
- `scripts/verify_production.sh` passed on the new revision with Firestore,
  async tasks, monitoring, and zero recent Cloud Run errors. The strengthened
  `scripts/verify_live_agent.sh` passed job `job-1fbf4e290e68` / workflow
  `58972084-55c9-46a9-b443-613d951ea9bc` through the real coordinator,
  evidence-bound Gemini impact analyst, Gemini decision copilot (2 options),
  Google ADK, both allowlisted tools, four artifacts, five audit events, and
  the deterministic `needs_approval` gate.
- `scripts/verify_public_approval_undo.sh` passed independently on job
  `job-f9979a4981c4` / workflow `2ec4f44a-4349-4011-996c-dae2b0ae1b71`:
  approval persisted the private packet, undo persisted the reversal, and the
  final response retained `external_write=false` and
  `external_systems_changed=false`.
- The live multimodal lane also passed on this revision: the public visual
  evidence route returned `data_mode=public_source` for the pinned before/after
  assets, and `POST /api/multimodal/analyze` returned
  `mode=gemini_vision`, `model=gemini-3.5-flash`, `material_change=true`, and
  `confidence=1.0` for evidence hash
  `a78e9f0acb5b471a9500a51bb462c52aa8a13f021f0f48886105e4924523d250`.
- GitHub Actions run `32485900320` passed for source `e68b55b` (245 backend
  tests, Ruff, frontend production build, standalone lockfile-pinned image,
  and shell release-helper hygiene).

## 2026-08-21 production-lane and judge-proof release (live)

- Source commit `810283f` was deployed by Cloud Build
  `9498f5c2-3f5e-4c0b-aad9-4fa85167d94d` (`SUCCESS`, 3m12s) as Cloud Run
  revision `driftline-00109-7qj` at 100% traffic. Before a scan exists, the
  workflow timeline now says `Ready to start` instead of implying that a
  monitor job is already running.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors. A
  fresh `scripts/verify_live_agent.sh` run proved job `job-2f590b23212c` /
  workflow `5016d631-d63d-49f2-9ff0-6b1e1bc428fb` reached `needs_approval`
  through `gemini-3.5-flash`, Google ADK, both allowlisted tools, four
  artifacts, and five audit events.

- Source commit `cd9776d` was deployed by Cloud Build
  `7930269a-915a-4a65-bb4d-693e276d4ad2` (`SUCCESS`, 3m17s) as Cloud Run
  revision `driftline-00108-f42` at 100% traffic. Built-in source definitions
  and workflow defaults now remain pinned even when environment overrides are
  absent; the regression suite explicitly rejects GitHub `main` fixture URLs.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors. A
  fresh `scripts/verify_live_agent.sh` run proved job `job-d76dae51ef94` /
  workflow `4e2d9523-9834-4778-93f7-de991d3ac93c` reached `needs_approval`
  through `gemini-3.5-flash`, Google ADK, both allowlisted tools, four
  artifacts, and five audit events. The persisted evidence URL was the
  immutable `19fc1e2` fixture.

- Source commit `7913c37` was deployed by Cloud Build
  `2f5b0c1b-057b-459d-a72b-759a1310d32a` (`SUCCESS`, 3m06s) as Cloud Run
  revision `driftline-00107-pr6` at 100% traffic. The pre-scan evidence link
  is now pinned to the same immutable competitor fixture commit used by the
  runtime, so the judge path cannot drift before the first click.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors. A
  fresh `scripts/verify_live_agent.sh` run proved job `job-4f477d45abd4` /
  workflow `706f0b5c-b70e-4978-9663-bd4a97dda88c` reached `needs_approval`
  through `gemini-3.5-flash`, Google ADK, both allowlisted tools, four
  artifacts, and five audit events.

- Source commit `a2b66f4` was deployed by Cloud Build
  `7ab6adb1-7b82-4244-b3b4-cd4c2b893b54` (`SUCCESS`, 3m21s) as Cloud Run
  revision `driftline-00106-7k7` at 100% traffic. The agent trace now shows
  the completed allowlisted work in plain language: inspect the registered
  source and read the Firestore workflow state; the rail explicitly labels
  these calls read/state-only.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors. A
  fresh `scripts/verify_live_agent.sh` run proved job `job-12fbcb7ab454` /
  workflow `655fb48c-9411-46d2-b01a-5c653e983ce0` reached `needs_approval`
  through `gemini-3.5-flash`, Google ADK, both allowlisted tools, four
  artifacts, and five audit events.
- A fresh logged-out Chrome pass against the current public alias completed the
  scan at desktop semantics and at a 390px mobile viewport. The new agent-work
  rail was visible with no console warnings/errors; mobile body and document
  scroll width both remained 390px, and Lighthouse snapshot scored 100 for
  accessibility, best practices, SEO, and agentic browsing.

- Source commit `efc37db` was deployed by Cloud Build
  `ab382c57-979e-4db0-99ee-5818575daa49` (`SUCCESS`, 3m03s) as Cloud Run
  revision `driftline-00105-cw4` at 100% traffic. The active gcloud project
  was verified as `driftline-hackathon-2026` before deployment.
- The public evaluation lane now exposes the production-facing
  `public_evaluation_packet_only` scope and records the durable output as a
  `firestore_change_packet`; legacy sandbox scope values remain accepted only
  for backwards-compatible persisted/local identities. This is a naming and
  contract clarity change, not a claim of third-party writes.
- `scripts/verify_production.sh` passed with Firestore persistence, async jobs,
  scheduler/tasks, monitoring, and zero recent Cloud Run errors. A fresh
  `scripts/verify_live_agent.sh` run proved job `job-46795fbe6b7b` /
  workflow `4df6bb1b-6122-4573-92aa-4be0c0330fb2` reached `needs_approval`
  through `gemini-3.5-flash`, Google ADK, both allowlisted tools, four
  artifacts, and five audit events. A public approval on that workflow
  persisted `firestore_change_packet` with `storage_status=persisted`,
  `external_write=false`, and `external_systems_changed=false`.
- GitHub Actions run `32479849233` passed all repository checks for this exact
  source commit. The new [`submission/JUDGE_SCORECARD.md`](../submission/JUDGE_SCORECARD.md)
  maps the official 40/30/30 judging weights to the live journey and exact
  release commands.

## 2026-08-21 immutable fixture release (live)

- Source commit `25a1bd3` was deployed by Cloud Build
  `3b82b514-b213-4106-aec2-4d337b574431` (`SUCCESS`) as Cloud Run revision
  `driftline-00104-8vc` at 100% traffic.
- Production now pins all five public source URLs to immutable GitHub commits:
  own pricing/terms remain pinned to `a48f7eb`, and competitor pricing,
  offering, and blog fixtures are pinned to `19fc1e2`. This removes branch
  drift from the judge workflow and the reproducibility scripts.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors. A
  fresh `scripts/verify_live_agent.sh` run proved job `job-934ea8ae11a7` /
  workflow `4f5bbaf9-d3a7-4372-857f-ae3cd52821ea` reached `needs_approval`
  through `gemini-3.5-flash`, Google ADK, both allowlisted tools, four
  artifacts, and five audit events.

## 2026-08-21 public scan race-closure release (live)

- Source commit `19fc1e2` was deployed by Cloud Build
  `0e2f0979-d355-4f4d-8069-eac5bf8c666d` (`SUCCESS`) as Cloud Run revision
  `driftline-00103-p6d` at 100% traffic.
- The public deduplication check, quota reservation, and enqueue now share a
  process-local critical section, closing the concurrent refresh race while
  durable Firestore job claims continue to protect cross-instance deliveries.
- A fresh live pair for `public/terms` returned the same job
  `job-f19c5ab37d65`; the second response explicitly returned
  `deduplicated=true`. `scripts/verify_production.sh` passed with zero recent
  Cloud Run errors.
- The live agent verifier then proved job `job-35d0bad97d36` / workflow
  `8aea1601-0a83-4763-9b44-aa2ea73b2ad1` reached `needs_approval` through
  Gemini 3.5 Flash and Google ADK with both allowlisted tools, four artifacts,
  and five audit events.

## 2026-08-21 public scan deduplication release (live)

- Source commit `251fa68` was deployed by Cloud Build
  `44eb8716-68e9-45be-890c-b17843de78dd` (`SUCCESS`) as Cloud Run revision
  `driftline-00102-ktk` at 100% traffic.
- The public scan seam now reuses an active anonymous job for the same
  allowlisted source instead of enqueueing duplicate Gemini work behind the
  one-concurrent Cloud Tasks queue. A live production probe returned the same
  job `job-77ca8e415b01` with `deduplicated=true` on the second request.
- `scripts/verify_production.sh` passed with zero recent Cloud Run errors. The
  live agent verifier then proved job `job-77ca8e415b01` / workflow
  `ccb90a0e-93a3-4b50-8995-07ce7312941b` reached `needs_approval` through
  `gemini-3.5-flash`, Google ADK, both allowlisted tools, four artifacts, and
  five audit events.

## 2026-08-21 isolated Google operator OAuth release (live)

- Source commit `302f151` was deployed by Cloud Build
  `ba2fe2e4-1114-45c8-9263-675a6c9b905c` (`SUCCESS`) as Cloud Run revision
  `driftline-00101-sm7` at 100% traffic.
- A new **Driftline production operator** Web application OAuth client was
  created in `driftline-hackathon-2026` with the Cloud Run origin
  `https://driftline-xvxczqg62a-uc.a.run.app`; no client secret was committed,
  logged, or used by the browser GIS flow.
- `/api/auth/config` now returns the new project-owned client ID and
  `credential_values_exposed=false`. A fresh Chrome browser loaded the GIS
  button with that client and opened the Google account sign-in page without
  the prior `invalid_client / no registered origin` error. Completing Google
  account selection/consent and obtaining a tenant token remains an external
  identity step; no authenticated connector claim is based on this browser
  probe alone.
- `/health` and `scripts/verify_production.sh` passed with zero recent Cloud
  Run errors. The public packet-safe lane remains live and unchanged.

## 2026-08-21 reproducible live-agent proof

- `scripts/verify_live_agent.sh` ran against the public revision after the
  isolated OAuth release. It creates one bounded, identity-free public-source
  job and fails closed unless the returned workflow proves the live model and
  agent path rather than the deterministic fallback.
- The run completed with job `job-850ac743c8af` and workflow
  `56cc8d5c-20df-469f-8628-706cca1de3c5` at `needs_approval`.
- Direct response evidence proved `data_mode=public_source`,
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, structured analysis
  mode `gemini_structured`, allowlisted tools
  `inspect_source_change,get_workflow_state`, four mapped artifacts, and five
  audit events. The verifier performs no approval and no external connector
  write.
- The same deployed path then completed a public approval → persisted packet →
  undo journey on workflow `671877de-a901-4919-b764-359e8c9b7fbc` (job
  `job-d799b1e1fef6`). Approval persisted four owner-review action items and a
  Cloud Storage packet; undo returned the workflow to `needs_approval`, wrote a
  rollback artifact, appended `decision_reopened`, and reported
  `external_systems_changed=false`. This proves the reversible operational
  loop without claiming a third-party write.

## 2026-08-21 stale-session isolation release (live)

- Source commit `1814bad` was deployed by Cloud Build
  `63b0d1de-f83d-4fa1-8cbd-5f8fb1b99a69` (`SUCCESS`) as Cloud Run revision
  `driftline-00100-f7x` at 100% traffic.
- The browser now attaches a session generation to scans, approval decisions,
  undo/dismiss requests, retries, history, source registry, and health reads.
  A response started under a prior tenant or signed-out session is discarded
  instead of repopulating the current console.
- The fresh public browser completed a deployed Gemini scan in 11 seconds,
  rendered the verified evidence-bound decision card, four mapped artifacts,
  and the deterministic human gate; it reported no browser alerts and no
  horizontal overflow. `/health` and `scripts/verify_production.sh` passed,
  with zero recent Cloud Run errors. Local verification remained 242 tests,
  Ruff, frontend production build, and `git diff --check` passing.

## 2026-08-21 tenant-switch isolation release (live)

- Source commit `330a534` was deployed by Cloud Build
  `ff3ee862-47d1-4677-a962-0e720d91e9b0` (`SUCCESS`) as Cloud Run revision
  `driftline-00099-ztd` at 100% traffic.
- Tenant switches and sign-out now clear the previous workflow, job, source
  selection, decision routes, and connector context from the browser before a
  new tenant can act. The connector panel also clears its aggregate read state
  whenever the tenant ID changes.
- The deployed browser completed a fresh competitor pricing scan with Gemini
  structured analysis, four evidence-bound artifacts, the deterministic human
  gate, no browser alerts, and no horizontal overflow. `/health` and the
  production verifier passed; the local suite remains 242 tests passed.

## 2026-08-21 authenticated connector context release (live)

- Source commit `0a22b9d` was deployed by Cloud Build
  `8f799fba-8cbb-4ab8-986b-d69b8cb5f309` (`SUCCESS`) as Cloud Run revision
  `driftline-00098-hmc` at 100% traffic.
- The signed operator console now exposes an explicit **Refresh context**
  control beside the handoff destinations. It performs a request-scoped,
  aggregate-only read of connector context and binding health before an
  operator approves a downstream action; raw records and credentials never
  enter the browser.
- The anonymous lane remains unchanged and packet-safe. A fresh deployed
  browser run completed the competitor pricing scan with `gemini_structured`,
  four evidence-bound surfaces, and no browser alerts or horizontal overflow.
- `/health`, the production verifier, local tests (242 passed), Ruff, the
  frontend production build, and `git diff --check` all passed.

## 2026-08-21 trust copy and connector-status clarity release (live)

- Source commit `28a8c75` was deployed by Cloud Build
  `c62bfffa-314d-42c3-83d3-ebb281d2309b` (`SUCCESS`) as Cloud Run revision
  `driftline-00089-cwj` at 100% traffic.
- The live trust panel now distinguishes an actually created/reused/reversed
  Jira handoff from unchanged destinations, instead of implying that a Jira
  write leaves every customer system unchanged.
- Connector telemetry now says `available` and explicitly notes that
  deployment capability is not proof of per-tenant credentials or an external
  write. This keeps the public evaluation lane accurate for prepared-only
  connectors.
- `/health` returned 200, `scripts/verify_production.sh` passed, and the fresh
  browser loaded the revised copy with no console errors or warnings.

## 2026-08-21 source schedule visibility release (live)

- Source commit `de94a27` was deployed by Cloud Build
  `5826f7d2-7f35-4c88-b9ef-396b0015067d` (`SUCCESS`) as Cloud Run revision
  `driftline-00090-kt9` at 100% traffic.
- The source registry now surfaces each source's last observation and next
  scheduled observation using the existing append-only freshness ledger. This
  makes the always-on monitor cadence visible without inventing a fetch or
  mutating source history.
- The live browser confirmed the five pinned sources display healthy status,
  last-observed timestamps, and next-due timestamps with no console errors or
  warnings. `/health` and `scripts/verify_production.sh` both passed.

## 2026-08-21 owner-action utility metrics release (live)

- Source commit `4ac141d` was deployed by Cloud Build
  `d6049daf-775d-4e47-ad21-93b4db447763` (`SUCCESS`) as Cloud Run revision
  `driftline-00091-bnm` at 100% traffic.
- `/api/ops/value-proof` now reports evidence-backed owner-action cycle-time
  p50/p90 values from append-only `created_at` → `completed_at` records. The
  public panel labels these as observed deployment telemetry and continues to
  keep customer ROI, revenue, retention, and willingness-to-pay explicitly
  unmeasured.
- Live API evidence returned an owner-action cycle sample of `n=5`, p50
  `115.7s`, and p90 `128.9s`; the browser displayed the same values with no
  console errors or warnings. This is operational timing, not customer time
  saved.
- The full local gate passed (241 backend tests, Ruff, frontend build, and
  `git diff --check`); `/health` and `scripts/verify_production.sh` passed.

## 2026-08-21 source-health loading truthfulness release (live)

- Source commit `2b14abe` was deployed by Cloud Build
  `1d76c3b6-3e1c-450c-bc37-45917b81b52f` (`SUCCESS`) as Cloud Run revision
  `driftline-00092-9cn` at 100% traffic.
- The source registry now distinguishes `Checking freshness` from a real
  `needs_baseline` result while the monitor ledger request is in flight, and
  reports `Freshness unavailable` if that request fails. It no longer flashes
  a false baseline state during first paint.
- The deployed browser settled on all five sources as healthy with
  last-observed and next-due timestamps, with no console errors or warnings;
  `/health` and the production verification script passed.

## 2026-08-21 below-fold visual performance release (live)

- Source commit `e7afc28` was deployed by Cloud Build
  `64601726-5e7f-4de7-8137-ce64f53e5d7a` (`SUCCESS`) as Cloud Run revision
  `driftline-00088-jn6` at 100% traffic.
- Multimodal before/after evidence images are now browser-lazy-loaded instead
  of eager-loaded. This keeps the visual evidence available in the live source
  panel while avoiding unnecessary initial transfer before a reviewer reaches
  that below-fold section.
- `/health` returned 200, the production verification script passed, and the
  browser confirmed both visual images have `loading=lazy` with no errors or
  warnings.

## 2026-08-21 production lane clarity release (live)

- Source commit `0aef33d` was deployed by Cloud Build
  `042c0406-4001-49d3-92dc-2fe9f5da38bd` (`SUCCESS`) as Cloud Run revision
  `driftline-00087-p74` at 100% traffic.
- The public console now calls itself the `Public evaluation lane` and
  `Packet-safe evaluation`: it is a live production-backed lane with
  allowlisted sources and deterministic approval, while external connector
  writes remain restricted to signed authenticated operators. This is a copy
  clarification, not a relaxation of the safety boundary.
- `/health` returned HTTP 200 after deployment; the fresh browser loaded the
  new copy with no console errors or warnings; the active-revision error log
  query was empty.

## 2026-08-21 reproducible production verification (live)

- Read-only `scripts/verify_production.sh` passed with the active gcloud
  project explicitly set to `driftline-hackathon-2026`.
- The check confirmed Cloud Run revision `driftline-00092-9cn` at 100% traffic,
  Firestore-backed `/health`, enabled Scheduler, a running Cloud Tasks queue
  with one concurrent dispatch and three attempts, the live uptime check and
  alert policy, the production dashboard, and zero severity `ERROR` entries in
  the last 15 minutes.
- The script refuses to run against another gcloud project and performs no
  writes or secret reads, making the release gate safe to rerun during handoff
  or cleanup.

## 2026-08-21 static asset cache safety release (live)

- Source commit `cce8e4d` was deployed by Cloud Build
  `5405921b-de1e-4b4f-ac28-647c371cdb87` (`SUCCESS`) as Cloud Run revision
  `driftline-00086-77b` at 100% traffic. The isolated project remained the
  active gcloud target throughout the release.
- Fingerprinted JavaScript/CSS assets return
  `Cache-Control: public, max-age=31536000, immutable`; missing `/assets/*`
  responses do not receive an immutable cache header, preventing a transient
  404 from being pinned by an intermediary.
- `/health` returned `status=ok`, Firestore persistence, and async jobs. Cloud
  Logging showed no application errors for the active revision. The full local
  gate passed: 241 backend tests, Ruff, `git diff --check`, and the frontend
  production build.

## 2026-08-21 always-on monitor canary (live)

- The isolated Cloud Scheduler job `driftline-monitor` is `ENABLED` on the
  `0 */6 * * *` UTC schedule and targets `/api/scheduler/tick` with the
  dedicated `driftline-scheduler` OIDC identity.
- A manual canary at `2026-08-21T08:38:11Z` returned HTTP 200. Cloud Logging
  recorded the Scheduler request and Cloud Tasks worker deliveries, and all
  five bounded monitor jobs (`public/pricing`, `public/terms`,
  `competitor/pricing`, `competitor/offerings`, `competitor/blog`) completed
  with no terminal failures. This is direct evidence of the background path,
  not a UI-only simulation.
- The monitor remains intentionally bounded to the five pinned public fixtures
  in the public console; arbitrary competitor crawling and private source
  access are not claimed.

## 2026-08-21 production liveness monitoring (live)

- Cloud Monitoring uptime check `driftline-health`
  (`projects/driftline-hackathon-2026/uptimeCheckConfigs/driftline-health-Hmxqs16MUkY`)
  is configured for HTTPS `GET /health`, HTTP 200, the
  `"status":"ok"` response marker, a five-minute period, ten-second timeout,
  SSL validation, and three regions (USA Iowa, Europe, Asia Pacific).
- Alert policy `Driftline health check failing`
  (`17375876853888551854`) is enabled with the same Driftline labels and a
  30-minute auto-close. It has no notification channel by design, so this
  monitoring addition does not send email or external messages; operators can
  inspect incidents in the isolated project.
- The check and policy are reproducible from
  `infra/monitoring/driftline-health-alert.json`. The first metric point may
  take several minutes after creation; the authoritative configuration above
  is already confirmed in Cloud Monitoring.
- A post-creation Monitoring API query returned two active checker series and
  twelve observed `check_passed=true` points for
  `driftline-health-Hmxqs16MUkY` in the current window. The third configured
  region may publish on a different sampling boundary; no failure point was
  observed.

## 2026-08-21 production operations dashboard (live)

- Cloud Monitoring dashboard `Driftline production control plane`
  (`projects/724959673622/dashboards/9f00a615-b74c-4567-aae9-211cd66e97fc`)
  is created with labels `app=driftline`, `environment=production`, and
  `owner=driftline`.
- The dashboard contains the liveness scorecard, Cloud Run request rate,
  Cloud Run container instance count, and Cloud Tasks dispatch-attempt rate.
  It is aggregate telemetry only and contains no prompts, source bodies,
  credentials, or customer outcomes.
- Configuration is reproducible from
  `infra/monitoring/driftline-production-dashboard.json`. Monitoring API
  header queries returned active series for all four metric families in the
  current window (`run.googleapis.com/request_count`,
  `run.googleapis.com/container/instance_count`,
  `cloudtasks.googleapis.com/queue/task_attempt_count`, and the uptime check).

## 2026-08-21 public end-to-end journey (live)

- Browser-driven production run `job-5f77824896c1` created workflow
  `794877e3-3794-464d-812b-2c3938c3da79` from the public console. The job
  completed through `execution_mode=google_adk` with model
  `gemini-3.5-flash`, source verification, four mapped artifacts, and the
  deterministic human-approval gate.
- The approval call recorded the decision and persisted a reversible,
  evidence-hash-bound packet plus its Google Cloud Storage operational output.
  The action record reported `external_systems_changed=false` and all
  external connector lanes remained `prepared_only`, as required for the
  anonymous public lane.
- The same run then exercised the undo path. The append-only event log recorded
  `decision_reopened`; the action record became `status=reversed` with a
  durable reversal marker and no external write. This proves scan → evidence →
  approval → persisted output → undo in the deployed product, not merely in a
  local fixture.
- Browser error/warning logs were empty and Cloud Logging showed no severity
  `ERROR` entries for the run window.

## 2026-08-21 owner follow-through canary (live)

- The same deployed workflow was approved again and its first owner action,
  `Pricing battlecard` for Product Marketing, was claimed and completed from
  the public console.
- The durable job record now reports `status=complete`; Firestore-backed
  closure state reports four action items, one completed, zero failed, zero
  reversed, and `completion_rate=0.25`, with the next step to assign and close
  the remaining owner actions. The append-only audit contains both the claim
  and completion events.
- Browser error/warning logs remained empty and Cloud Logging showed no
  severity `ERROR` entries after the closure canary. This is an observed
  operational metric for the isolated deployment, not a customer ROI claim.

- The canary was completed end to end: all four owner actions (Product
  Marketing, Customer Success, Support, and RevOps) were claimed and
  completed exactly once. The durable closure record reached `state=closed`,
  `completed=4`, `failed=0`, `overdue=0`, and `completion_rate=1.0`, with the
  next step `Review the completed evidence trail`.

## 2026-08-21 fontless console performance release (live)

- Source commit `02b2e41` passed the full 240-test suite, Ruff,
  `git diff --check`, and the frontend production build. Cloud Build
  `85e9ff6e-29ab-4302-a3f4-c76bd2d99442` completed `SUCCESS`; Cloud Run
  revision `driftline-00085-wbl` serves 100% of traffic.
- Removed the render-blocking Google Fonts stylesheet. The console keeps its
  existing DM Sans → Inter → system fallback stack without relying on a third-
  party font request, and the CSP now allows only the required Google Identity
  stylesheet path with `font-src 'self'`.
- Fresh Lighthouse evidence: performance `0.81`, accessibility `1.0`, best
  practices `1.0`, SEO `1.0`, agentic browsing `1.0`, FCP `3.1s`, LCP `4.1s`,
  zero render-blocking savings, zero console errors, zero inspector issues,
  and 755 KiB total transfer. Live `/health` and Cloud Logging probes remain
  clean.

## 2026-08-21 multimodal delivery and cache release (live)

- Source commit `2b35881` passed the full 240-test suite, Ruff,
  `git diff --check`, and the frontend production build. Cloud Build
  `09f36c8f-43e4-469f-a170-01a317090b6c` completed `SUCCESS`; Cloud Run
  revision `driftline-00084-7bh` serves 100% of traffic.
- The live visual registry is pinned to commit `d51a3c8` and now serves
  768x512 JPEG evidence bytes (about 68–70 KiB each) instead of the previous
  1536px PNG-derived payloads. `/api/multimodal/evidence/promise-card` returns
  `public_source`, `image/jpeg`, the pinned source URLs, and fresh SHA-256
  hashes.
- Fingerprinted Vite JavaScript/CSS assets now return
  `Cache-Control: public, max-age=31536000, immutable`. A fresh Lighthouse
  run measured 792 KiB total transfer, 100% accessibility, best practices,
  SEO, and agentic browsing scores, no console errors, and no inspector issues.
- The Google Identity stylesheet policy now includes the exact `/gsi/` path
  and an explicit `style-src-elem` directive; the live response contains both.

## 2026-08-21 recoverable console release (live)

- Source commit `e456290` passed 239 backend tests, Ruff, `git diff --check`,
  and the frontend production build. Cloud Build
  `27dfc586-47a3-40d5-93f3-cb00c715df29` completed `SUCCESS`; Cloud Run revision
  `driftline-00080-j9m` serves 100% of traffic with the existing max-one,
  scale-to-zero guardrails.
- The frontend now has a bounded React error boundary. A render-time failure
  presents a recovery card with a reload action and does not erase persisted
  workflow state or transmit exception details to a third party.
- Post-deploy probes returned `/health` HTTP 200, Firestore persistence,
  `gemini-3.5-flash` ADK execution through the public Run scan, deterministic
  `needs_approval`, zero browser warning/error logs, and zero severity `ERROR`
  Cloud Logging entries for the active revision.

## 2026-08-21 Google Identity CSP hardening release (live)

- Source commit `8e2d617` passed 239 backend tests, Ruff, `git diff --check`,
  and the frontend production build. Cloud Build
  `21827537-3377-438d-869e-428ef3e1939b` completed `SUCCESS`; the image digest
  is `sha256:d29afc2896c442c31638a7a0bc0e4df8a47d5383e61858735b7b6b5a3523b261`;
  Cloud Run revision `driftline-00079-k8c` serves 100% of traffic.
- The production CSP now explicitly permits the Google Identity Services
  stylesheet origin used by the operator sign-in control. This removes a
  browser-level stylesheet violation while keeping scripts, frames, and
  connections restricted to the required Google origin.
- The deployed auth client is still pending replacement with a new OAuth client
  created inside this isolated project; the current `32555940559...` value is
  retained only until that action is completed and live sign-in is reverified.
- A fresh logged-out browser journey on this revision completed **Run scan**;
  the durable job reached `needs_approval`, the UI rendered the live
  `gemini-3.5-flash` ADK trace with `inspect_source_change` and
  `get_workflow_state`, and the browser captured no warning or error logs.
- The same browser probe at a 390x844 mobile viewport measured
  `innerWidth=390`, `documentElement.scrollWidth=390`, and `body.scrollWidth=390`,
  confirming no horizontal overflow on the production console; the temporary
  viewport override was reset afterward.

## 2026-08-21 scheduler deduplication release (live)

- Source commit `bc811b0` passed 239 backend tests, Ruff, `git diff --check`,
  and the frontend production build. Cloud Build
  `cd102932-84da-4243-8625-9fe345570c95` completed `SUCCESS`; Cloud Run
  revision `driftline-00078-2wq` serves 100% of traffic.
- The six-hour monitor is now safe against at-least-once scheduler delivery:
  before enqueueing, it checks the in-memory and durable job ledgers for a
  queued/running monitor with the same tenant and source. Duplicate sources
  are returned in `in_flight_source_ids` as an explicit no-op, and a ledger
  lookup failure fails closed rather than fanning out unbounded model work.
- Live probes returned `/health` HTTP 200 with Firestore persistence and async
  jobs enabled, Google OIDC configuration with no credential values exposed,
  registry summary `5 healthy / 0 needs_baseline / 0 source_failed`, three
  append-only public pricing observations, the durable memory summary, the
  public scan queue shape, 100% traffic, maxScale `1`, concurrency `20`, and
  no severity `ERROR` logs for the active revision.

## 2026-08-21 idempotent tenant retry release (live)

- Source commit `ffa331f` passed 238 backend tests, Ruff, `git diff --check`,
  and the frontend production build. Cloud Build
  `5d20546a-38ce-4281-a52f-0945f2629c0f` completed `SUCCESS`; Cloud Run
  revision `driftline-00077-xts` serves 100% of traffic.
- Signed tenant Run history now exposes a terminal-failure retry action. The
  API rechecks tenant membership and the source allowlist, preserves the
  failed job's query/source/run mode, and writes a durable `retry_of` link.
  Concurrent retry requests return the existing successor instead of creating
  duplicate agent work. Anonymous jobs remain packet-safe: a live public probe
  received HTTP 403 with `Public jobs can be rerun from the public scan
  control`.
- Post-deploy probes used the isolated project and returned `/health` HTTP 200
  with Firestore persistence and async jobs enabled, Google OIDC configuration
  with no credential values exposed, the public console title, 100% traffic,
  maxScale `1`, concurrency `20`, and no severity `ERROR` logs for the active
  revision.

## 2026-08-21 tenant pilot measurement release (live)

- Source commit `3d3d2d7` passed 237 backend tests, Ruff, `git diff --check`,
  and the frontend production build. Cloud Build
  `557f98b9-dfb0-4586-abca-4a44ac9b6877` completed `SUCCESS`; Cloud Run
  revision `driftline-00076-7qw` serves 100% of traffic.
- Authenticated tenant operators now have a Pilot measurement panel backed by
  the existing signed `/api/ops/outcomes` and `/api/ops/pilot-report` routes.
  It records only aggregate before/after minutes and optional outcome fields,
  requires an evidence reference, and labels every result
  `operator_reported_unverified`. The anonymous route remains protected: a
  logged-out `/api/ops/pilot-report` probe returned HTTP 401.
- Post-deploy probes returned `/health` HTTP 200, Google OIDC auth config, the
  public console title, 100% traffic, scale-to-zero/max-one guardrails, and
  zero severity `ERROR` entries for the active revision.

## 2026-08-21 source onboarding parser and selection release (live)

- Source commit `810e35f` passed 237 backend tests, Ruff, `git diff --check`,
  and the frontend production build. Cloud Build
  `40fca7a7-d934-448a-82f7-5a811cc2710c` completed `SUCCESS`; Cloud Run
  revision `driftline-00075-xt7` serves 100% of traffic.
- The authenticated onboarding form now supports the bounded HTML, plain-text,
  and RSS/Atom parser contracts already enforced by the backend. It selects a
  newly registered source for the next scan, and registered competitor sources
  are no longer mislabeled as synthetic in the source selector.
- Post-deploy probes returned `/health` HTTP 200, Google OIDC auth config, the
  public console title, 100% traffic, scale-to-zero/max-one guardrails, and
  zero severity `ERROR` entries for the active revision.

## 2026-08-21 direct registered-source agent lane (live)

- Source commit `efa8ac3` passed 237 backend tests, Ruff, `git diff --check`,
  and the frontend production build. Cloud Build
  `26af7a0f-da62-4aef-a36b-c3a257dcef2c` completed `SUCCESS`; Cloud Run
  revision `driftline-00074-vl4` serves 100% of traffic.
- The signed `POST /api/agent/run` path now resolves an operator-registered
  source only after authenticating the tenant, then carries that exact source
  through the live ADK run. Anonymous callers still cannot discover or execute
  tenant sources. This aligns the direct API, console, and scheduler paths.
- Post-deploy probes returned `/health` HTTP 200, Google OIDC auth config,
  100% traffic on the new revision, scale-to-zero/max-one guardrails, and zero
  severity `ERROR` Cloud Logging entries for the active revision.

## 2026-08-21 registered-source evidence labeling release (live)

- Source commit `9a3f144` passed GitHub Actions `32456185723`, 236 backend
  tests, Ruff, `git diff --check`, and the frontend production build. Cloud
  Build `f40e7210-69e8-4611-a212-9032e3ac62e6` completed `SUCCESS`; Cloud Run
  revision `driftline-00073-qjm` serves 100% of traffic.
- Registered-source runs now display `Operator-registered public source` and
  `Authenticated source monitor` in the console. The UI no longer labels a
  successfully captured public tenant source as synthetic or “Awaiting
  capture,” preserving the distinction between pinned fixtures, registered
  public evidence, and synthetic replay.
- Post-deploy probes returned `/health` HTTP 200, Google OIDC auth config,
  public console title, 100% traffic, `maxScale=1`, concurrency `20`, and zero
  severity `ERROR` entries for the active revision.

## 2026-08-21 registered-source console monitor lane (live)

- Source commit `772139b` passed GitHub Actions `32455807729`, 236 backend
  tests, Ruff, `git diff --check`, and the frontend production build. Cloud
  Build `c1a93c09-1bc0-43d5-bcc7-d18870318d6b` completed `SUCCESS`; Cloud Run
  revision `driftline-00072-lg8` serves 100% of traffic.
- The authenticated console now detects a tenant's operator-registered
  `public_only` source and queues `run_mode=monitor` when **Run scan** is
  pressed. Pinned fixtures continue to use the bounded `tenant_demo` lane.
  This closes the product loop from source onboarding to a real public fetch,
  append-only baseline/history, ADK analysis, and deterministic approval; it
  no longer presents a registered URL in the UI that the backend would reject
  as a synthetic-only run.
- Post-deploy probes returned `/health` HTTP 200, the Google OIDC auth config,
  the public console title, 100% traffic on the new revision, scale-to-zero
  `maxScale=1`, and zero `severity>=ERROR` Cloud Logging entries for the
  revision. No external connector write was performed by this UI regression
  check.

## 2026-08-21 visual evidence reliability release (live)

- Source commit `453c2c6` passed GitHub Actions `32442923011`; the frontend
  production build passed and Cloud Build
  `b0f238a7-37e9-4626-a6e4-e859c41f4dfe` completed `SUCCESS`. Cloud Run revision
  `driftline-00052-f75` serves 100% of traffic.
- The before/after multimodal cards now load eagerly instead of waiting for
  scroll intersection. A fresh headless Chrome probe measured both public
  visual assets at `1536x1024`, `complete=true`, with no console or page errors.
  The same probe measured `documentWidth=390` at a 390px mobile viewport.

## 2026-08-21 production source onboarding release (live)

- Source commit `0ec10af` passed GitHub Actions `32442367441` and the local
  gate (224 backend tests, Ruff, and the frontend production build). Cloud
  Build `64840a9b-3836-4899-81b0-96474e14ea14` completed `SUCCESS`; Cloud Run
  revision `driftline-00051-rll` serves 100% of traffic.
- Signed exact-URL source onboarding now performs one bounded public read in
  production source mode and returns an explicit `baseline_established` or
  `source_fetch_failed` result. It remains metadata-only in local/synthetic
  mode, and the scheduler continues retrying failed sources.
- Post-deploy proof: `/health` returned HTTP 200; an anonymous public scan on
  job `job-9dd517681c11` reached `needs_approval` with workflow
  `b736c7fc-3408-47e4-af30-6bd8ba9dba38`, `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, `data_mode=public_source`, and exactly two
  allowlisted tool calls. An unsigned tenant-demo request returned HTTP 401.
- Cloud Logging returned no severity `ERROR` entries for
  `driftline-00051-rll`.

## 2026-08-21 console lifecycle truthfulness release (live)

- Source commit `8eeae4a` passed GitHub Actions `32441821450` and the local
  gate (223 backend tests, Ruff, and the frontend production build). Cloud Build
  `930e8940-35e6-442d-959b-986565b8451e` completed `SUCCESS`; Cloud Run revision
  `driftline-00050-42p` serves 100% of traffic.
- The console now renders connector outcomes as `Created`, `Reused`,
  `Reactivated`, `Reversed`, or `Blocked · closed target`, matching provider
  responses instead of implying every approved handoff was newly created.
- Post-deploy probes returned `/health` HTTP 200 and the public console; an
  unsigned `tenant_demo` start returned HTTP 401 as intended. Cloud Logging
  returned no severity `ERROR` entries for `driftline-00050-42p`.

## 2026-08-21 closed-target safety boundary (live)

- Source commit `c61823c` passed GitHub Actions `32441421717` and the full local
  gate (223 backend tests, Ruff, and the frontend production build). Cloud
  Build `76212a86-49a1-40a7-ae05-71ac321b7bf2` completed `SUCCESS`; Cloud Run
  revision `driftline-00049-dq7` serves 100% of traffic.
- The GitHub adapter now fails closed with `blocked_closed` when a marker points
  at a human-closed issue. It performs no relabel, reopen, or delete operation;
  the operator must explicitly reopen the issue or choose a new target. This
  prevents a closed task from being represented as active.
- The current revision returns `/health` HTTP 200 with Firestore and async jobs.
  Earlier live provider reads remain valid for the all-connector active/reversed
  lifecycle proof on revision `driftline-00048-j8g`; this release adds the
  closed-target safety boundary without changing public demo behavior.

## 2026-08-21 all-connector reactivation and reversal proof (live)

- Source commit `76c2a39` passed GitHub Actions `32440926605` and the full local
  gate (222 backend tests, Ruff, and the frontend production build). Cloud
  Build `c2857f9d-b9c7-4c6a-8033-af5e8274abad` completed `SUCCESS`; Cloud Run
  revision `driftline-00048-j8g` serves 100% of traffic.
- On workflow `858ab326-d2fe-45f0-af89-42da12ef60b2`, signed approval on the
  current revision returned `reactivated` and `idempotent=true` for Jira,
  Confluence, Slack, and GitHub. The action was tenant-bound to
  `driftline-demo` and remained reversible.
- Direct provider reads confirmed the approved state: Jira `KAN-18` had
  `driftline-active` plus `driftline-approval-gated`; Confluence page `1605654`
  contained versioned reactivation and reversal markers; Slack contained the
  corresponding reactivation message in `C0BRGFUSADA`; GitHub issue `#11` had
  `driftline-active` and `driftline-approval-gated` with no reversed label.
- Signed undo returned all four connector statuses to `reversed`. Direct reads
  then confirmed Jira/GitHub had only `driftline-reversed`, Confluence retained
  both append-only audit markers, and Slack retained the reversal messages.
  GitHub's unrelated labels are preserved by the atomic label replacement.
- This is an isolated authenticated fixture canary, not customer data or ROI;
  the public judge lane remains packet-only and Salesforce remains
  `not_configured`.

## 2026-08-21 connector reactivation hardening (live)

- Source commit `1c5ec8f` passed GitHub Actions `32440101155` and the full local
  gate (221 backend tests, Ruff, and the frontend production build). Cloud
  Build `af23c2ee-0693-4e09-a454-3df0f8b072a4` completed `SUCCESS`; Cloud Run
  revision `driftline-00046-hjc` serves 100% of traffic.
- The release hardens every external handoff adapter: Jira and GitHub restore
  Driftline-owned active labels after a prior reversal, Slack emits an explicit
  reactivation audit message, and Confluence removes its reversal label or
  appends a versioned reactivation marker without overwriting history.
- Current live checks returned `/health` HTTP 200 with Firestore and async jobs,
  anonymous exposure scans clear for `/api/ops/summary`, `/api/ops/value-proof`,
  `/api/jobs`, and `/api/sources`, and signed binding health with four healthy,
  namespace-verified connectors (Salesforce remains not configured). Cloud
  Logging returned no severity `ERROR` entries for `driftline-00046-hjc`.

## 2026-08-21 signed tenant pilot and reversible Jira proof (live)

- Source commit `282fcde` passed the full local gate (218 backend tests, Ruff,
  and the frontend production build). Cloud Build
  `2c112a6b-32bc-4314-814a-ba5084755fb6` completed `SUCCESS`; Cloud Run
  revision `driftline-00045-hvw` serves 100% of traffic in the isolated
  `driftline-hackathon-2026` project.
- The new signed `run_mode=tenant_demo` lane ran job `job-5828e40c0c86` and
  workflow `116dd7ce-690a-436a-9c31-ca98a41d757c` through real
  `google_adk`/`gemini-3.5-flash`, with exactly
  `inspect_source_change` and `get_workflow_state`. Firestore state was
  tenant-bound to `driftline-demo`, marked `synthetic_tenant_demo`, and held at
  `needs_approval` until a named human selected the Gemini copilot option.
- The signed approval created a real, project-scoped Jira Task handoff in the
  isolated `KAN` project. The idempotent marker found the prior reversed issue
  `KAN-18` and reactivated only Driftline-owned labels (`jira_status=reactivated`,
  `external_systems_changed=true`). A direct Jira API read confirmed labels
  `driftline-active` and `driftline-approval-gated`.
- Signed undo completed on the same workflow and changed only the Jira-owned
  labels to `driftline-reversed`; a direct Jira API read confirmed the reversed
  state. The original issue was retained and no delete operation was used.
- This is a bounded authenticated fixture pilot and connector proof, not a
  customer outcome or live competitor-monitoring claim. Salesforce remains
  `not_configured`; the anonymous public judge lane remains packet-only.
- Cloud Logging for `driftline-00045-hvw` returned no severity `ERROR` entries
  after the live proof.

## 2026-08-21 production-control-plane copy rollout (live)

- Source commit `bb8a437` passed GitHub Actions `32435761464` and Cloud Build
  `db3305b1-7770-4cec-a7f3-e468eb4210f5` completed `SUCCESS`.
- Cloud Run revision `driftline-00037-6t9` serves 100% of traffic with the same
  scale-to-zero and one-instance guardrails. The public console now names this
  the production control plane and labels the anonymous lane as packet-only
  public-demo safety mode; it does not imply customer data or external writes.
- A fresh anonymous `/api/agent/run` canary on the preceding rollout returned
  `persisted=true`, `execution_mode=google_adk`, `model=gemini-3.5-flash`, and
  `data_mode=public_source`. No external connector write was performed.

## 2026-08-21 responsive production-control-plane rollout (live)

- Source commit `9431006` passed GitHub Actions `32437783883` and Cloud Build
  `351447cf-e436-41c6-ace9-0fdab19d639e` completed `SUCCESS`.
- Cloud Run revision `driftline-00043-xkb` serves 100% of traffic with the
  existing scale-to-zero and one-instance guardrails. The release contains the
  live operational pulse and contains the intentional activity, history, and
  worklist scrollers so they cannot expand the document viewport on mobile.
- A public 390px emulation probe reported `bodyScrollWidth=500`,
  `documentElement.scrollWidth=500`, and `scrollX=0` while the nested scrollers
  remained independently scrollable (`920`, `871`, and `780`px content widths).
  Desktop and mobile Lighthouse navigation audits each passed 57/57 checks with
  100 scores for accessibility, best practices, SEO, and agentic browsing; the
  browser console had no messages.

## 2026-08-21 packet-language rollout (live)

- Source commit `1c71473` passed GitHub Actions `32436210206` and Cloud Build
  `bfc15321-f8f2-40d8-bf02-e3ba96ab5d7b` completed `SUCCESS`.
- Cloud Run revision `driftline-00038-2gq` serves 100% of traffic. A fresh public
  ADK/Gemini run persisted a workflow, approval persisted the private packet,
  and the packet now says `isolated public-demo output`; the same workflow was
  undone with `external_write=false` and `external_systems_changed=false`.

## Current state snapshot (authoritative)

Checked after the latest live verification on 2026-08-21 UTC. The release
entries below are append-only history; they are not a substitute for this
snapshot.

- Public URL: `https://driftline-xvxczqg62a-uc.a.run.app/`
- Active Cloud Run revision: `driftline-00097-rdn` at 100% traffic, scale to
  zero, one-instance cap.
- Cloud Run limits: 1 vCPU, 512 MiB, concurrency 20, max scale 1, no minimum
  scale. Billing budget `Driftline $10 Guardrail` is filtered to this project
  with 10%, 25%, 50%, 75%, 90%, and 100% current-spend thresholds; default
  billing-account recipients remain enabled and no custom notification channel
  is configured.
- Deployed runtime source: `c8966fa`; Cloud Build
  `8d62f466-d179-4a54-bfb9-0d90fbfa7c4c`.
- The public console now presents the live service as a production control
  plane with an explicit public-demo safety mode; anonymous judging remains
  packet-only and cannot write to customer systems.
- `/health`: HTTP 200, Firestore persistence enabled, async jobs enabled.
- A fresh anonymous `POST /api/agent/run` on workflow
  `17549d67-ebb6-4f9a-a0e5-e5b5a126fa3c` returned HTTP 200 with
  `persisted=true`, `execution_mode=google_adk`, `model=gemini-3.5-flash`,
  and `data_mode=public_source`; the workflow was re-read from Firestore in
  `needs_approval` state. No connector write was requested.
- Current public registry: five pinned judge fixtures only. No arbitrary
  competitor source is registered.
- Signed connector health: Jira, Confluence, Slack, and GitHub healthy;
  Salesforce `not_configured`; credential values redacted.
- Anonymous exposure recheck: `/api/ops/summary`, `/api/ops/value-proof`,
  `/api/jobs`, and `/api/sources` returned no token/secret fields; connector,
  tenant-policy, and failure-ledger routes remained signed-only.
- Signed pilot report remains `status=not_measured`, `record_count=0`; the
  authenticated fixture/Jira proof above is an operational canary, not a
  customer outcome measurement.
- Public-demo value proof: 45 workflows, 41 source observations, 24
  human-owned action items, 1 completed action (4.2%), 0 external writes.
- Final video upload and Devpost submission: not completed.

## 2026-08-20 reproducible isolated deploy identity (live)

- Source commit `97a3ed8` pins `cloudbuild.yaml` to the dedicated
  `driftline-build@driftline-hackathon-2026.iam.gserviceaccount.com`; the
  checked-in deployment now does not depend on a CLI-only identity override.
- A deployment submitted without `--service-account` succeeded: Cloud Build
  `1cc53c92-d106-46a1-9d51-0d17dac60a9f` completed `SUCCESS`, producing Cloud
  Run revision `driftline-00031-n7l` at 100% traffic. The active gcloud project
  was `driftline-hackathon-2026`.
- `/health` returned 200 after rollout. A fresh canary on `driftline-00031-n7l`
  persisted a Firestore workflow with `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, `source_status=needs_approval`, and exactly
  `inspect_source_change` plus `get_workflow_state`; Cloud Logging returned no
  severity `ERROR` entries for the revision. The query-auth guard and signed
  connector reconciliation remain active as recorded below.
- A Chrome performance trace on the current public app recorded LCP 164 ms,
  CLS 0.00, and no material render-blocking savings opportunity at desktop
  navigation conditions. This is lab evidence, not field-user CrUX data.

## 2026-08-20 final UI copy and live quality gate (live)

- Source commit `6117327` removes a misleading hard-coded “four work items”
  claim from the owner action queue; the copy now reflects the durable item
  count returned by the workflow.
- Cloud Build `0e4f1d76-244f-4385-b736-7f9c54c98631` completed `SUCCESS` and
  Cloud Run revision `driftline-00030-kkb` serves 100% of traffic. GitHub
  Actions run `32428607406` passed backend tests, Ruff, frontend production
  build, and standalone image build.
- Current public browser checks found no console messages. Lighthouse passed
  all 57 audits on desktop and mobile: accessibility 100, best practices 100,
  SEO 100, and agentic browsing 100. `/health` remains HTTP 200 with
  Firestore persistence and async jobs enabled.

## 2026-08-20 Salesforce read-only scope release (live)

- Source commit `bb0dd66` narrows the Salesforce OAuth callback binding to the
  concrete `read_context` operation. It no longer inherits the legacy
  compatibility `runtime` scope; Salesforce has no write path.
- Cloud Build `4348b061-8b1c-4d6f-8262-6c40ed5355fb` completed `SUCCESS` and
  Cloud Run revision `driftline-00029-zdn` serves 100% of traffic. The active
  project was verified as `driftline-hackathon-2026` before submission.
- Current live canary: `/health` 200; anonymous `/api/agent/run` persisted a
  Firestore workflow with `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, `source_status=needs_approval`, and only
  `inspect_source_change` plus `get_workflow_state` tool calls. Hosted query
  authentication returned 400 for a URL token, and Cloud Logging returned no
  severity `ERROR` entries for the revision.
- Signed connector reconciliation remains `4 healthy`, `0 attention`, and `1
  not_configured` (Salesforce). Jira, Confluence, Slack, and GitHub continue
  to report verified tenant namespaces and aggregate-only read readiness with
  no credential values exposed. Salesforce still requires the owner login and
  consent callback before any CRM read can be claimed.

## 2026-08-20 fail-closed connector scope release (live)

- Source commit `9ccde30` adds a fail-closed resolver default: a legacy or
  malformed connector binding with no `allowed_operations` field can lease
  `read_context` only and cannot silently authorize an external write. The
  focused broker tests report `10 passed`; the full backend suite reports
  `214 passed`; Ruff and the frontend production build are clean. GitHub
  Actions run `32426734472` completed `success`.
- Cloud Build `97a7231d-0718-4045-822e-5f49c423ee4e` completed `SUCCESS` with
  the isolated `driftline-build` identity. Cloud Run revision
  `driftline-00028-2nx` serves 100% of traffic with the existing scale-to-zero,
  one-instance cap, and 512 MiB runtime settings. Bucket object-read and
  Artifact Registry write permissions were granted only to the isolated
  build identities required by this deployment.
- Live `/health` returned 200 with Firestore persistence and async jobs. The
  hosted query-auth guard returned 400 for a URL `approval_token`. A fresh
  anonymous `/api/agent/run` returned `persisted=true`, `execution_mode=
  google_adk`, `model=gemini-3.5-flash`, `source_status=needs_approval`, and
  exactly `inspect_source_change` plus `get_workflow_state`.
- A signed live binding-health probe returned `4` healthy configured
  connectors and `1` not configured connector: Jira, Confluence, Slack, and
  GitHub were readable within their fixed scopes with no credential values
  exposed; Salesforce remains `not_configured` pending the owner-completed
  OAuth consent callback. A signed aggregate context probe again returned
  only bounded counts and scope metadata, with `persisted=false`.
- Cloud Logging returned no severity `ERROR` entries for revision
  `driftline-00028-2nx` after rollout. This is deployment evidence, not a
  customer-outcome or pilot result.
- Chrome DevTools on the current public revision found no console messages.
  Lighthouse navigation passed all 57 audits on both desktop and mobile:
  accessibility 100, best practices 100, SEO 100, and agentic browsing 100.

## 2026-08-20 tenant and source security hardening (live)

- New connector enrollments default to the concrete `read_context` scope only.
  Connector adapters now request `create_*` or `reverse_*` scopes explicitly
  for downstream writes, so a read-only enrollment cannot later lease a write
  credential. The regression suite covers the rejected write attempt.
- Operator-registered source URLs are fetched through one validated public DNS
  answer, pinned at the socket connection, with TLS hostname verification and
  redirects disabled. This closes the DNS-rebinding/TOCTOU SSRF path while
  retaining exact HTTPS URL allowlisting.
- Memory-mode custom source definitions and histories are tenant-scoped just
  like Firestore mode; anonymous `/api/sources`, history, and memory responses
  expose only the five static demo fixtures.
- Hosted images set `DRIFTLINE_REJECT_QUERY_AUTH=true`. GET requests carrying
  `approval_token` or `identity_token` in the URL are rejected; signed operator
  clients use `X-Driftline-Approval` and `Authorization` headers. Local tests
  retain query compatibility unless that flag is enabled.
- Cloud Build `2ac70c0e-d281-4dea-9f48-4a48c33bdf59` completed `SUCCESS` from
  runtime commit `cba22ea`; Cloud Run revision `driftline-00027-vvn` serves 100% of
  traffic in the isolated project. `/health` returned 200 and a GET carrying
  `approval_token` returned 400, while the public API retained `no-store` and
  HSTS headers.
- GitHub Actions run `32425880837` completed `success` for the preceding
  runtime/docs release. Cloud Logging returned no severity `ERROR` entries for
  revision `driftline-00027-vvn` after rollout.
- Chrome DevTools loaded the public console at desktop and mobile widths with
  no console messages. Lighthouse navigation scored 100 for accessibility,
  best practices, SEO, and agentic browsing on both devices (57/57 audits).
- A fresh anonymous `/api/agent/run` completed with `persisted=true`,
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and exactly the
  allowlisted tool calls `inspect_source_change` and `get_workflow_state`.
  The returned workflow was re-read from the public API in `needs_approval`
  state, then a named demo approval and undo were exercised successfully;
  no external write occurred.
- The post-hardening canary on revision `driftline-00027-vvn` again returned
  `persisted=true`, `google_adk`, `gemini-3.5-flash`, and exactly
  `inspect_source_change` plus `get_workflow_state`; `/health` returned 200
  and the query-auth rejection remained active.
- A signed live connector context probe completed aggregate-only reads for
  Jira (`project:KAN`, 18 open issues), Confluence (`space:DRIFT`, 5 pages),
  Slack (`channel:C0BRGFUSADA`, 27 recent messages), and GitHub
  (`mikeyerke/driftline`, 0 open issues, 3 open pull requests). Salesforce is
  intentionally not called live: its status remains `oauth_ready` /
  `awaiting_authorization` until the Salesforce browser consent callback is
  completed by the account owner.

## 2026-08-20 API cache-policy enforcement (live)

- Source commit `481c8c7` changed the API security middleware from a default
  header to an unconditional `Cache-Control: no-store` assignment. This keeps
  an endpoint-defined cache header from weakening the privacy contract for
  tenant metadata or one-time OAuth responses. A focused regression test
  supplies a conflicting `public, max-age=3600` header and verifies it is
  replaced; the full local suite reports `208 passed` with Ruff clean.
- GitHub Actions run `32422051597` completed `success`. Cloud Build
  `658bcb18-dd42-4a16-8068-a78d491d4d5e` completed `SUCCESS`; Cloud Run
  revision `driftline-00023-w7h` serves 100% of traffic in the isolated
  project with the existing scale-to-zero and one-instance cap.
- Live `/health` returned `200` with Firestore persistence and async jobs.
  The public `/api/ops/value-proof` response returned `200` with
  `cache-control: no-store`; the current direct value proof reported 50
  isolated workflows, 50 change cards, five healthy sources, zero external
  writes, and explicitly labelled all customer-outcome fields
  `not_measured`.
- A direct public agent canary on this revision returned
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, exactly the
  allowlisted tools `inspect_source_change` and `get_workflow_state`,
  `source_status=needs_approval`, and redacted anonymous query/user fields
  (`null`). Cloud Logging showed no severity `ERROR` entries for the new
  revision after rollout.

## 2026-08-20 Standalone image reproducibility (repository/CI)

- Source commit `70d4540` aligned the checked-in `backend/Dockerfile` with
  the production image: it copies `backend/uv.lock`, runs the frozen
  `uv==0.8.17` resolution, and drops to the dedicated non-root `driftline`
  user. This alternate backend image is not deployed separately; the root
  Dockerfile remains the Cloud Run artifact.
- GitHub Actions run `32422871806` completed `success` across backend tests,
  frontend production build, and the new standalone backend image build.
- No Cloud Run mutation was needed for this repository-only reproducibility
  improvement; revision `driftline-00023-w7h` remains the verified live
  deployment.

## 2026-08-20 Frontend dependency reproducibility (repository/CI)

- Source commit `a09f1a5` replaced direct frontend `latest` declarations with
  the exact versions already present in the lockfile (`react`/`react-dom`
  19.2.8, `vite` 8.2.1, `@vitejs/plugin-react` 6.0.5, and `lucide-react`
  1.32.0). This prevents a fresh manifest install from silently selecting a
  different build toolchain.
- Local `npm ci --ignore-scripts`, production build, and high-severity audit
  all passed with zero reported vulnerabilities. GitHub Actions run
  `32423063200` completed `success` across all three verification jobs.
- This is repository-only; the already verified Cloud Run revision
  `driftline-00023-w7h` remains unchanged.

Before any future mutation, verify the target explicitly:

```bash
gcloud config set project driftline-hackathon-2026
test "$(gcloud config get-value project 2>/dev/null)" = driftline-hackathon-2026
```

## 2026-08-20 Reopened-workflow value-proof correction (live)

- Source commit `2294467` corrected the value-proof aggregation to read the
  workflow event's `outcome` field. Reopened decisions were being persisted as
  `decision_reopened` but were omitted from `workflows_reversed_or_reopened`.
  A regression test now covers the approve → undo path and the full local suite
  reports `206 passed` with Ruff clean; the frontend production build also
  passes.
- Cloud Build `ea3c00d5-b041-4961-87d1-a89533a34b0e` completed `SUCCESS` and
  produced image digest
  `sha256:7890e3b7d0a5e4f4fd30cf75a9148ada0d8b5949c908d828c9b6676f7fecf758`.
  Cloud Run revision `driftline-00021-rlt` serves 100% of traffic in
  `driftline-hackathon-2026` with scale-to-zero and the existing one-instance
  cap. GitHub Actions run `32419555900` for this commit completed `success`.
- Live `/health` returned `200` with Firestore persistence and async jobs. The
  public value-proof endpoint now reports `workflows_reversed_or_reopened=13`
  and `action_items_completed=0` after the synthetic reversal exercise; these
  are isolated deployment records, not customer outcomes. A direct public
  agent canary returned `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, exactly the allowlisted tools
  `inspect_source_change` and `get_workflow_state`, and redacted anonymous
  query/user fields (`null`).
- A signed live aggregate-context probe on the same revision returned HTTP 200
  for Jira (`project:KAN`, 18 sampled open issues), Confluence (`space:DRIFT`,
  5 pages), Slack (`channel:C0BRGFUSADA`, 27 recent messages), and GitHub
  (`mikeyerke/driftline`, 0 open issues, 3 open pull requests). The response
  explicitly reported `persisted=false` and `aggregate_metadata_only`; no
  source bodies or message text were returned. Salesforce remains
  `oauth_ready` pending the operator's Salesforce login/consent and a
  post-callback aggregate health probe.
- Cloud Logging returned no severity `ERROR` entries for revision
  `driftline-00021-rlt` after rollout.
- The deployed pilot gate was rechecked: unsigned `GET /api/ops/pilot-report`
  returned `401`, while the signed `driftline-demo` request returned
  `status=not_measured`, `record_count=0`, and null outcome lifts. This is the
  correct fail-closed state until a real participant supplies independently
  verifiable before/after records; synthetic workflow telemetry is not used as
  a customer-pilot substitute.
- The current revision's signed Salesforce start route returned
  `status=authorization_required` with a ten-minute state and
  `code_challenge_method=S256`; no client secret was exposed in the URL. The
  browser handoff remains at Salesforce login, so no OAuth callback or CRM
  record read is claimed.
- The always-on monitor is not a UI-only claim: Cloud Scheduler job
  `driftline-monitor` is `ENABLED` on `0 */6 * * *` UTC and targets the
  scheduler tick endpoint. Cloud Logging shows successful `POST
  /api/scheduler/tick` responses at 00:00, 06:00, 12:00, 18:00, and 19:54 UTC
  on the current operating window. The latest registry probe reported all five
  pinned sources `healthy`, `stale=0`, `source_failed=0`, and fresh public
  observations; the fixture boundary remains explicitly disclosed.

## 2026-08-20 API privacy-header hardening (live)

- Source commit `7f9d4eb` adds explicit `Cache-Control: no-store` to every
  `/api/` response and a restrictive `Permissions-Policy` for camera,
  microphone, geolocation, payment, and USB. This protects tenant metadata and
  one-time OAuth responses from intermediary/browser retention and reduces
  unnecessary browser capability exposure.
- Local regression is `207 passed` with Ruff and the frontend production build
  clean. GitHub Actions run `32420758822` completed `success`.
- Cloud Build `14e49de2-110e-43c3-b71d-65289492d3d4` completed `SUCCESS` with
  image digest
  `sha256:6518878b6c419de705bc087092fe9f55a03b6458979835dd5476e63e34bf9783`.
  Cloud Run revision `driftline-00022-zf4` serves 100% of traffic.
- Live `/health` returned 200. Public API headers included `cache-control:
  no-store` and the new Permissions-Policy. A direct anonymous agent canary
  still returned `execution_mode=google_adk`, `model=gemini-3.5-flash`, only
  `inspect_source_change` and `get_workflow_state`, and null query/user fields.
  The active revision has no severity `ERROR` logs.

## 2026-08-20 Infrastructure closeout recheck (live)

- Cloud Run remains labelled `app=driftline`, `environment=production`, and
  `hackathon=all-things-agentic`, with the dedicated
  `driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com`, one
  maximum instance, one vCPU, and 512 MiB.
- Cloud Tasks queue `driftline-jobs` is `RUNNING` with one concurrent dispatch,
  0.2 dispatches/second, three attempts, and bounded 5–60 second backoff.
- Firestore TTL fields are present for jobs, failures, workflows, snapshots,
  outcome measurements, Salesforce OAuth state, and credential-access events.
- The project-scoped budget remains `Driftline $10 Guardrail` on project
  number `724959673622`; no billing resource outside the isolated project was
  selected by the check.
- IAM recheck found the runtime service account's project roles limited to
  Vertex AI user, Cloud Tasks enqueuer, Firestore user, and Secret Manager
  version-adder; connector secret access is granted only on the exact
  tenant-specific secrets to the derived tenant data-plane identity. The
  build identity has only Cloud Build builder, Run admin, and Service Usage
  consumer roles. The public invoker is intentional for the identity-free
  judging surface; tenant reads/writes still require signed identity.

## 2026-08-20 Durable connector-read quota fix (live)

- Source commit `2aaca67` registers `connector_calls` in the shared usage and
  transactional rate-limit metric allowlist. The earlier quota release could
  reserve agent/workflow slots but rejected connector reservations as an
  invalid metric; this fix keeps the connector allowance fail-closed without
  blocking valid reads.
- Cloud Build `2b46a3fc-b630-42bc-92c1-472b60ead9c8` completed `SUCCESS` and
  produced image digest
  `sha256:4f068c46e5233b24c24b90dda32aa2269985157aa5b1db72db956c61d4cdb3db`.
  Cloud Run revision `driftline-00008-kw6` serves 100% of traffic in the
  isolated project with the existing scale-to-zero/max-one settings.
- `/health` returned `200` with Firestore persistence and async jobs. Signed
  live probes returned `200` for tenant policy, connector binding health, and
  aggregate connector context. The effective `driftline-demo` policy is
  `connector_calls_per_window=60` per 3600-second window. The binding health
  summary reported 4 healthy, 1 not configured (Salesforce), 0 attention, and
  `credential_values_exposed=false`; the signed usage ledger recorded
  `connector_calls=3` without credential values.
- Cloud Logging showed no severity `ERROR` entries after the 00008 rollout.
  A direct public `POST /api/agent/run` returned `200` with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`,
  `source_status=needs_approval`, `persisted=true`, and workflow
  `5aff9cca-3cce-494a-ae2b-b8946aabb478`; its Firestore workflow remained
  tenantless packet-safe state with five events and no credential terms.
  Browser QA on the deployed URL passed at desktop and 390px widths with no
  overflow, console errors, or failed requests; the complete journey reported
  4 rows, 2 selects, needs-approval, completed, and reopened states. Local
  regression remains `195 passed`; Ruff, frontend production build, and
  `git diff --check` are clean.

## 2026-08-20 Multimodal spend guardrail (live)

- Source change adds a process-wide cap of 10 allowlisted Gemini visual
  analyses per 3600-second window. Exhaustion returns HTTP `429` with a
  `Retry-After` header, and `/api/ops/summary` exposes the active bound without
  exposing request content or credentials.
- The route remains limited to the fixed repository visual pair and is kept
  separate from tenant connector quotas because the public visual lane is
  intentionally tenantless. Local regression covers the accepted call and
  retryable exhaustion behavior (`196 passed`). Cloud Build
  `4fa9ad07-333c-4996-a2b0-58f2ff38eb01` completed `SUCCESS` with image digest
  `sha256:2108138018ff5181d3adb8289f582af0f4fdc66c91422a06e64d366c189a3162`;
  Cloud Run revision `driftline-00009-mlb` serves 100% of traffic.
- `/health` returned 200 with Firestore persistence and async jobs. The live
  ops summary reports `multimodal_max_calls=10` and
  `multimodal_window_seconds=3600`. One live visual analysis returned 200 with
  `mode=gemini_vision`, `model=gemini-3.5-flash`, material change true,
  confidence `0.98`, and a 64-character evidence hash. Post-deploy logs have
  zero severity `ERROR` entries; desktop/mobile audit and the complete
  scan-to-reopen journey pass with no console errors or failed requests.

## 2026-08-20 Public demo ADK degradation guardrail (live)

- Source commit `3fe3093` keeps the identity-free synthetic judge lane
  reviewable when a real Gemini turn is temporarily quota-limited. The narrow
  fallback creates a labelled `synthetic_demo` workflow with
  `execution_mode=deterministic_demo_fallback`; signed tenant and monitor runs
  still fail closed and never receive synthetic state.
- Cloud Build `b52da696-f041-472b-8d8a-2d27baac31ac` completed `SUCCESS` with
  image digest
  `sha256:7d246e7c631149220f644ecaa1f364bf8dd04feef0911d87ade1f2d0bbd7f107`;
  Cloud Run revision `driftline-00011-mnz` serves 100% of traffic with
  `allUsers` invoker access, min zero, and max one instance.
- A live demo job returned `needs_approval` with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, workflow
  `ba84dd8c-e571-49a4-8693-733a9a0acc1a`, Firestore-backed `public_source`
  state, and a redacted ADK trace. The fallback path is covered by a focused
  regression test; no Gemini or business outcome claim is made when it is
  used. The deployed browser journey reported 4 artifact rows, 2 selects,
  needs-approval, completed, and reopened states with zero console errors or
  failed requests; post-rollout Cloud Logging has zero severity `ERROR` or
  `WARNING` entries for revision `driftline-00011-mnz`.

## 2026-08-20 Credential namespace isolation hardening (live)

- Source commit `3d7854a` makes the broker compare every canonical namespace
  field before reading Secret Manager: schema version, tenant, connector,
  fully-qualified secret resource, per-tenant service account, and isolation
  mode. A mismatch fails closed as `credential_namespace_mismatch`.
- Cloud Build `8c7d6e80-cfb0-4642-9ea3-f78c108740ac` completed `SUCCESS` with
  image digest
  `sha256:685ab0f488076dace3049c57ab1bdf2bce79c4d114d8f358384288187887250c`;
  Cloud Run revision `driftline-00012-trk` serves 100% of traffic. `/health`
  returned 200 with Firestore persistence and async jobs, the public invoker
  remained `allUsers`, and post-rollout logs have zero severity `ERROR`
  entries. The focused credential-broker suite is `8 passed`.

## 2026-08-20 Visual evidence outage fallback (live)

- Source commit `b50c982` keeps the fixed public visual evidence panel
  available when a GitHub byte fetch is temporarily unavailable. The strict
  multimodal helper still fails closed for live callers; the anonymous
  metadata route may return a clearly labelled `synthetic_demo` pair with a
  `fallback_reason`, and the UI switches asset/analysis requests to demo mode
  without claiming public bytes or Gemini execution.
- Cloud Build `efdeaf85-c64e-42eb-ae57-450421f261b1` completed `SUCCESS` with
  image digest
  `sha256:aa890284c3f6bfe2185d39488e737f3b8aad18dc0a5d5e64db1c3c895a5c577e`;
  Cloud Run revision `driftline-00013-d9g` serves 100% of traffic. `/health`
  returned 200, the live visual metadata route returned 200 with
  `data_mode=public_source` and a 64-character pair hash, and post-rollout
  logs have zero severity `ERROR` entries. The deployed desktop/mobile audit
  remains clean with no overflow, console errors, or failed requests.

## 2026-08-20 Final current-revision smoke (live)

- On revision `driftline-00013-d9g`, direct public `POST /api/agent/run`
  returned `200` with `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, `source_status=needs_approval`,
  `persisted=true`, workflow `bad5c77e-2730-4d11-8be6-c0e56faae0b5`, and
  allowlisted tools `inspect_source_change` and `get_workflow_state`.
  A follow-up workflow read returned Firestore-backed `public_source`,
  `await_approval`, five events, a 64-character evidence hash, and a redacted
  ADK trace.
- The final local suite is `201 passed` with 3 dependency deprecation
  warnings; Ruff, `git diff --check`, and the frontend production build pass.
  The final browser journey reported 4 rows, 2 selects, approval enabled,
  completed and reopened states, zero console errors, and zero failed requests.

## 2026-08-20 Scheduler fan-out smoke (live)

- The isolated Cloud Scheduler job `driftline-monitor` is enabled on the
  six-hour cadence `0 */6 * * *` and invokes the service with its dedicated
  OIDC service account. A manual run at `2026-08-20T19:54:13Z` returned
  `POST /api/scheduler/tick` HTTP 200.
- That tick created five bounded monitor jobs for the registered demo sources.
  All five completed through `execution_mode=google_adk` with
  `model=gemini-3.5-flash`; no job failures or post-tick severity `ERROR`
  logs were observed. Cloud Tasks remains bounded at three attempts, one
  concurrent dispatch, and 0.2 dispatches per second.

## 2026-08-20 Continuous verification gate (external)

- Source commit `5c279c2` adds `.github/workflows/verify.yml` for every push
  to `main` and every pull request. It has `contents: read` permissions only,
  uses no cloud credentials, and never deploys.
- GitHub Actions run `32411709745` completed successfully: backend Ruff plus
  the full Python suite and the locked frontend `npm ci`/production build all
  passed. Deployment remains an explicit Cloud Build step after this gate.
- Commit `26c1f03` refreshed the action runtimes to current Node 24-compatible
  majors; final-HEAD run `32411863662` passed both jobs without the prior
  Node 20 deprecation annotation.
- Commit `aed8020` aligns the backend job with the production resolver by
  installing `uv==0.8.17` and running `uv sync --locked`; run `32412237907`
  passed the frozen-lock backend suite and frontend build on the resulting
  source tree.

## 2026-08-20 Public repository hygiene (external)

- Read-only review of the public repository found 11 open issues whose bodies
  identified them as Driftline connector smoke-test artifacts (synthetic
  workflow IDs and evidence hashes, all authored by the repository owner).
  Issues `#1` through `#11` were closed as `not planned`; no source, secrets,
  or customer work were changed. The public open-issue count is now zero.

## 2026-08-20 Project IAM least-privilege audit (live)

- The isolated project-level IAM policy had an unused default Compute Engine
  service account with `roles/editor`. Driftline Cloud Run uses
  `driftline-runtime` and Cloud Build uses `driftline-build`, so the default
  identity was removed with an explicit unconditioned IAM update.
- A follow-up policy query found no remaining `roles/editor` binding for
  `724959673622-compute@developer.gserviceaccount.com`. The public health
  endpoint still returned HTTP 200 and Cloud Run remained on revision
  `driftline-00013-d9g` at 100% traffic.

## 2026-08-20 Dedicated Cloud Build deployment (live)

- Commit `7bcdb41` adds explicit `CLOUD_LOGGING_ONLY` configuration required
  for a custom Cloud Build service account and keeps deployment behind the
  project-guarded `scripts/deploy.sh` wrapper. The wrapper verifies the active
  gcloud project and selects `driftline-build` instead of the default Compute
  identity.
- Build `315a3056-d2fe-4a8b-b44a-9530989ae19a` completed `SUCCESS` as
  `projects/driftline-hackathon-2026/serviceAccounts/driftline-build@...`,
  produced image digest
  `sha256:48e4d5bcdc8ed6ec3ec44f0d1ac4d76a6b18a450529c4efa36fca23b0285cce8`,
  and deployed revision `driftline-00014-4ws` at 100% traffic.
- Post-deployment `/health` returned HTTP 200. A direct public agent run
  returned `execution_mode=google_adk`, `model=gemini-3.5-flash`,
  `persisted=true`, `data_mode=public_source`, and `source_status=needs_approval`;
  its Firestore workflow read showed five events, a 64-character evidence
  hash, and the redacted ADK trace. The new revision has no severity `ERROR`
  Cloud Logging entries.
- Commit `9030132` adds an explicit `.gcloudignore`; `gcloud meta
  list-files-for-upload` confirmed that only the two documented example env
  files are included while local `.env` files, virtualenvs, dependencies,
  generated bundles, and screenshots are excluded. Final-head GitHub Actions
  run `32413254910` passed the frozen-lock backend suite and frontend build.

## 2026-08-20 Multimodal fallback URL contract (live)

- Commit `e2f2b09` makes the visual evidence metadata route return asset URLs
  using the effective mode. If live bytes fail and the route returns a
  labelled `synthetic_demo` pair, both URLs now point to `mode=demo` instead
  of advertising unavailable live bytes. The regression suite remains
  `201 passed` with the multimodal fallback URL assertions included.
- Dedicated build `aa34fdca-eb78-43dd-becd-a50ddf08572f` completed `SUCCESS`
  as `driftline-build`, producing digest
  `sha256:9fca7188373628dcb7fad9f2c3e16108129209e436d4b665fedf015fe409c7cd`
  and revision `driftline-00015-gk5` at 100% traffic. `/health` returned 200,
  the live visual route returned public-source metadata with a 64-character
  evidence hash, and the new revision has no severity `ERROR` logs.

## 2026-08-20 Supply-chain maintenance gate (external)

- Repository credential-pattern scan found no committed API keys, private-key
  blocks, or provider token formats. `npm audit --audit-level=moderate` found
  zero info/low/moderate/high/critical vulnerabilities across the locked
  frontend dependency tree.
- Commit `2931e37` adds weekly Dependabot coverage for the backend `uv.lock`,
  frontend `package-lock.json`, and GitHub Actions. The final-head hosted
  verification run `32414028439` passed the frozen-lock backend suite and
  frontend production build.

## 2026-08-20 Scheduler spend retry bound (live)

- The enabled `driftline-monitor` Cloud Scheduler job previously had an
  unlimited retry duration. It is now bounded to two retries after the initial
  attempt (three total attempts), a five-minute retry window, five-second
  minimum backoff, and 60-second maximum backoff. The six-hour UTC cadence,
  OIDC identity, and exact `/api/scheduler/tick` target are unchanged.
- A post-update `gcloud scheduler jobs describe` confirmed `state=ENABLED`,
  `retryCount=2`, `maxRetryDuration=300s`, and `maxBackoffDuration=60s`.

## 2026-08-20 Anonymous job-history redaction (live)

- Commit `00c9267` adds a tenantless API boundary that removes caller query
  text, user IDs, raw model responses, failure details, and opaque Cloud Tasks
  claim IDs from public job history. It replaces them with a bounded status
  summary; signed tenant jobs retain their complete operational fields. The
  frontend agent trace and run history now render that safe summary.
- The local suite is `202 passed` with Ruff and the frontend production build
  passing. Dedicated build `a4034ca1-00a5-4060-83fd-49fc2452fc6e` completed
  `SUCCESS` as `driftline-build`, deploying revision `driftline-00016-kqd` at
  100% traffic. A live canary job submitted with sensitive text returned none
  of the five redacted fields and exposed only `public_summary`; `/health`
  returned HTTP 200 and the revision has no severity `ERROR` logs.
- The anonymous `/api/jobs/demo` lane also now ignores caller-provided query
  and user identity fields, sending only a fixed allowlisted instruction to
  Gemini. Signed tenant monitor requests retain their explicit query and
  identity contract; the new regression suite is `203 passed`.
- Commit `e570b87` was deployed by dedicated build
  `1d1f0213-5796-4d3f-988d-37f516ad0ec1` as revision `driftline-00017-s8x` at
  100% traffic. A live public request containing a sensitive canary returned
  `user_id=public-demo` and the fixed allowlisted query; `/health` returned
  200 and the revision has no severity `ERROR` logs.

## 2026-08-20 Anonymous direct-agent input hardening (live)

- Source commit `f58065a` applies the same fixed-input contract to the direct
  public `POST /api/agent/run` lane. Anonymous caller query text and user IDs
  are replaced before Gemini or any durable workflow write; signed tenant
  requests retain their operator query and tenant identity.
- Local verification passed `203` backend tests, Ruff, and the frontend
  production build. GitHub Actions run
  `https://github.com/mikeyerke/driftline/actions/runs/32415707755` passed the
  preceding documentation commit; the source commit itself was then promoted
  through dedicated Cloud Build
  `8ea58385-0a1d-4f6e-ac42-18ed59ba938c`.
- Cloud Run revision `driftline-00018-4v9` serves 100% of traffic. A live
  direct-agent request containing a sensitive canary returned
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and the two allowlisted
  tool calls while returning no `query` or `user_id`; `/health` returned 200.

## 2026-08-20 Tenant RSS/Atom source parser (live)

- Source registry onboarding now accepts the explicit `rss` parser alongside
  `html` and `text`. It fetches only the caller's exact HTTPS URL, rejects
  redirects/private DNS/challenge pages as before, parses bounded RSS/Atom
  entries, and stores normalized titles, dates, links, and summaries rather
  than raw XML. The source remains tenant-scoped and scheduler-capped.
- Local regression is `199 passed`; the focused source suite is `14 passed`.
  Cloud Run revision `driftline-00011-mnz` exposes the OpenAPI parser enum
  `["html", "text", "rss"]`; `/health` returned 200. No external feed was
  registered or claimed because no tenant target was supplied.

## 2026-08-20 Canonical tenant credential control plane (live)

- Source commit `3ba7554` is the checked-in tenant-boundary release. Connector
  profiles and bindings are validated against `driftline_tenants/{tenant_id}`;
  each binding resolves only through its tenant namespace, pinned Secret
  Manager version, explicit connector operation scope, and impersonated
  tenant identity. Raw credential values are never returned or written to
  Firestore. The old flat binding collection is a migration artifact and is
  read-only unless the explicit compatibility flag
  `DRIFTLINE_WRITE_LEGACY_CONNECTOR_MIRROR=true` is enabled.
- The live Cloud Run revision is `driftline-00005-qh6`, serving 100% of traffic
  in `driftline-hackathon-2026`. It uses image digest
  `sha256:34f2610659511e1b957d49a2ec16cb715be2818dd934ae6fe83879a998c755e0`
  from Cloud Build `31dc6793-0240-4698-b569-db2e1de0cea6` (`SUCCESS`). The
  active env confirms `DRIFTLINE_REQUIRE_TENANT_CREDENTIAL_NAMESPACE=true`,
  `DRIFTLINE_WRITE_LEGACY_CONNECTOR_MIRROR=false`, and task, scheduler, and
  Salesforce callback URLs use the exact public `...xvxczqg62a-uc.a.run.app`
  host.
- `/health` returned `200` after deploy. Cloud Tasks queue `driftline-jobs` is
  `RUNNING`, max concurrent dispatches `1`, max attempts `3`; a fresh browser
  workflow dispatched through `POST /api/jobs/{id}/run` and persisted a
  `needs_approval` job (`job-c99775eefb59`, workflow
  `9441fb8a-7f2a-4924-b25d-a8018c27e58e`). Its 12-event audit trail includes
  evidence verification, four mapped artifacts, approval, packet creation, and
  decision reopening. The public URL remains
  `https://driftline-xvxczqg62a-uc.a.run.app/`.
- This is a production tenant-scoped credential data-plane foundation, not a
  claim of complete self-serve SaaS: enterprise SSO, customer-managed keys,
  per-tenant billing, automated provider consent, and an independently
  measured customer pilot are still separate gates.

## 2026-08-20 Connector destination SSRF hardening (live)

- Source commit `e13a4ae` validates connector destination profiles before
  persistence and repeats the check when adapters are constructed. Jira and
  Confluence accept only Atlassian Cloud/scoped gateway hosts; Slack accepts
  `slack.com`; GitHub accepts the GitHub API host family; Salesforce accepts
  Salesforce/Force domains. HTTPS is required and userinfo, query credentials,
  and fragments are rejected.
- Cloud Build `811f8d1e-825b-4aab-9898-a0a47fb766ec` completed `SUCCESS`; image
  digest is
  `sha256:9b539163daff78ecb03472a1c833082bc723cd9000fea71b50e719436334c116`.
  Cloud Run revision `driftline-00006-ncb` serves 100% of traffic and `/health`
  returned `200`.
- A live unauthenticated malicious Slack profile attempt returned `422
  connector_profile_url_not_allowlisted`. The signed `driftline-demo` Slack
  profile was rechecked afterward and remains the intended
  `https://slack.com/api/` plus channel `C0BRGFUSADA`; no credential value was
  returned. Post-deploy logs contained zero severity `ERROR` entries.
- Regression suite is `195 passed`; Ruff and `git diff --check` are clean.

## 2026-08-20 Tenant quota and privacy policy release (current)

- Source commit `fcae79c` adds durable, owner-managed tenant policy for
  `agent_calls_per_window`, `workflow_mutations_per_window`, and bounded
  `retention_days` (`1..3650`). Quota values are used by both local and
  Firestore reservations; tenant source observations, workflow/job, failure,
  outcome, and credential-access metadata now receive the tenant TTL. Missing policy
  metadata falls back to deployment defaults; a hosted quota lookup failure
  fails closed and a retention lookup failure uses the bounded default.
- Signed `GET/POST /api/tenants/policy` is live. Anonymous policy access
  returned `401 Signed approval is required`; a live signed read for the
  existing `driftline-demo` tenant returned the bounded policy (`10` agent
  calls, `30` workflow mutations, `30` retention days), `billing_enabled=false`,
  and `credential_values_exposed=false`. The public Value proof remains
  `observed_driftline_sandbox_records` with `0` tenant-scoped workflows.
- Cloud Build `aefbb6f3-051c-44ed-8bcc-28b4a5715aaf` completed `SUCCESS`; image
  digest is
  `sha256:beeae2d98e182ca7752963eaf55ecc668d05cc89903f00119031d07c07903606`.
  Cloud Run revision `driftline-00170-m6c` serves 100% of traffic in the
  isolated project and `/health` reports Firestore persistence and async jobs.
- Full backend suite: `187 passed`; Ruff, frontend production build, and
  `git diff --check` are clean. Desktop/mobile browser QA and the complete
  scan → evidence → artifact → approval → completion → reopen journey passed
  with no console errors or failed requests. Latest verified job is
  `job-dd9c790526a5`, workflow `d083ea27-fb6f-4bba-aa8c-039689c76bb8`, recorded
  with Gemini 3.5 Flash and Google ADK.

## 2026-08-20 Exact tenant evidence scope release (superseded snapshot)

- Source commit `f1cf108` makes anonymous record reads strictly tenantless and
  makes signed operational reads exact-tenant only. This prevents a signed
  customer metric from mixing deployment-wide demo activity into its evidence.
  The public Value proof panel is explicitly labeled `Public sandbox records`
  and remains an anonymous, judge-safe surface.
- Cloud Build `64889270-0bcf-4bc2-be43-03f42003f4b0` completed `SUCCESS`; image
  digest is
  `sha256:821c6f6a82d43b9b93698c26a615336998eb204745f32a58ceedcb56dff88bd5`.
  Cloud Run revision `driftline-00166-n74` serves 100% of traffic in
  `driftline-hackathon-2026`; `/health` reports Firestore persistence and async
  jobs. The active project was verified before deployment.
- The current anonymous proof window reports `50` workflows: `47`
  `public_source` and `3` `synthetic_demo`, all `50` tenantless. These mode
  categories are mutually exclusive; separate job modes report `37` demo and
  `9` monitor jobs. They are isolated deployment observations, not customer,
  revenue, adoption, or ROI claims.
- Post-deploy error logs at or after `2026-08-20T15:45:00Z` are empty. Cloud Run
  invoker policy remains intentionally public for the packet-only demo plus the
  scheduler service identity. Desktop/mobile browser QA and the complete
  scan → evidence → artifact → approval → completion → reopen journey passed
  with no console errors or failed requests; latest verified job is
  `job-663297c3cd4c` and workflow `4d83dbce-900f-42f1-9aec-23778e75b4ab`.

## 2026-08-20 Evidence-mix transparency release (superseded snapshot)

- Source commit `876e98b` adds an explicit evidence-mix breakdown to the public
  Value proof panel and makes signed value metrics report
  `observed_tenant_records`. The API separates workflow `data_mode` counts and
  job run modes, and exposes tenant-scoped versus tenantless record counts.
  This prevents sandbox activity from being misread as customer traction.
- Cloud Build `6ee6f0cb-244f-471c-a30d-4e62cd1bb3cb` completed `SUCCESS` after
  the Cloud Run deploy race settled; image digest
  `sha256:a0d1602c1f4cc6bb00a132220492442b67060a2b1809e6d25164c51d442f49b6`,
  Cloud Run revision `driftline-00164-r6r` serves 100% of traffic. The live
  service remains in project `driftline-hackathon-2026`, with scale-to-zero and
  max-one settings unchanged.
- At that earlier snapshot, public value proof reported `41` public-source
  workflows and `4` synthetic replays. The exact-scope release above is the
  authoritative current count; this historical count is retained for audit
  continuity only.
- The final desktop/mobile audit passed with no overflow, console errors, or
  failed requests. The complete journey passed scan, evidence, artifact
  selection, approval, completion, and reopen/undo; latest verified job is
  `job-12c151671648`, workflow `00b6ce22-ab09-421c-a59a-01332cc8a5ab`, with
  `gemini-3.5-flash` and `google_adk` recorded.

## 2026-08-20 Tenant credential enrollment release (current)

- Source commits `19d7887` and `dec00ac` add the tenant-scoped credential
  enrollment seam. Owners can start a 15-minute, secret-free session at
  `POST /api/connectors/{connector}/credential-enrollment`; new sessions
  default to `runtime` and `read_context`, and requested operations are
  validated against the fixed connector allowlist. After a provider version is
  added out of band, the signed completion route verifies the exact tenant
  secret, pins its version, activates the canonical binding, and closes the
  session. Enrollment records live below
  `driftline_tenants/{tenant}/credential_enrollments/{id}` and never store raw
  credential values.
- Local release verification is `182 passed`; Ruff, frontend production build,
  and `git diff --check` are clean. The focused enrollment test proves a
  tenant cannot load another tenant's enrollment and that the completed binding
  retains only the explicit read-only scope.
- Cloud Build `58faca0d-f27b-4ba4-aedd-82b6e63901f4` completed `SUCCESS`; image
  digest `sha256:1a9e1c580a08b392e7312a0fe829383e36d067fa5b9a142eda9155c177e4aea1`,
  Cloud Run revision `driftline-00163-kl9` serves 100% of traffic. The build
  emitted the known IAM warning while the live policy was rechecked and still
  contains `allUsers` plus the scheduler identity.
- Fresh live verification: `/health` returned Firestore persistence and async
  jobs; an anonymous enrollment attempt returned `401 Signed approval is
  required`; Cloud Run reported no `severity>=ERROR` entries since deploy.
  The final desktop/mobile browser audit and the prior complete journey both
  passed with no overflow, console errors, or failed requests. The public
  console remains tenantless, synthetic, and packet-only.

## 2026-08-20 Durable value proof and history merge release (current)

- Source commits `1d2196e` and `fdb086a` add the public Value proof panel and
  fix an instance-boundary undercount in operator history. Hosted summaries,
  change memory, job history, and value proof now merge bounded Firestore
  records with the in-flight Cloud Run cache, deduplicated by durable ID; the
  current instance wins for an in-progress transition. Local regression is
  `179 passed`; Ruff, frontend production build, and `git diff --check` are
  clean.
- Cloud Build `3a53460f-aa3e-45e2-943c-2d0ce13e4d5f` completed `SUCCESS`; image
  digest `sha256:e985aa1241aa67c1964655d176071f043e2c240c00aa7a4a29fd7c0c2e6c18a5`,
  Cloud Run revision `driftline-00161-5jc` serves 100% of traffic. The build
  emitted an IAM warning while preserving the already-verified `allUsers`
  invoker binding; the live policy was checked after deployment.
- Public `/health` returned Firestore persistence and async jobs. The live
  value-proof endpoint from a fresh instance reported `40` durable jobs, `37`
  durable workflows, `27` source observations, and five healthy sources. It
  explicitly keeps hours saved, revenue/win-rate lift, retention impact, and
  willingness-to-pay in `not_measured`.
- Headless Chrome at 1440px and 390px passed with no overflow, console errors,
  or failed requests. The corrected end-to-end journey passed scan, evidence,
  artifact selection, custom `Owner review` routing, approval, packet
completion, and reopen/undo. Latest verified job is `job-f78894009a9e` and
  workflow `03788b14-b0a8-4bff-a827-ba61052d0e12`; its persisted trace is
  `google_adk` / `gemini-3.5-flash`, both structured analysis and Decision
  Copilot are `gemini_structured`, policy review is `pass`, and the audit chain
  contains `approval_recorded` with the explicit copilot override marker and
  `decision_reopened` with `external_write=false`.

## 2026-08-20 Decision Copilot and artifact-routing release (current)

- Source commits `bb95199` and `25136a4` keep the copilot's reviewed option id
  while marking an operator's artifact-route change as an explicit custom
  override. The API revalidates complete artifact coverage, allowlisted
  actions, high-risk routing, and a human-provided reason before recording the
  plan and audit event. The Decision Copilot output budget was raised to fit
  three evidence-bound options across four artifacts; a fresh public run
  verified `decision_copilot.mode=gemini_structured` with
  `model=gemini-3.5-flash`, not the deterministic demo fallback.
- Cloud Build `7711374d-9907-4696-83e2-eb6d1137288d` completed `SUCCESS`; image
  digest `sha256:c07b8593d2cea458cc4ced86eb758e52c40f7ec2286d8c22dab502a63f94425e`,
  Cloud Run revision `driftline-00159-g9d` serves 100% of traffic.
- Public `/health` returned Firestore persistence and async jobs. Headless
  Chrome at 1440px and 390px passed with no overflow, console errors, or
  failed requests. The live journey passed scan, evidence, artifact
  selection, manual `Owner review` routing, approval, packet completion, and
  reopen/undo; the final browser state was `Decision reopened · no external
  systems were changed` with `sawNeedsApproval=true`, `sawCompleted=true`,
  and `sawReopened=true`. The latest durable job is
  `job-9548be0d202b` and workflow `acf228c7-903d-4039-a274-e07239141b58`;
  its Firestore trace records Gemini structured impact analysis and a
  Gemini structured decision copilot; the approval and reopen events are
  persisted with `external_write=false`. The custom-routing path is covered
  by the local API regression tests and records its option id and reason when
  exercised.
- Local regression is `178 passed`; Ruff and the frontend production build
  are clean. The public lane remains synthetic and packet-only; authenticated
  connectors remain tenant-scoped and signed.

## 2026-08-20 Artifact-routing override release (historical)

- Source commit `11348a5` keeps the copilot's reviewed option id while marking
  an operator's artifact-route change as an explicit custom override. The API
  revalidates complete artifact coverage, allowlisted actions, high-risk
  routing, and a human-provided reason before recording the plan and audit
  event; the previous false `409 Artifact decisions do not match` response is
  gone without creating a policy bypass.
- Cloud Build `7cb9a192-b403-4f14-aa53-eff9d60ce3e3` completed `SUCCESS`; image
  digest `sha256:cf2de9ba2390ab6f336e5aa2e352e3b8ca68369ef4eedbbc1d746a108f6555b4`;
  Cloud Run revision `driftline-00157-ck5` serves 100% of traffic.
- Public `/health` returned Firestore persistence and async jobs. Headless
  Chrome at 1440px and 390px passed with no overflow, console errors, or
  failed requests. The live journey passed scan, evidence, artifact selection,
  manual `Owner review` routing, approval, packet completion, and reopen/undo;
  the final browser state was `Decision reopened · no external systems were
  changed` with `sawNeedsApproval=true`, `sawCompleted=true`, and
  `sawReopened=true`. The latest durable job is `job-d8770ab35c36` and
  workflow `b020f014-845c-4e36-b20c-f829a212fee0`; its Firestore event chain
  includes `approval_recorded`, four artifact decisions, a packet summary, and
  `decision_reopened`, with `external_write=false` and a persisted rollback
  marker.
- Local regression remains `175 passed`; the production frontend build and
  `git diff --check` are clean. The public lane remains synthetic and
  packet-only; authenticated connectors remain tenant-scoped and signed.

## 2026-08-20 Responsive navigation and browser journey release (current)

- Source commit `773b7e6` changes the narrow layout from a partially hidden
  horizontal navigation strip to a visible 3×2 navigation grid, keeping
  Overview, Sources, Workflows, Approvals, Activity, and Settings discoverable
  at first render on mobile widths.
- Cloud Build `e06778f7-ac2a-47e1-b6b7-60ef619e8927` completed `SUCCESS`; image
  digest `sha256:04a1f357ba6c13104e049f501b9bc9e6c806f1b501f5e57d0c564f3f9e017440`;
  Cloud Run revision `driftline-00153-zbz` serves 100% of traffic.
- Headless Chrome against the public alias passed at 1440px and 390px: no
  document overflow, console errors, or failed requests; the evidence modal
  opened at both widths. The full public journey passed scan → artifact row
  selection → decision selection → approval → reopen/undo, with no console or
  network errors. The run created a live Firestore workflow and the final UI
  state visibly returned to `Decision reopened · no external systems were
  changed`.
- Local production frontend build and `git diff --check` are clean. The public
  app remains packet-only for anonymous users; configured connector writes
  still require a signed tenant operator.

## 2026-08-20 Credential cutover and slow-ADK journey release (current)

- Source commits `7d34973` and `e1af9a6` harden the shared SaaS credential
  boundary and the public run path. In hosted strict namespace mode, missing
  canonical `driftline_tenants/{tenant}/credentials/{connector}` records never
  fall back to the legacy flat mirror; connector resolution and inventories
  fail closed until migration is complete. The console also polls durable ADK
  jobs for up to 126 seconds, inside the 300-second Cloud Run budget, so a
  slower cold-started Gemini run is not mislabeled as a client timeout.
- Cloud Build `b6dd62cb-b86a-4d9d-93ac-8e746f8291f6` completed `SUCCESS` for
  the credential cutover; image digest `sha256:1cdb5754f359f517efc850e78b5101d2cbddfcd47959f5dc6ac7973c22a75849`,
  Cloud Run revision `driftline-00154-4cv` served 100% of traffic. Cloud Build
  `2902980a-9c7c-49cd-a4be-909b122c13ad` completed `SUCCESS` for the polling
  fix; image digest `sha256:7ed187081008bb31150d92c36aa8cc79d1f1201abb18fec84456813bc6e16d43`,
  Cloud Run revision `driftline-00155-82w` serves 100% of traffic.
- Live proof on the public alias: `/health` returned Firestore persistence and
  async jobs; desktop and 390px Chrome journeys had no console errors, failed
  requests, or document overflow. The final end-to-end journey passed live
  scan, artifact selection, decision selection, approval, packet completion,
  and reopen/undo, with `sawNeedsApproval=true`, `sawCompleted=true`, and
  `sawReopened=true`. The resulting Firestore-backed job was
  `job-8ac5cf45f80e` and workflow `051817f9-a65e-4c35-ab60-029dab0c2869`;
  its audit events include `approval_recorded` and `decision_reopened`.
- Local regression remains `175 passed`; Ruff and the frontend production build
  pass. The anonymous lane remains a synthetic, packet-only evaluation surface;
  authenticated connectors remain tenant-scoped and signed.

## 2026-08-20 Durable tenant discovery and selection release (current)

- Source commit `4aeb73d` adds the identity-only `GET /api/tenants/available`
  contract and durable membership discovery. A Google OIDC identity with one
  active membership can resolve that tenant without inheriting the demo
  default; identities with multiple active memberships must select a tenant;
  unknown, disabled, malformed, or partial tenant records fail closed. The
  response contains only tenant/role metadata and `credential_values_exposed=false`.
- Cloud Build `535f2cf5-9b6c-412c-b348-a5aaac9270fb` completed `SUCCESS`; image
  digest `sha256:54a773bb5fbab49875345a0e1145cac44919c8692c24a026c05d1013e6c41b60`;
  Cloud Run revision `driftline-00152-9gm` serves 100% of traffic.
- Live proof: the active Cloud Run URL returned `/health` with Firestore
  persistence and async jobs, the console returned HTTP 200, and
  `/api/tenants/available` returned `401` without an OIDC identity. Public
  `/api/agent/run` returned HTTP 200 with `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, `source_status=needs_approval`, and
  `persisted=true`; its Firestore workflow retained raw source evidence,
  contained no credential terms, and contained no model sanitizer marker.
  The active revision had zero `severity>=ERROR` log entries.
- This completes the tenant identity/selection layer for the credential data
  plane. It does not claim customer-managed KMS keys, self-serve billing, a
  second-customer pilot, or Salesforce consent; those remain explicitly
  unverified product/commercial gates.
- Local regression is `175 passed`; Ruff, production frontend build, and
  `git diff --check` are clean.

## 2026-08-20 Per-tenant Secret Manager identity release (current)

- Source commit `8950abc` adds a deterministic, collision-resistant Google
  service-account identity for every tenant. The shared Cloud Run identity can
  impersonate only the derived tenant identity; the tenant identity alone has
  Secret Manager access to that tenant's connector and operator-signing
  secrets. Salesforce refresh-token version writes are scoped to that tenant's
  Salesforce secret. Direct runtime grants on the live `driftline-demo` tenant
  secrets were removed after the new revision was verified.
- Tenant identity provisioned:
  `driftline-driftline-de-7f8fce0@driftline-hackathon-2026.iam.gserviceaccount.com`.
  The runtime has only `roles/iam.serviceAccountTokenCreator` on this exact
  identity; no key was created.
- Cloud Build `8a4c5f34-57f0-4ca5-817c-28cc0b86c04d` completed `SUCCESS`; image
  digest `sha256:42c5926f6175cdb173bc7ea0d3c57a50107fdd983ad85010d99fdd81767a7a5e`;
  Cloud Run revision `driftline-00149-z6f` serves 100% of traffic with
  `DRIFTLINE_TENANT_SECRET_IDENTITY_MODE=impersonated`.
- Live proof: `/health` returned Firestore persistence and async jobs, root
  returned HTTP 200, public invoker remained present, and the active revision
  had zero `severity>=ERROR` entries. Signed credential inventory and binding
  health succeeded through the impersonated identity; all four configured
  connector secrets were readable and Salesforce remained explicitly
  `not_configured`. Signed aggregate reads for Jira, Confluence, Slack, and
  GitHub succeeded. Signed ADK returned `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and `source_status=unchanged`.
- Local regression is `163 passed`; Ruff, shell syntax, and `git diff --check`
  are clean. The public synthetic demo remains packet-only and reliable.

## 2026-08-20 Tenant credential version-pinning release (current)

## 2026-08-20 Multi-tenant credential broker release (current)

- Source commits `5a9034c` and `b0cb211` add the credential-broker seam. Every
  tenant connector now resolves only `(tenant, connector, operation)` through
  the broker, which checks the active binding, exact deterministic Secret
  Manager reference, operation scope, and pinned version before issuing a
  short-lived in-process lease. Binding metadata now carries a stable
  `credential_id`, backend/scope metadata, and allowlisted operations.
- Cloud Build `126a9c3b-a38b-4380-92b8-746bd6e8edc3` completed `SUCCESS`; image
  digest `sha256:f7a216107c2c84b98d88719b7e8125cd4a89d33feb384f0dd45c80b9cb529cf8`;
  Cloud Run revision `driftline-00147-wv4` serves 100% of traffic.
- Live proof: `/health` returned Firestore persistence and async jobs, root
  returned HTTP 200, public invoker remained present, the active revision had
  zero `severity>=ERROR` logs, and signed context reads through all four
  configured connectors succeeded. Signed credential inventory returned four
  tenant-scoped records with `secret_version=1`, operation scopes, and
  `credential_values_exposed=false`; the signed access trail recorded resolved
  leases for all four connectors without token values or provider bodies. A
  signed `/api/agent/run` returned `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and `source_status=unchanged` without fabricating
  a workflow; the public demo still returned `data_mode=synthetic_demo` and
  `status=needs_approval`.
- New signed routes: `/api/connectors/credentials` (metadata-only inventory)
  and `/api/connectors/credentials/access` (tenant-filtered append-only lease
  audit). Salesforce health uses the same broker seam; OAuth callback binding
  metadata uses the same operation scope contract.
- The access ledger is `driftline_credential_access_events` with the normal
  30-day expiry. Firestore TTL for `expires_at` is `ACTIVE` in the isolated
  project, so the lease audit receives the same automated bounded cleanup.
  This is a real multi-tenant
  credential-control-plane foundation; customer-managed keys, self-serve
  SSO/billing, and per-tenant worker IAM remain explicit SaaS gaps.
- Local regression is `162 passed`; Ruff and `git diff --check` are clean.

- Source commits `245b149` and `457c7f8` add version-aware tenant Secret
  Manager bindings. An active binding records the resolved provider version
  at owner verification; connector calls use that pinned version. Rotation
  moves the binding to `rotation_pending` and fails closed until the owner
  re-verifies the replacement. Legacy bindings without a version remain on
  `latest` only until their next verification.
- Cloud Build `f8f264fc-89a7-459d-b989-c58d459e51d7` completed `SUCCESS`; image
  digest `sha256:b4355fcb6a37294fafb3975dcf3051a07c7a0e114e650a184986666a56fa2c67`;
  Cloud Run revision `driftline-00144-rjf` serves 100% of traffic.
- Live proof: `/health` returned Firestore persistence and async jobs, root
  returned HTTP 200, the public invoker binding remained present, the active
  revision has zero `severity>=ERROR` logs, and hosted static tenant admission
  bindings are absent. Signed metadata for the four configured connectors
  reports `secret_version=1`, `status=active`, and `credential_values_exposed=false`.
  The signed aggregate context probe succeeded for Jira `KAN`, Confluence
  `DRIFT`, Slack `C0BRGFUSADA`, and GitHub `mikeyerke/driftline` while returning
  no source bodies or message text.
- The isolated deployment still has one verified tenant (`driftline-demo`),
  not a claim of a second-customer pilot or a full hosted identity/billing
  product. Per-tenant control-plane records, deterministic secret namespaces,
  owner-only lifecycle, audit, and quota boundaries are live; provider token
  revocation and destructive secret deletion remain explicit offboarding steps.
- Local regression is `155 passed`; Ruff and `git diff --check` are clean.

## 2026-08-20 Durable terminal-failure ledger release (current)

- Source commit `ea29b6a` records a metadata-only terminal marker in
  `driftline_job_failures` when a Cloud Tasks job exhausts its three bounded
  attempts. The signed `/api/ops/job-failures` route filters by the caller's
  tenant and excludes prompts, source bodies, exception text, and credentials;
  public `/api/ops/summary` reports zero cross-tenant failure counts.
- Cloud Build `871a4ed7-9702-441c-bfd7-b890f618c521` completed `SUCCESS`; image
  digest `sha256:b561922052ab67abc8e4d79a4c847bb2e31ddeab2bdd2f757844195cf6f4b514`;
  Cloud Run revision `driftline-00145-ddh` serves 100% of traffic.
- Live proof: `/health` returned Firestore persistence and async jobs, root
  returned HTTP 200, the public invoker binding remained present, the active
  revision has zero `severity>=ERROR` logs, and hosted static tenant admission
  bindings are absent. Public ops reported `dead_lettered=0`; the signed
  `driftline-demo` failure ledger returned an empty, redacted list with a
  30-day retention contract. Local regression is `157 passed`; Ruff and
  `git diff --check` are clean.
- Firestore TTL for `driftline_job_failures.expires_at` is now `ACTIVE` in the
  isolated project, so terminal markers receive the same automated bounded
  cleanup as jobs, workflows, source observations, and outcomes.

## 2026-08-20 Signed live-mode guard release (current)

- Source commit `155c184` makes a tenant-signed direct ADK run explicitly use
  `run_mode=live`. A source outage, challenge page, or missing baseline can no
  longer silently become a synthetic workflow; the public judge lane remains
  the only path that uses deterministic replay.
- Cloud Build `dd1d0646-f600-4d5e-bfec-d1e5986dfd96` completed `SUCCESS`; image
  digest `sha256:dc3d6164c1b71caef3bfa629a32dc4eec9ee3e666cc3a96b70ef15030b70af15`;
  Cloud Run revision `driftline-00141-jrx` serves 100% of traffic.
- Live proof: `/health` returned `ok`, root returned HTTP 200, the active
  revision has zero `severity>=ERROR` log entries, and no static tenant
  admission bindings are present. A public demo run returned
  `data_mode=synthetic_demo` as intended. A signed tenant run against the
  allowlisted `competitor/pricing` source returned
  `execution_mode=google_adk`, `model=gemini-3.5-flash`,
  `source_status=baseline_established`, `change_detected=false`, and no
  workflow, proving the live lane did not fabricate a change when no new
  observation existed.
- Local regression is `154 passed`; Ruff and `git diff --check` are clean.

## 2026-08-20 Durable membership admission release (current)

- Source commit `21dc3f7` removes the hosted deployment-wide
  `DRIFTLINE_OPERATOR_EMAILS` and `DRIFTLINE_TENANT_MEMBERS` bindings. OIDC
  tenant admission now relies on the durable Firestore membership directory;
  adding an active tenant membership no longer requires a Cloud Run redeploy.
  The static mappings remain supported only for local/bootstrap compatibility.
- Cloud Build `f396e081-b67b-49ee-8119-13dd0f152adb` completed `SUCCESS`; image
  digest `sha256:fe048e3d54963201561606c1f0bc913ca1bfd185977ee3508bdc4def89f38281`;
  Cloud Run revision `driftline-00140-8r2` serves 100% of traffic.
- Live proof: the active revision has no hosted `DRIFTLINE_OPERATOR_EMAILS` or
  `DRIFTLINE_TENANT_MEMBERS` environment bindings; `/health` returned `ok`,
  root returned HTTP 200, public invoker bindings remained present, and the
  revision has zero `severity>=ERROR` log entries. The tenant-specific HMAC
  operator lane remains authorized against the durable active tenant directory:
  signed `/api/ops/summary` reported `membership_source=firestore` and
  `static_operator_allowlist=false`, while a live signed ADK run created
  workflow `26fa06b5-bc9c-4d27-871d-fcdba8d3b8eb` with
  `tenant_id=driftline-demo`, `status=needs_approval`, and a persisted
  `gemini-3.5-flash` trace using only the two allowlisted tools.
  A user-account Google OIDC token was not minted by the local gcloud CLI
  because custom-audience identity tokens require a service account; the OIDC
  path remains covered by local membership tests and is not claimed as a live
  browser proof in this release.
- Local regression is `154 passed`; Ruff and `git diff --check` are clean.

## 2026-08-20 Durable ADK trace release (current)

- Source commit `25180b8` makes the direct signed `/api/agent/run` path persist
  its redacted Google ADK/Gemini trace on the tenant workflow itself. The
  record contains model, execution mode, allowlisted tool calls, structured
  analysis, and decision-copilot policy metadata; prompts, source bodies, and
  connector credentials are excluded.
- Cloud Build `bc2cb13c-84ea-4cfd-8b90-19cae57c14fe` completed `SUCCESS`; image
  digest `sha256:18c0cc97b274dcfe07abc7c7cd5fd67fbbc5c5810224e5fdee895b620e896d69`;
  Cloud Run revision `driftline-00139-g5n` serves 100% of traffic.
- Live proof on the public service: `/health` returned `ok`, root returned
  HTTP 200, the active revision has zero `severity>=ERROR` log entries, and
  the tenant-signed ADK run created workflow
  `e6f52052-5b4b-49f0-a12a-ef9ff0f869d0` with
  `tenant_id=driftline-demo`, `status=needs_approval`,
  `data_mode=public_source`, model `gemini-3.5-flash`, execution mode
  `google_adk`, and only `inspect_source_change` plus `get_workflow_state`.
  A signed read of that Firestore-backed workflow returned the same trace and
  five audit events. Local regression is `154 passed`; Ruff and
  `git diff --check` are clean.

## 2026-08-20 Tenant credential rotation release

- Source commits `de9480e` and `f1b1e39` expose monitor source-failure counts
  and add the rotation lifecycle; this release
  also adds the owner-only `POST /api/connectors/{connector}/binding/rotate`
  lifecycle gate. It records an append-only rotation audit event, moves the
  tenant binding to `rotation_pending`, and makes connector reads/writes fail
  closed until a replacement version is added to the deterministic tenant
  Secret Manager secret and the normal owner binding verification route is
  repeated. No endpoint accepts or returns a credential value or arbitrary
  secret name.
- Cloud Build `b87762f2-ee97-4411-ab1e-870dbbb058c8` completed `SUCCESS`; image
  digest `sha256:321ae22b7791d60587eae14d9ea7a571b83287faa775f57bce4ea2123d5c79cb`;
  Cloud Run revision `driftline-00135-65c` serves 100% of traffic.
- Live proof: `/health` returned `ok`; `/api/monitor/registry` reported five
  healthy sources, zero stale sources, and `source_failed=0`; the newest
  revision has zero `severity>=ERROR` log entries. Local regression is
  `152 passed`; Ruff and `git diff --check` are clean.
- The credential control plane is now tenant-scoped for this deployment:
  durable tenant directory and memberships, owner-only binding activation,
  audited rotation/revocation, deterministic per-tenant Secret Manager names,
  per-secret runtime IAM, and soft deprovisioning. Customer login/SSO,
  billing, and provider-token destruction are intentionally separate product
  surfaces and are not represented as complete SaaS features.

## 2026-08-20 Rotation retry-safety release

- Source commit `0960ec1` makes owner credential rotation idempotent: repeated
  requests preserve the original `rotation_id`, do not create duplicate audit
  events, and reject revoked or otherwise non-rotatable bindings.
- Cloud Build `6358ccf2-0a96-4eb7-abe3-0b5eb6d07e92` completed `SUCCESS`; image
  digest `sha256:98e8598ee67fa4331eba9c3dbd37e7e1ccc4e9ec654812b6ff3a6f03f297517d`;
  Cloud Run revision `driftline-00136-t2r` serves 100% of traffic.
- Live proof: `/health` returned `ok`; the unauthenticated rotation route
  returned `401 Signed approval is required`; the newest revision has zero
  `severity>=ERROR` log entries. Local regression remains `152 passed`.

## 2026-08-20 Tenant bootstrap contract correction

- Source commit `3e3e9bf` includes Salesforce in the platform tenant bootstrap
  `secret_references` contract, so all five connector namespaces are returned
  consistently (`jira`, `confluence`, `slack`, `github`, `salesforce`).
- Cloud Build `6fd679f6-957b-43df-9eec-4fefdaadc303` completed `SUCCESS`; image
  digest `sha256:22dd01920ebd9974e86f4f1329dc6fd9655f0c7652d3f447c701db45d0f60485`;
  Cloud Run revision `driftline-00137-fm5` serves 100% of traffic.
- Live proof: `/health` returned `ok`; the live OpenAPI contract contains both
  the platform bootstrap route and rotation route; the newest revision has
  zero `severity>=ERROR` log entries. Local regression remains `152 passed`.

## 2026-08-20 Tenant binding health release

- Source commit `e97b5ce` adds the signed, read-only
  `GET /api/connectors/bindings/health` reconciliation probe. It enumerates
  all five connector namespaces, checks active bindings against the exact
  deterministic Secret Manager secret, and reports metadata-only
  `healthy`, `attention`, or `not_configured` states.
- Cloud Build `75d90549-7868-4b65-809c-afae7f92f1db` completed `SUCCESS`; image
  digest `sha256:a55226fc54c42e7a993c915dd1fd9a818bbe2e740ca8d7a9d26a678851aec6a9`;
  Cloud Run revision `driftline-00138-zdr` serves 100% of traffic.
- Live proof: `/health` returned `ok`; unauthenticated binding-health access
  returned `401 Signed approval is required`; the live OpenAPI contract exposes
  the route; the newest revision has zero `severity>=ERROR` log entries. Local
  regression is `153 passed`. A tenant-signed live probe returned four
  readable active bindings (Jira, Confluence, Slack, GitHub), one honest
  `not_configured` Salesforce binding, zero attention states, and
  `credential_values_exposed=false`.

## 2026-08-20 Tenant signer isolation release

- Source commit `6dfd885` adds deterministic tenant-specific break-glass
  signing. OIDC remains the preferred operator identity; the hosted release
  requires `DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS=true` and reads only
  `driftline-tenant-operator-<tenant>` from Secret Manager. A deployment-wide
  HMAC token is rejected rather than reused across tenants.
- Cloud Build `c4b4bee9-7f77-401f-9d1d-68214acd8ab3` completed `SUCCESS`; image
  digest `sha256:0baae28f9e1fdbb2322cf8ef7d69a6383b51f2a8fd67aa18d2a1ac516e7362fb`;
  Cloud Run revision `driftline-00119-h78` serves 100% of traffic.
- Live proof: `/health` returned `ok`; the tenant-specific signer authorized
  an aggregate context read with all four connector scopes `status=ok` and
  `external_read=true`; a token signed with a deployment-wide key returned
  `401 Invalid signed approval`. The new revision has zero `ERROR` log entries.
- Secret Manager `driftline-tenant-operator-driftline-demo` is version 1,
  labeled `app=driftline`, `environment=production`,
  `hackathon=all-things-agentic`, `tenant=driftline-demo`,
  `kind=operator-signing`; only the Driftline runtime service account can
  access it. The similarly labeled `driftline-tenant-driftline-demo-operator`
  container was created during the first provisioning attempt and is retained
  as an unused, recoverable resource; it is not referenced by Cloud Run.
- The checked-in tenant provisioning helper now creates the signer container
  for every future tenant, without accepting a secret value. Local API tests:
  `46 passed`; Ruff and `git diff --check` are clean.

## 2026-08-20 Legacy signer purge release

- Source commits `a0a72be` and `fae4237` remove the historical
  `DRIFTLINE_APPROVAL_SIGNING_SECRET` binding from the active Cloud Run
  template. The old Secret Manager resource remains unmounted and is retained
  only for reviewed cleanup; no active request can use it.
- Cloud Build `5ceb5014-d150-41a6-be20-5936557e2033` completed `SUCCESS`; image
  digest `sha256:0dd778eec23912a83953fe31595dc99ad79844732bc31cee3d628bb18ecfca68`;
  Cloud Run revision `driftline-00121-nbs` serves 100% of traffic.
- Live checks after explicit public-invoker reconciliation: `/health` returned
  `ok`; the active template has zero legacy signer env bindings, retains only
  the tenant signer prefix/required flag, and the revision has zero
  `severity>=ERROR` log entries.
- Final tenant proof authorized all four aggregate connector reads and a
  Gemini 3.5 Flash / Google ADK direct agent run using only
  `inspect_source_change` and `get_workflow_state`; Firestore stored workflow
  `193e6223-3bb6-4d37-886a-d2c64d8a6a4a` with `tenant_id=driftline-demo` and
  `status=needs_approval`. Full local suite: `139 passed`; Ruff, frontend
  production build, and `git diff --check` are clean.

## 2026-08-20 Durable tenant directory release

- Source commits `83918ea` and `38b3946` make the durable Firestore tenant
  directory authoritative for break-glass tenant admission. The active
  tenant must exist with `status=active`; disabled or unreadable tenant
  records fail closed. The deployment-wide `DRIFTLINE_HMAC_TENANTS` variable
  is no longer present in the Cloud Run template.
- Cloud Build `846ebd0d-4d56-48cb-b53d-be9b2a550cb9` completed `SUCCESS`; image
  digest `sha256:4b3aba111078d120f398196dd3af3e91937f73b320c32bc01436ca92a16ceb8d`;
  Cloud Run revision `driftline-00123-2ph` serves 100% of traffic.
- Live checks after public-invoker reconciliation: `/health` returned `ok`;
  the template reported zero `DRIFTLINE_HMAC_TENANTS` bindings and one
  durable-directory flag; the revision produced zero `ERROR` log entries.
- With no deployment allowlist, the tenant-specific signer authorized all
  four aggregate connector reads (`status=ok`) and a Gemini 3.5 Flash /
  Google ADK run using only `inspect_source_change` and `get_workflow_state`.
  Firestore stored workflow `0cc63917-031a-41e7-a028-e6cd7c0d2318` with
  `tenant_id=driftline-demo` and `status=needs_approval`.
- Full local suite remains `140 passed`; Ruff, frontend production build, and
  `git diff --check` are clean.

## 2026-08-20 Durable-mode fail-closed correction

- Source commit `32b1b45` removes the implicit default-tenant admission when
  durable directory mode is enabled. In the hosted configuration, an HMAC
  signer now requires an active Firestore tenant record even when no legacy
  allowlist is configured; an unknown tenant is rejected with
  `tenant_not_allowlisted`.
- Cloud Build `7e597b8c-927f-4f4b-8735-03875e6e704b` completed `SUCCESS`; image
  digest `sha256:24d4033b51d517d88f0281e8a3f5a5ca16a69a7230c5c9bb7b2b55f9bf3b5f36`;
  Cloud Run revision `driftline-00124-m4x` serves 100% of traffic.
- Live checks: `/health` returned `ok`; `DRIFTLINE_HMAC_TENANTS` is absent,
  durable mode is enabled, the public invoker binding is present, and the
  revision has zero `ERROR` log entries. The existing active tenant still
  passed all four connector reads and a Gemini 3.5 Flash / Google ADK run;
  Firestore workflow `68cc3711-aef6-48c7-8c6b-53e8e802fbb9` is recorded under
  `tenant_id=driftline-demo` with `status=needs_approval`.
- Final local regression: `140 passed`; Ruff and `git diff --check` are clean.

## 2026-08-20 Platform tenant bootstrap release

- Source commit `e7d4f8c` adds the OIDC-only `POST /api/platform/tenants`
  control-plane route. It can create or reactivate tenant and owner-membership
  metadata, returns only deterministic Secret Manager references, and accepts
  no provider credential. The separate
  `DRIFTLINE_PLATFORM_OPERATOR_EMAILS` allowlist is configured for the signed-in
  platform operator; normal tenant operators remain a separate boundary.
- Cloud Build `3342b43b-5a22-41ed-be67-9a53ca058eea` completed `SUCCESS`; image
  digest `sha256:6d1b7c70be9aee82a3319e85c970913ef31e0b43b8aaf438b9167b4cd2226208`;
  Cloud Run revision `driftline-00125-zjw` serves 100% of traffic.
- Live checks after public-invoker reconciliation: `/health` returned `ok`;
  the platform route returned `401 Platform identity is required` without an
  identity; no HMAC allowlist env binding exists; the revision produced zero
  `ERROR` log entries.
- Existing tenant regression passed: all four signed connector context reads
  returned `status=ok`, and a Gemini 3.5 Flash / Google ADK run used only
  `inspect_source_change` and `get_workflow_state`. Firestore stored workflow
  `f9f44b48-2219-46d7-9e37-5bd5bfa91f0a` with `tenant_id=driftline-demo` and
  `status=needs_approval`.
- Full local suite: `142 passed`; Ruff, frontend production build, and
  `git diff --check` are clean. A real platform OIDC success has not been
  claimed because no browser identity token was used in this smoke window.

## 2026-08-20 Atomic tenant bootstrap release

- Source commit `e7d4f8c` now uses `provision_tenant_metadata`, an atomic
  tenant/membership transaction, rather than a read-then-write bootstrap.
  Concurrent platform requests have a single-winner contract; the local
  fallback uses a process lock.
- Cloud Build `dd1b9f65-77fc-48c7-a7a7-965adec403e1` completed `SUCCESS`; image
  digest `sha256:865a15ddfef33b70d8537dabca032aae56314138817b08262b9ae22f83878223`;
  Cloud Run revision `driftline-00126-ds5` serves 100% of traffic.
- Live checks after public-invoker reconciliation: `/health` returned `ok`;
  unauthenticated platform bootstrap returned `401 Platform identity is
  required`; the revision produced zero `ERROR` log entries.
- Existing tenant regression passed: all four signed connector context reads
  returned `status=ok`, and Gemini 3.5 Flash / Google ADK used only
  `inspect_source_change` and `get_workflow_state`. Firestore stored workflow
  `ed2a13e8-8c9a-4265-bced-5032be10d16e` with `tenant_id=driftline-demo` and
  `status=needs_approval`.
- The regression suite covers concurrent single-winner behavior and reports
  `143 passed`; Ruff, frontend production build, and `git diff --check` are
  clean.

## 2026-08-20 Unified tenant credential lifecycle release

- Source commit `aca16ea` unifies Salesforce refresh-token storage with the
  shared tenant connector namespace: `driftline-tenant-<tenant>-salesforce`.
  OAuth callback success now creates the metadata-only Salesforce binding and
  audit event; aggregate health requires the connection record and an active,
  exact-name binding. Disconnect revokes the binding and records an audit event
  without deleting the provider secret.
- Platform bootstrap now passes its initial audit event into the tenant
  transaction. Firestore commits tenant, owner membership, and audit metadata
  together; the in-memory fallback uses the same process lock. This removes the
  prior rare state where a tenant could exist without a bootstrap audit.
- Cloud Build `97c9d7ca-712b-49d8-b100-e86324ebf90c` completed `SUCCESS`;
  image digest `sha256:3ad6e1efd96201f28d08db0ae9b5d96acd36cc674fdfed1e93e71ca81b0369c7`;
  Cloud Run revision `driftline-00127-d4t` serves 100% of traffic.
- Live checks: active project remained `driftline-hackathon-2026`; `/health`
  returned Firestore-backed `ok`; public invoker is present; revision error
  logs are zero. The public ops summary still reports Salesforce honestly as
  `oauth_ready` / `awaiting_authorization` because no real Salesforce callback
  has been completed.
- Secret Manager `driftline-tenant-driftline-demo-salesforce` was created
  with Driftline labels and runtime-only accessor plus version-adder IAM. It
  has no credential version yet; the existing legacy `driftline-sf-driftline-demo`
  secret remains retained but is no longer the tenant naming path.
- Full backend suite: `145 passed`; Ruff, compileall, and `git diff --check`
  are clean. Salesforce remains unconnected until a real org consent callback
  and read probe succeed; no connected-org claim is made.

## 2026-08-20 OAuth lifecycle race hardening release

- Source commit `f021ae7` makes the Salesforce OAuth callback re-check the
  durable tenant record immediately before writing a refresh token or creating
  the connector binding. A flow that began before deprovisioning now fails
  closed with no Secret Manager write.
- Cloud Build `bf7b5723-2a3c-4726-83ea-a35094fe016c` completed `SUCCESS`;
  image digest `sha256:98d305a9ad94af626f3c1923c916a2431007f2b8beb97fa9d70546ad673872bb`;
  Cloud Run revision `driftline-00128-5jg` serves 100% of traffic.
- Live `/health` remained Firestore-backed `ok`; the signed Salesforce start
  path returned `authorization_required` with a 600-second PKCE state, while
  signed health correctly returned `409 Salesforce is not connected for this
  tenant`. No Salesforce consent or CRM data access is claimed.
- Post-deploy live ADK proof used the tenant signer and returned HTTP 200 with
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, source status
  `needs_approval`, and exactly `inspect_source_change` plus
  `get_workflow_state`; Firestore stored workflow
  `deaad302-bcb9-4dd0-8e11-250408291802` under `tenant_id=driftline-demo`.
- Regression suite: `146 passed`; Ruff and `git diff --check` are clean.

## 2026-08-20 Salesforce owner-gate release

- Source commit `7ac0f91` restricts Salesforce OAuth start to an active tenant
  owner, matching binding and disconnect permissions. Tenant operators can
  still run the aggregate read health probe but cannot initiate credential
  acquisition.
- Cloud Build `34baeb0f-6a54-4011-802b-fe80849b8331` completed `SUCCESS`;
  image digest `sha256:2640f25890e05d9846880dd416aeb3957ff5e4dfc2f2bfbe7e9b26500be48966`;
  Cloud Run revision `driftline-00129-mbl` serves 100% of traffic.
- Live checks: `/health` returned Firestore-backed `ok`; the owner-signed
  Salesforce start path returned `authorization_required` with PKCE and a
  600-second state; the revision has zero `severity>=ERROR` log entries and
  the public invoker binding remains present.
- Full backend suite: `147 passed`; Ruff, frontend production build, and
  `git diff --check` are clean.

## 2026-08-20 Firestore-authoritative tenant release

- Source commit `d5cfaa8` removes process-memory fallback when Firestore is
  enabled for tenants, memberships, connector bindings, connector profiles,
  and Salesforce connections. Hosted OAuth callbacks also refuse to resurrect
  local state when the durable state was consumed or deleted. An unavailable
  or missing durable record now fails closed instead of reviving stale tenant
  authority.
- Cloud Build `3140e288-7b19-414d-b3f2-0188011e1e23` completed `SUCCESS`;
  image digest `sha256:1e7d6f955d418b02f228d8ff3e0bae4fc95d2f2800e2ba47273e0a0fb9e156a2`;
  Cloud Run revision `driftline-00130-q5j` serves 100% of traffic.
- Live checks: `/health` returned Firestore-backed `ok`; the tenant signer
  authorized the aggregate context read with all four connector scopes
  returning `status=ok` and `external_read=true`; the revision has zero
  `severity>=ERROR` log entries and the public invoker binding remains
  present.
- Full backend suite: `148 passed`; Ruff, frontend production build, and
  `git diff --check` are clean.

## 2026-08-20 Monitor fail-closed release

- Source commit `482ee04` prevents scheduled monitor runs from converting a
  public-source outage, malformed body, or bot/challenge interstitial into a
  synthetic business change. Those runs return `source_fetch_failed`,
  `change_detected=false`, and zero confidence; synthetic replay remains only
  on the explicit judge/demo path.
- Cloud Build `38fb4c78-3f19-4fba-83ec-ac7b3448f8b5` completed `SUCCESS`;
  image digest `sha256:232f01db9a39fcad8228d945faba5dcdf21d193fe74ce4d9b2c9f19ed3248d62`;
  Cloud Run revision `driftline-00132-qvv` serves 100% of traffic.
- Live signed monitor probe completed on the deployed revision as
  `job-9cc20672ea42`: `status=complete`, `run_mode=monitor`, no workflow was
  created, and Gemini reported the allowlisted `public/pricing` snapshot as
  unchanged. `/health` returned Firestore-backed `ok`; revision error logs
  remain zero.
- Full backend suite: `150 passed`; Ruff, frontend production build, and
  `git diff --check` are clean.

## 2026-08-20 Tenant status fail-closed release

- Source commit `d425499` makes hosted tenant-status read failures fail closed
  during authorization instead of trusting a stale active snapshot. The
  regression suite also covers durable membership fallback rejection and
  status-read failure behavior.
- Cloud Build `d9eb3bfa-c754-453b-8c0f-8afda6aa6225` completed `SUCCESS`;
  image digest `sha256:fdcf45eeb468199f710d214bc4e8d7102c2a1fdb3408df8515416ae6222d6920`;
  Cloud Run revision `driftline-00131-5pb` serves 100% of traffic.
- Live checks: `/health` returned Firestore-backed `ok`; the tenant signer
  authorized all four aggregate connector reads (`status=ok`,
  `external_read=true`); a live Gemini 3.5 Flash / Google ADK run returned
  `needs_approval` with only `inspect_source_change` and `get_workflow_state`,
  and Firestore stored workflow `75757683-cded-4b77-ae56-6bb337d8c78a` under
  `tenant_id=driftline-demo`; revision error logs remain zero.
- Full backend suite: `149 passed`; Ruff, frontend production build, and
  `git diff --check` are clean.

## 2026-08-20 Tenant identity and read-isolation releases

- Source commits `b783a74` (tenant identity propagation through signed monitor
  jobs and workflows) and `5eb997a` (signed read authorization for tenant-bound
  jobs, workflows, packets, actions, and scenarios), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `1225e5a4-b3d5-4fb3-9717-27a28126d8ea` built the first change;
  Cloud Build `7cefae2e-b1c9-4033-b224-bf4059e33429` deployed the combined
  release successfully. Artifact Registry image digest:
  `sha256:31ed4cbef61839b47c3017180595eb52faf6734c1b563c8af82fc5862bfeefae`.
- Cloud Run revision `driftline-00098-5g2` is ready and serves 100% of traffic.
  `GET /health` returned Firestore persistence and async jobs; the newest
  revision `severity>=ERROR` query returned no entries.
- Live signed monitor probe created `job-fc0c4ff0d774` for
  `tenant_id=driftline-demo`; it completed with `model=gemini-3.5-flash`,
  `execution_mode=google_adk`, and no error. An unsigned read returned `403`,
  the public job list omitted the tenant-bound job, and a matching signed read
  returned it. The signed tenant metadata probe still returned four active
  connector bindings with `credential_values_exposed=false`; an unknown tenant
  returned `403 tenant_not_allowlisted`.
- The local regression suite is `117 passed`; Ruff and `git diff --check` are
  clean. The public demo remains tenantless synthetic data and continues to
  use the packet-only lane.

## 2026-08-20 Tenant summary-isolation release

- Source commit: `eb1374b` (public operator summaries and append-only change
  memory now exclude tenant-bound records unless the caller supplies a
  matching signed identity), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `c9c4860e-8dab-49b4-833e-54f3933d7866` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:06ebca7d16a969191f2701fd51a79f5833b9a46d739b465399582c494eb322d6`.
- Cloud Run revision `driftline-00099-xt2` is ready and serves 100% of traffic.
  `GET /health` returned Firestore persistence and async jobs; the newest
  revision error query returned no entries. Public memory contained zero
  `driftline-demo` tenant identifiers, while a signed memory query returned
  the tenant-scoped view.
- The public ops summary remains aggregate-only and tenant-filtered; the
  public demo continues to show only tenantless synthetic records.

## 2026-08-20 Per-tenant quota isolation release

- Source commit: `fde1e31` (signed agent and workflow-mutation rate limits now
  use independent tenant buckets; public demo and scheduler buckets remain
  separate), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `e08960c9-ef42-4e2e-a0ef-7b6bed270cee` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:07c25dc11f8e504d33845c9717cfeefa6750810199426b5a9a7d8744bad11267`.
- Cloud Run revision `driftline-00100-n6v` is ready and serves 100% of traffic.
  `GET /health` returned Firestore persistence and async jobs; the newest
  revision error query returned no entries. A signed monitor job completed
  with `tenant_id=driftline-demo`, `model=gemini-3.5-flash`, and
  `execution_mode=google_adk`; the public read returned `403` and the public
  job list omitted it.
- The local regression suite is `118 passed`; tenant bucket behavior is
  covered directly.

## 2026-08-20 Tenant action-lifecycle release

- Source commit: `5843a37` (claim, complete, fail, retry, and reverse action
  transitions now enforce the workflow's signed tenant identity), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `491cf520-aad7-4fa3-8691-99db69f02f89` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:bad0193ce6f969fa6c45b55e4fb31e28a71e87459c54ddedbd5ecce97e49cbfa`.
- Cloud Run revision `driftline-00101-vcd` is ready and serves 100% of traffic.
  `GET /health` returned Firestore persistence and async jobs; the newest
  revision error query returned no entries. A signed monitor job completed on
  this revision with `tenant_id=driftline-demo` and
  `model=gemini-3.5-flash`; its public read returned `403` and public history
  omitted the job.
- The complete local suite remains `118 passed`, including a regression that
  rejects a public action transition on a tenant-bound workflow.

## 2026-08-20 Tenant source-ledger release

- Source commit: `d1ab77c` (custom source definitions and append-only snapshot
  histories are tenant-scoped; signed monitor baselines for shared fixtures use
  tenant-namespaced storage keys), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `4d012d06-bc2c-4c75-8bc6-ee34d07e21e5` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:82975d4c4c84799ba88182061dc2154e1e4ea7e4d47c7d13266136aaaa46ad78`.
- Cloud Run revision `driftline-00103-6km` is ready and serves 100% of traffic.
  `GET /health` returned Firestore persistence and async jobs; the newest
  revision error query returned no entries. The public registry returned only
  five pinned fixtures. A signed monitor/history probe returned a tenant-scoped
  `public/pricing` observation; an unknown custom history path returned `404`.
- The local regression suite is `119 passed`; source tenant definitions and
  namespace behavior are covered directly.

## 2026-08-20 Tenant scheduler release

- Source commit: `5ec651b` (the bounded internal scheduler now enumerates
  tenant-owned source metadata and enqueues one tenant-bound monitor job per
  source, with tenant-specific quotas), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `56a443b6-c1cf-49c2-8b8f-eeed54092ce4` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:00563259c695caff5bf7440d6c689ba9dea2395e65224b23ae186ecff0c493f3`.
- Cloud Run revision `driftline-00104-t2r` is ready and serves 100% of traffic.
  `GET /health` returned Firestore persistence and async jobs; the newest
  revision error query returned no entries. A signed monitor/history probe
  returned two tenant-scoped `public/pricing` observations, while the public
  custom-source history path returned `404`.
- The local regression suite is `120 passed`, including scheduler propagation
  of a custom source's tenant ID.

## 2026-08-20 Signed source-registry release

- Source commit: `68c1cf0` (source registry and monitor-freshness reads now
  accept either the public fixture view or an explicitly signed tenant view),
  pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `025f29f4-5da0-4f95-8f0f-31186cd87461` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:05f4d48a1fa428f8a7471c7d335dea58ae78a97eabc953ff3150bcde87f7c3c1`.
- Cloud Run revision `driftline-00105-mb4` is ready and serves 100% of
  traffic. `GET /health` returned Firestore persistence and async jobs; the
  newest-revision error query returned zero entries.
- Live public `/api/sources` returned five pinned fixtures. A signed
  `driftline-demo` source-registry read returned five tenant-visible entries,
  and the signed freshness registry returned five bounded health records.
  An unauthenticated custom-source history path returned `404`.
- The local regression suite is `121 passed`; the new signed/public registry
  boundary is covered directly. This is a tenant-aware control-plane slice,
  not a claim of self-serve SaaS onboarding, billing, or a second live
  customer tenant.

## 2026-08-20 Connector binding lifecycle release

- Source commit: `020c4b0` (owner-only metadata revocation for tenant
  connector bindings; revoked bindings fail closed without deleting or
  returning the underlying secret), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `d0ad1895-0242-4500-aa00-ba4a731ca5b9` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:0d09e38861669850b78bf8f754c2f2c143db56d1d1173c4004bee8ceeb1cb56d`.
- Cloud Run revision `driftline-00106-fdw` is ready and serves 100% of
  traffic. `GET /health` returned Firestore persistence and async jobs; the
  newest-revision error query returned zero entries.
- Live public `/api/sources` returned five fixtures; unsigned binding revoke
  returned `401`; a signed tenant binding metadata read returned four
  bindings with `credential_values_exposed=false`. No live production
  connector binding was revoked during verification.
- The local regression suite is `122 passed`, including the revoked-binding
  fail-closed contract. Secret rotation remains an infrastructure operation:
  provision a replacement version in the deterministic Secret Manager secret,
  then re-run the signed owner binding verification route.

## 2026-08-20 Credential lifecycle audit release

- Source commit: `34947ea` (tenant-scoped append-only credential lifecycle
  events and signed metadata-only audit reads), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `0bca99a6-6d80-4f09-bccc-7df02d93453e` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:78f6b8ff6479793e108519a36fea9bcbd1e206312c7daee6df24ccb4796b5277`.
- Cloud Run revision `driftline-00107-zkh` is ready and serves 100% of
  traffic. `GET /health` returned Firestore persistence and async jobs; the
  newest-revision error query returned zero entries.
- Live signed owner re-verification of the existing Jira binding returned
  `active` with `credential_value_accepted=false`; the signed tenant audit
  read returned an append-only activation event with
  `credential_values_exposed=false`.
- The local regression suite is `122 passed`. Credential lifecycle events are
  control-plane metadata and do not use the 30-day content TTL.

## 2026-08-20 Tenant offboarding release

- Source commit: `7f5007e` (owner-confirmed soft tenant deprovisioning that
  disables memberships, revokes bindings, preserves audit metadata, and makes
  future HMAC/OIDC authorization fail closed), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `f54799d7-e20b-401f-a33b-78f019256bf0` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:e7ffd91a12d389b60d20cffe11f1bb28d5b895dcf751597d895d49e6afac64bc`.
- Cloud Run revision `driftline-00108-ts4` is ready and serves 100% of
  traffic. `GET /health` returned Firestore persistence and async jobs; the
  newest-revision error query returned zero entries.
- Live signed deprovision verification with a mismatched confirmation returned
  `422 tenant_confirmation_mismatch`; unsigned deprovision returned `401`.
  No production tenant was deprovisioned during verification.
- The local regression suite is `123 passed`, including disabled-tenant
  authorization failure.

## 2026-08-20 Durable tenant usage metering release

- Source commit: `9ae19d9` (durable tenant-period usage counters and signed
  tenant usage read), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `423618fe-0495-4129-a926-cd67aa88a819` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:8e0444f443a0e17cab4dfcc18d47d27e74b2843012e901c4e351745bcc1276f6`.
- Cloud Run revision `driftline-00109-lwj` is ready and serves 100% of
  traffic. `GET /health` returned Firestore persistence and async jobs; the
  newest-revision error query returned zero entries.
- A signed live monitor canary completed with `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and `tenant_id=driftline-demo`. The signed
  `GET /api/tenants/usage` read returned `agent_calls=1` for the current
  period with `metering.durable=true`, `billing_enabled=false`, and
  `credential_values_exposed=false`. This directly verifies a Firestore-backed
  aggregate write without exposing source content or credentials.
- The local regression suite is `125 passed`; Ruff and `git diff --check`
  passed. Durable counters are metering evidence, not customer ROI or a
  billing claim; distributed quota enforcement and self-serve plan management
  remain future SaaS work.

## 2026-08-20 Tenant-scoped connector target release

- Source commit: `2a1d709` (operator-owned per-tenant non-secret connector
  target profiles with deployment-default fallback), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `75ee8dac-17fb-438e-834c-47a36be612f2` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:128d12971fc1b7c99258bd023e4c0402aa61ebc215c1ffe3da3d412c3042f706`.
- Cloud Run revision `driftline-00110-6mq` is ready and serves 100% of
  traffic. `GET /health` returned Firestore persistence and async jobs;
  public `GET /api/sources` returned the five pinned fixtures; the
  newest-revision error query returned zero entries.
- A fresh signed tenant monitor canary completed with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and
  `tenant_id=driftline-demo`. Durable signed usage advanced to
  `agent_calls=2` for the current period. The live demo still uses its
  existing deployment-wide target defaults because no second tenant profile
  has been provisioned; this release makes the profile boundary available
  without claiming a second-customer verification.
- The local regression suite is `127 passed`; Ruff, frontend production
  build, and `git diff --check` passed.
- `scripts/provision_tenant_connector_secrets.sh` was exercised against the
  existing `driftline-demo` tenant. It was idempotent, touched only the four
  deterministic tenant secrets, and re-verified runtime-only Secret Manager
  access without accepting or printing credential values. The repeatable
  lifecycle is documented in `docs/TENANT_ONBOARDING.md`.

## 2026-08-20 Transactional tenant quota release

- Source commits: `b583ed1` (Firestore transactional tenant-window
  reservations) and `952ebaa` (fix the Firestore transaction iterator read),
  pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `abb25ce1-e4c2-4f6c-b2dc-3dc39b3a64cc` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:4e8c5b46588c39f9c7a22b19b7c2b216ba51842d2b21e1c7746501822af5302f`.
- The first live probe on revision `driftline-00111-jdq` correctly failed
  closed with HTTP 429 but exposed a Firestore SDK iterator bug; its error was
  fixed immediately and not treated as a passing deployment.
- Revision `driftline-00112-6zt` is ready and serves 100% of traffic.
  A fresh signed tenant monitor completed with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and
  `tenant_id=driftline-demo`; signed usage returned `agent_calls=3` and
  `metering.durable=true`. The ops summary reports
  `tenant_quota_enforcement=firestore_transaction`; the newest-revision
  error query returned zero entries.
- The local regression suite is `128 passed`; Ruff, frontend production
  build, and `git diff --check` passed. The public synthetic demo remains on
  its local rate guardrail; signed tenant work is transactionally reserved in
  Firestore.

## 2026-08-20 Durable tenant connector profile release

- Source commit: `31e3a02` (`Add durable tenant connector profiles`), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `31caf000-6124-444e-b902-f854bd1ae3bf` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:c1d4605081d4a9adfb2994ecf36184ab6818ba2d0f3e10cb0942f6f436b9cd8e`.
- Cloud Run revision `driftline-00113-2g7` serves 100% of traffic at the
  existing public alias with the existing scale-to-zero and max-one-instance
  limits. `/health` returned Firestore persistence and async jobs; the newest
  revision error query returned zero entries.
- Added owner-only `POST /api/connectors/{connector}/profile` and signed
  metadata reads. The profile validator allows only connector-specific target
  fields and rejects credentials, arbitrary paths, and unknown keys. Adapters
  prefer the durable Firestore profile and retain the deployment environment
  as an explicit compatibility fallback only when a tenant field is not yet
  provisioned.
- Four non-secret profiles were provisioned for the existing
  `driftline-demo` tenant (Jira `KAN`, Confluence `DRIFT`, Slack
  `C0BRGFUSADA`, GitHub `mikeyerke/driftline`). Firestore REST directly showed
  four documents in `driftline_tenant_connector_profiles`; no credential
  values were accepted or returned.
- Signed profile reads and the aggregate-only context probe succeeded for all
  four configured connectors. The signed ops summary reported
  `tenant_quota_enforcement=firestore_transaction`, durable memberships, and
  `credential_model.legacy_global_fallback=false`.
- The local regression suite is `131 passed`; Ruff, frontend production
  build, and `git diff --check` passed. The live `/api/agent/run` request was
  accepted and completed on the newest revision according to Cloud Run access
  logs; the client-side 120-second probe expired before the response body,
  which is disclosed as a latency observation rather than a green synchronous
  latency claim. The public UI uses the bounded asynchronous jobs lane.

## 2026-08-20 Hosted tenant-profile fail-closed release

- Source commits: `8603a10` (hosted target fallback disabled), `1c8ea1d`
  (context-contract copy), and `b6a9ba3` (live ADK source binding), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `937bfc45-f501-492e-b007-5efccbc9dd7e` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:2e13374abdb85c0cafb8a3a7a3e1f69088657ab6d54c269b7cc2e31d57d0b338`.
- Cloud Run revision `driftline-00116-hf4` serves 100% of traffic. The hosted
  environment explicitly reports
  `DRIFTLINE_ALLOW_DEPLOYMENT_CONNECTOR_TARGET_FALLBACK=false`; a signed
  tenant without a durable profile fails closed with
  `tenant_connector_profile_missing` instead of inheriting another target.
- The existing `driftline-demo` profile was completed with its fixed
  Confluence parent page `720897`; the signed aggregate-only context probe on
  this revision returned `status=ok` for Jira `KAN`, Confluence `DRIFT`, Slack
  `C0BRGFUSADA`, and GitHub `mikeyerke/driftline`, with no raw content.
- `/health` returned Firestore persistence and async jobs; the signed ops
  summary reported `tenant_quota_enforcement=firestore_transaction`,
  `legacy_global_fallback=false`, and `deployment_target_fallback=false`.
  The newest-revision error query returned zero entries.
- Final async smoke `job-1bf037d1fed3` / workflow
  `b3950de8-3961-431e-9f58-06e3c038c071` reached `needs_approval` with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and the allowlisted
  tools `inspect_source_change` and `get_workflow_state`. Public demo approve
  and undo returned all four connector statuses as `prepared_only` with
  `external_write=false`.
- A direct public `POST /api/agent/run` probe on this revision completed in
  31.56 seconds with `execution_mode=google_adk`, `model=gemini-3.5-flash`,
  `source_status=needs_approval`, workflow
  `1fe6e9d6-ebb9-45ac-b56e-3e26d66994d9`, and exactly the allowlisted tools
  `inspect_source_change` and `get_workflow_state`. The workflow document was
  confirmed in Firestore collection `driftline_workflows`; no external write
  occurred. The fix binds placeholder model references only to the workflow
  created in the same ADK turn and requires an explicit allowlisted `source_id`.
- A second direct public probe (`decision-copilot-audit`) also completed with
  live Gemini structured impact analysis and live Gemini decision copilot
  output (`option_count=2`); its workflow was
  `e4a32330-fa45-4080-9a6e-e118c5bb28e6`. The first probe's transient
  deterministic decision fallback is retained as an explicitly labelled demo
  reliability path, not presented as Gemini output.
- The local regression suite is `135 passed`; Ruff, frontend production
  build, and `git diff --check` passed. Salesforce remains
  `oauth_ready` / `awaiting_authorization`; no connected-org claim is made.

## 2026-08-20 Tenant-aware direct ADK release

- Source commit: `869ca30` (signed tenant-aware direct ADK execution), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `829d9758-609e-41e2-b832-89e06b848cac` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:34684c569ed262d299d5e4b62386d6edd63e3d2f0ba0ad036fe7ae0f5053f1e1`.
- Cloud Run revision `driftline-00117-lp7` serves 100% of traffic. `/health`
  returned Firestore persistence and async jobs.
- Public direct ADK probe `cad9bc28-9256-4c72-a367-e73a64d99523` completed
  with Gemini 3.5 Flash, `execution_mode=google_adk`, the two allowlisted tools,
  and Gemini structured decision output. Its Firestore workflow is explicitly
  tenantless, preserving the packet-only judge lane.
- Signed direct ADK probe `896c891f-5d35-4f01-b9eb-e73b01b8bcc7` completed
  through the HMAC tenant boundary with the same model/tool contract. Firestore
  REST confirmed `tenant_id=driftline-demo`, `status=needs_approval`, and
  `data_mode=public_source` in `driftline_workflows`; no external write occurred.
  Partial identity and unallowlisted-source requests are rejected before model
  execution by regression coverage.
- The latest-revision Cloud Logging query returned no entries at `ERROR` or
  above. The local suite is `137 passed`; Ruff, frontend production build, and
  `git diff --check` passed.
- Cloud Run's public invoker binding was independently reconciled in the
  isolated project after the build warning: `roles/run.invoker` contains
  `allUsers` and the dedicated scheduler identity; the public alias returns
  the verified health payload.
- All 12 Driftline Secret Manager resources now carry `app=driftline`,
  `environment`, and `hackathon=all-things-agentic` labels; tenant secrets
  additionally carry `tenant=driftline-demo` and their connector label. IAM
  inspection confirmed the four tenant connector secrets and approval secret
  grant `roles/secretmanager.secretAccessor` only to
  `driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com`.

Browser QA on the public alias found no horizontal overflow at the default
desktop viewport (`1280x720`) or a `390x844` mobile viewport; both exposed 22
focusable controls and the browser console contained zero warnings/errors.

## 2026-08-20 Membership status enforcement release

- Source commit: `7c5293b` (durable membership state overrides bootstrap
  mappings and disabled members fail closed), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `0ac576e4-200d-4238-b1e7-b559b13c59e8` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:b5eb1683a1e10d0ed17a5bd31d2df6eb99ded412c2f4cb88c9d94656fe8b7abd`.
- Cloud Run revision `driftline-00096-2st` is ready and serves 100% of traffic.
  Health returned Firestore persistence and async jobs; the newest-revision
  error query returned no entries. A signed tenant metadata probe returned four
  active bindings without credentials, and owner-route validation returned the
  expected `422 member_email_invalid` before any membership write.
- The local regression suite is `114 passed`; disabled durable memberships are
  explicitly covered as a fail-closed authorization case.

## 2026-08-20 Membership provisioning verification release

- Source commit: `6fa724c` (stable membership document IDs plus focused API
  coverage), pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `1a0a9bdd-1bae-4606-8694-c3a7feff2a05` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:6ce7f01ec0099ef67d5c6b7201a0591ac799bac11b180cba5f0e64391c4564fe`.
- Cloud Run revision `driftline-00095-k9t` is ready and serves 100% of traffic.
  Health returned Firestore persistence and async jobs; the newest-revision
  error query returned no entries. The complete local suite is `113 passed`.
- The owner membership route now returns a deterministic metadata-only
  `membership_id`, and the no-credential contract is covered by the API test.

## 2026-08-20 Tenant membership fail-closed release

- Source commit: `d057ef7` (reject unprovisioned OIDC tenant claims and add the
  owner-only durable membership provisioning route), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `6958fafb-18a5-4db6-afc7-4c23396f527f` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:a6f8f23a12d58c09407929d73f2931517d9fb59181bf17b8ca8718b479f15416`.
- Cloud Run revision `driftline-00094-zp5` is ready and serves 100% of traffic.
  Health returned Firestore persistence and async jobs; the newest-revision
  error query returned no entries. A signed live probe returned tenant metadata
  with four active bindings and `credential_values_exposed=false`; the same
  signed token against an unknown tenant returned `403 tenant_not_allowlisted`.
- OIDC identities now require an explicit environment or durable Firestore
  membership. Owners can provision/update role metadata through
  `POST /api/tenants/members`; the route accepts no credentials or tokens in
  the body and returns metadata only. This is a durable tenant-control-plane
  foundation, not a claim of self-serve billing, enterprise IdP provisioning,
  or a second-customer pilot.

## 2026-08-20 Mobile navigation release

- Source commit: `feb0975` (mobile navigation flex-shrink fix), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `e1741ee7-6723-46bc-a8b2-a848eeb3baae` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:790766ecbde83b0765c64159bef93137ada8a2bd928726089c60a0282c1adaa6`.
- Cloud Run revision `driftline-00093-knj` is ready and serves 100% of traffic.
  The public health check returned Firestore persistence and async jobs. A
  final browser smoke completed the live scan with `gemini-3.5-flash`, opened
  the evidence-bound approval gate, recorded approval, and reopened it through
  the reversible undo path. Desktop geometry was 1440px wide with no document
  overflow; at 390px the nav is intentionally horizontally scrollable
  (`overflow-x:auto`, `scrollWidth=758`, `clientWidth=358`) and no body
  overflow/clipping was observed. Browser console error/warning logs were
  empty during the smoke.

## 2026-08-20 Immutable output and monitoring-quality release

- Source commit: `b822198` (challenge/interstitial detection for operator
  sources), deployed on top of `6f89e20`'s durable tenant control plane.
- Cloud Build `514e0bb9-7873-4877-9f8a-63d6dd1f544b` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:fb319298c763a9119856178e015d55763890eeec24c54bdb895509aa94ee75d1`.
- Cloud Run revision `driftline-00092-8vh` is ready and serves 100% of traffic.
  Health, durable tenant metadata, bounded connector context, signed approval,
  signed undo, and the four external connector statuses all passed. Both
  Cloud Storage action artifacts and operational outputs returned persisted
  (idempotent reuse on the deterministic paths), and the newest-revision error
  query returned no entries.
- Artifact writes now use `if_generation_match=0` and read-only reuse on
  `PreconditionFailed`; the runtime keeps least-privilege object creator/viewer
  access and does not need object delete/update permissions. A regression test
  covers the create/reuse behavior.
- Operator-registered source fetches reject common Cloudflare/Akamai/captcha
  challenge pages as `source_challenge_page_detected`, recording no source
  change. The behavior is covered by a source-monitor regression test; it does
  not claim arbitrary-web coverage.

## 2026-08-20 Durable tenant control-plane release

- Source commit: `6f89e20` (durable tenant and membership metadata, tenant
  metadata routes, and binding lifecycle correction), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `a6d33f9d-c1cc-4900-81dc-67bc55fc15ed` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:37daa8cbd50984967d132a35ea94de8d742d957f206790d042f183941467da66`.
- Cloud Run revision `driftline-00091-n64` is ready and serves 100% of traffic.
  Health, signed context, tenant metadata, signed approval/undo, and the
  unallowlisted-tenant `403` probe all passed; the newest-revision error query
  returned no entries.
- Firestore now has explicit `driftline_tenants` and
  `driftline_tenant_memberships` control-plane collections, alongside
  `driftline_connector_bindings`. Tenant and membership metadata never receives
  the 30-day content TTL; it remains until explicit owner deprovisioning.
  The four connector bindings were reactivated after deployment to remove the
  old expiry field.
- Signed `/api/tenants` returns caller-tenant metadata and binding/member
  counts; owner-only `/api/tenants/members` returns role metadata only. No
  credential values or bearer tokens are returned. Durable memberships can
  authorize OIDC principals in addition to bootstrap environment mappings.

## 2026-08-20 Tenant allowlist hardening release

- Source commits: `cfffd23` (explicit HMAC tenant allowlist) and `2fe6cb5`
  (clean forbidden response for unknown tenants), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Builds `f4bc1bc0-f31f-4f7e-83c8-1f8d1e3b8191` and
  `389a1aa7-1f67-4e75-bf65-3c66bc3a26b2` both completed `SUCCESS`; the final
  image digest is
  `sha256:a50375f59bf1fed5e5c334e7e90481266132037695c8b5926b4f958d6a571179`.
- Cloud Run revision `driftline-00087-n7p` is ready and serves 100% of traffic.
  The public health check returned Firestore persistence and async jobs; the
  newest-revision `severity>=ERROR` query returned no entries.
- The HMAC break-glass lane now accepts only the explicit
  `DRIFTLINE_HMAC_TENANTS=driftline-demo` allowlist. An unknown tenant was
  directly tested and returned `403 tenant_not_allowlisted` rather than a
  server error. The configured tenant context still returned all four
  aggregate connector reads, and a signed approval/undo smoke completed and
  reversed all four external connector handoffs.

## 2026-08-20 Tenant-bound connector credential architecture release

- Source commits: `cbe936c` (tenant-bound connector resolution and fail-closed
  handoffs) and `83e4442` (operator posture and metadata-only binding routes),
  pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `915c17cf-feda-47da-b353-d4cda4068cb3` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:7e5ae3fe06527ea131ec475dac294822a74445f3f86746524a402798e82e0418`.
- Cloud Run revision `driftline-00085-nkq` is ready and serves the public
  service with the existing min-0/max-1 guardrails. `GET /health` returned
  Firestore persistence and async jobs; the newest-revision error query returned
  no `ERROR` entries.
- Four deterministic tenant secrets were provisioned for `driftline-demo`:
  `driftline-tenant-driftline-demo-jira`,
  `driftline-tenant-driftline-demo-confluence`,
  `driftline-tenant-driftline-demo-slack`, and
  `driftline-tenant-driftline-demo-github`. Each is labeled `app=driftline`,
  `environment=production`, `hackathon=all-things-agentic`,
  `tenant=driftline-demo`, and its connector name. The runtime service account
  has `roles/secretmanager.secretAccessor` on these exact secrets only.
- Deployment-wide connector token mounts were removed. The runtime sets
  `DRIFTLINE_ALLOW_LEGACY_GLOBAL_CONNECTOR_SECRETS=false`; connector calls
  require a validated tenant binding in the `driftline_connector_bindings`
  Firestore collection and resolve only the deterministic tenant secret name.
  Missing bindings, unknown connectors, arbitrary secret names, and credential
  values in API requests fail closed.
- Signed owner activation was live-verified through
  `POST /api/connectors/{connector}/binding` for all four connectors. The
  metadata-only `GET /api/connectors/bindings` response returned
  `credential_values_exposed=false`. A signed context probe returned aggregate
  reads for Jira `KAN`, Confluence `DRIFT`, Slack `C0BRGFUSADA`, and GitHub
  `mikeyerke/driftline` without source bodies.
- A signed live workflow on this revision completed with
  `tenant_id=driftline-demo`, `external_write=true`, and all four connector
  handoffs (`reused`); the same workflow was signed-undo reversed across all
  four connectors. Storage/operational packet writes reported their existing
  non-blocking `failed` status, while external connector writes and reversals
  succeeded. This is one verified tenant, not a claimed second-customer pilot.
- The prior deployment-wide secrets remain retained but unmounted so cleanup is
  recoverable; they are not used by the active revision. No credentials or
  values are stored in source, responses, or logs.

## 2026-08-20 Bounded internal-context and Change Card identity release

- Source commits: `cdb319d` (`Add bounded internal context connector lane`) and
  `6529eed` (show the stable Change Card identity in the console), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `e044b5ce-2088-4d90-9194-41896a17dfeb` — `SUCCESS`; Artifact
  Registry image digest
  `sha256:c1316e787d5340cdba4d7b11dc18805897e086008d0bd40d31b4c141a8f68166`.
- Cloud Run revision `driftline-00082-bv9` serves 100% of traffic in the
  isolated project, with the existing min-0/max-1 resource guardrails. The
  revision readiness condition is `True`; its error-log query returned no
  `ERROR` entries.
- `GET /health` returned Firestore persistence and async jobs. The newest
  revision async smoke `job-5e84b1ea695a` reached `needs_approval` with
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, and no error.
- Signed `POST /api/connectors/context/summary` directly returned successful,
  aggregate-only reads for the fixed scopes: Jira `17` open issues in `KAN`,
  Confluence `5` pages in `DRIFT`, Slack `20` recent messages in the isolated
  channel, and GitHub `10` open issues in `mikeyerke/driftline`. The response
  declared `persisted=false`, `redaction=aggregate_metadata_only`, and no raw
  text/body fields.
- Public demo approval/undo on the newest revision remained packet-only:
  connector statuses were `prepared_only` and `external_write=false` in both
  directions. Salesforce still reports `oauth_ready` / `awaiting_authorization`,
  not connected.

The final UI release was built by Cloud Build
`3380ff5f-8b5e-4af7-885f-8c5a42541a02` (`SUCCESS`) and is serving as revision
`driftline-00083-pst` with image digest
`sha256:620d07dc70f9a8b1c2204351b3d6e67e0aa1c55a52c59ec40badfc186b5e477d`.
`GET /health` returned `status=ok`; newest-revision async smoke
`job-33b0b62edbe0` reached `needs_approval` with `model=gemini-3.5-flash`,
`execution_mode=google_adk`, and no error. The public deterministic demo
returned stable Change Card `card-51b2caa0b18994ae6413`; connector writes were
not invoked by that public path.
- A final signed context probe on `driftline-00083-pst` returned `status=ok`
  for all four configured scopes (Jira `KAN`, Confluence `DRIFT`, Slack
  `C0BRGFUSADA`, GitHub `mikeyerke/driftline`) with
  `redaction=aggregate_metadata_only`; the newest-revision error query returned
  zero `ERROR` log entries.

## 2026-08-20 Tenant credential namespace release

- Source commit: `2adbaeb` (canonical per-tenant credential namespace,
  namespace validation, metadata-only migration, and tenant-scoped lease
  evidence), pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `1f9eea3a-8c91-4d86-8f03-e496b49fa297` completed `SUCCESS` in the
  isolated `driftline-hackathon-2026` project. Artifact Registry image digest:
  `sha256:ffbe02d786b743c48dc2d696942dde359521d4d90a3faf43909777e1e34e0c6b`.
- Cloud Run revision `driftline-00150-n8m` serves 100% of traffic at the
  existing public alias with min 0, max 1, 1 CPU, 512 MiB, and concurrency 20.
  `/health` returned `status=ok`, `persistence=firestore`, and
  `async_jobs=true`; the public ADK smoke returned HTTP 200 with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and a persisted
  workflow. The revision error query returned zero `ERROR` entries.
- Cloud Run reports `DRIFTLINE_REQUIRE_TENANT_CREDENTIAL_NAMESPACE=true` and
  `strict_namespace_required=true` in `/api/ops/summary`. Four active
  `driftline-demo` bindings (Jira, Confluence, Slack, GitHub) were migrated
  through the Firestore API into
  `driftline_tenants/driftline-demo/credentials/{connector}` with schema
  version `1`, exact project Secret Manager resources, and the derived tenant
  service identity. The legacy flat records remain a rolling-migration mirror.
  No Secret Manager value was read or changed by the migration.

## 2026-08-20 Source-content guardrail release

- Source commit: `f8313d5` (deterministic untrusted-source guardrails across
  ADK tool output, structured text analysis, decision copilot, and Gemini
  vision prompts), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `d0e5bbbd-35f1-4ce3-ac1b-4efe1bfe6266` completed `SUCCESS` in
  `driftline-hackathon-2026`. Artifact Registry image digest:
  `sha256:1130748d28ec1c347ad4536f8d3b1f29ed4f369ca0324ad3b5c47b2cf5dcdd2e`.
- Cloud Run revision `driftline-00151-c7d` serves 100% of traffic. `/health`
  returned `status=ok`, strict namespace enforcement remained enabled, the
  public ADK smoke returned HTTP 200 with `model=gemini-3.5-flash`,
  `execution_mode=google_adk`, `needs_approval`, and a persisted Firestore
  workflow, and the revision error query returned zero `ERROR` entries.
- Firestore inspection confirmed the persisted workflow retained the raw
  evidence text and hash without guardrail markers. The guardrail applies only
  to model-visible copies, so audit/UI evidence integrity is preserved.

## Current deployment pointers

The authoritative live pointers for the latest deployed release are Cloud Run
revision `driftline-00020-w65` from source commit `eb66e30` and Artifact
Registry image digest
`sha256:cf005756c7d7dbe593fd974e0881c3f2b4464d7050698bb2a3b643197e38fd9e`.
This release adds the signed, tenant-filtered pilot outcome report at
`GET /api/ops/pilot-report`; an unsigned public request returned HTTP 401.
The historical resource table below is retained as the broader inventory; the
release sections above record each subsequent deployment and its direct proof.

## 2026-08-20 Agent trace state refresh

- Source commit `eb66e30` keeps the frontend Agent Trace synchronized with
  approval, reopen, and dismissal outcomes instead of retaining the prior
  approval-gate summary. The change was deployed by Cloud Build
  `18b0c587-6636-4540-9fec-498a975acb13` as revision `driftline-00020-w65`.
- A fresh anonymous direct-agent canary against the new revision returned
  HTTP 200 with `execution_mode=google_adk`, model `gemini-3.5-flash`, and
  exactly the allowlisted tools `inspect_source_change` and
  `get_workflow_state`; the attempted caller query and user ID were returned
  as `null`.
- Browser verification on the new revision reached the live workflow,
  Firestore-backed approval gate, packet creation, and the corrected trace
  summary `Action plan recorded · sandbox packet created`.

## 2026-08-20 Live connector context verification

- A signed owner read through the public Cloud Run revision returned HTTP 200
  for Jira, Confluence, Slack, and GitHub using the isolated tenant bindings;
  the request used the tenant's break-glass signer in memory and did not expose
  any credential value.
- The response was aggregate-only and request-scoped: Jira `project:KAN`
  returned 18 sampled open issues, Confluence `space:DRIFT` returned 5 pages,
  Slack `channel:C0BRGFUSADA` returned 27 recent messages, and GitHub
  `repository:mikeyerke/driftline` returned 0 open issues and 3 open pull
  requests. No source text or message bodies were persisted or returned.
- This proves live runtime reads and tenant/secret isolation for the four
  configured connectors. It does not prove Salesforce authorization; the
  Salesforce lane remains `oauth_ready` / `awaiting_authorization` and is
  read-only when enabled.

## Resources

| Resource | Name / scope | Verified status | Labels / notes |
| --- | --- | --- | --- |
| Google Cloud project | `driftline-hackathon-2026` (`724959673622`) | Active, created 2026-08-18 | `app=driftline`, `environment=hackathon`, `hackathon=all-things-agentic` |
| Billing account | `billingAccounts/01B9B8-321AE7-ECA02B` | Free trial linked and billing enabled | Trial credit `$300`, start 2026-08-18, end 2026-11-17; paid-account activation was not enabled |
| Billing budget | `77e23b49-d3b8-45de-91b7-f0c6172dfd9b` | Active `$10 USD` monthly guardrail filtered to project 724959673622 | Current-spend thresholds 10%, 25%, 50%, 75%, 90%, 100%; default billing-account recipients enabled; no custom notification channel created; reapply with `scripts/update_budget_guardrail.sh` |
| Cloud Run service | `driftline` in `us-central1` | Ready, latest revision `driftline-00020-w65` from commit `eb66e30` | Public URL: https://driftline-xvxczqg62a-uc.a.run.app/; min 0, service and revision max 1, 1 CPU, 512 MiB, concurrency 20; agent trace now refreshes after approval/reopen/dismissal; signed tenant-filtered pilot report added; unsigned pilot report returned HTTP 401; tenant-bound sources/reads/writes/action-lifecycle/quotas require signed identity; connector credentials use canonical tenant credential paths, exact Secret Manager resources, namespace schema validation, operation scopes, pinned versions, short-lived leases, owner-only lifecycle, metadata-only lease audit, and impersonated per-tenant service identities; untrusted source content is guarded only in model-visible copies; shared runtime has no direct live-tenant secret grants; Salesforce OAuth refresh tokens use the same broker namespace; both legacy global connector credential and hosted deployment-target fallbacks disabled |
| Cloud Run runtime identity | `driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Project roles: `roles/aiplatform.user`, `roles/datastore.user`; `roles/iam.serviceAccountTokenCreator` only on derived tenant identities |
| Tenant data-plane identity | `driftline-driftline-de-7f8fce0@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created; `driftline-demo` tenant | Secret Manager accessor only on that tenant's connector and signer secrets; Salesforce version-adder only on its Salesforce secret |
| Cloud Tasks queue | `driftline-jobs` in `us-central1` | Active, max 1 concurrent dispatch, 0.2 dispatches/second | OIDC target is the Driftline Cloud Run URL; task worker verifies the dedicated runtime identity |
| Cloud Scheduler job | `driftline-monitor` in `us-central1` | Enabled, every 6 hours UTC | OIDC calls `/api/scheduler/tick` as the dedicated scheduler identity; monitor mode records historical snapshots and does not invent workflows on no-change |
| Cloud Scheduler identity | `driftline-scheduler@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Dedicated `roles/run.invoker` on Driftline Cloud Run only; no reuse of runtime or build identity |
| Cloud Build identity | `driftline-build@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Build, deploy, service-usage roles; can impersonate only the Driftline runtime identity |
| Artifact Registry | `driftline` Docker repo in `us-central1` | Active | Latest deployed image: `us-central1-docker.pkg.dev/driftline-hackathon-2026/driftline/driftline@sha256:cf005756c7d7dbe593fd974e0881c3f2b4464d7050698bb2a3b643197e38fd9e` |
| Firestore database | `(default)` Native in `us-central1` | Active, directly write/read verified | `driftline_jobs`, `driftline_job_failures`, `driftline_credential_access_events`, `driftline_workflows`, `audit_events`, tenant control-plane metadata, canonical `driftline_tenants/{tenant}/credentials/{connector}` bindings plus rolling `driftline_connector_bindings` mirror, `driftline_tenant_audit_events`, `driftline_tenant_usage`, `driftline_tenant_rate_limits`, `driftline_tenant_connector_profiles`, and bounded `driftline_source_failures`; tenant lifecycle, usage, rate-limit, profile, binding, and credential-access records are metadata-only; job-failure and credential-access markers carry the same 30-day expiry; TTL is `ACTIVE` for both job failures and credential access |
| Cloud Storage artifact bucket | `gs://driftline-artifacts-724959673622` in `us-central1` | Active, uniform access, public access prevention, object versioning enabled | Labels: `app=driftline`, `environment=production`, `hackathon=all-things-agentic`; runtime has object creator/viewer only; paths `actions/<workflow>/<action>/packet.md` and `rollback.json` |
| Cloud Build logs bucket | `gs://724959673622-us-central1-cloudbuild-logs` | Created by regional Cloud Build | Labels: `app=driftline`, `environment=build`, `hackathon=all-things-agentic` |
| Cloud Build source bucket | `gs://driftline-hackathon-2026_us-central1_cloudbuild` | Created by regional Cloud Build | Labels: `app=driftline`, `environment=build`, `hackathon=all-things-agentic` |
| Cloud Build compatibility bucket | `gs://driftline-hackathon-2026_cloudbuild` | Created by Cloud Build | Labels: `app=driftline`, `environment=build`, `hackathon=all-things-agentic` |
| GitHub repository | `https://github.com/mikeyerke/driftline` | Public, source matches deployed revision | Separate repository under existing user account; no organization created |
| Jira site / project | `https://mikeyerke.atlassian.net` / `KAN` (`Driftline`) | Free Team-managed software project; no billing added | Atlassian API gateway cloud ID `7ed26020-ee58-470a-8fbb-3340925348ce`; connector is restricted to this project |
| GitHub connector target | `mikeyerke/driftline` | Authenticated and directly verified | Dedicated `driftline-github-token` Secret Manager secret; connector created and reversed issue `#1`; repository scope is fixed in runtime config |
| Secret Manager | `driftline-jira-token` | Retained for recoverable cleanup; not mounted by the active revision | Historical deployment-wide secret; active connector calls use `driftline-tenant-driftline-demo-jira` instead; no token value is stored in Git or docs |
| Secret Manager | `driftline-github-token` | Retained for recoverable cleanup; not mounted by the active revision | Historical deployment-wide secret; active connector calls use the tenant-bound binding; no token value is stored in Git or docs |
| Secret Manager | `driftline-slack-token` | Retained for recoverable cleanup; not mounted by the active revision | Historical deployment-wide secret; active connector calls use the tenant-bound binding; no token value is stored in Git or docs |
| Slack workspace / app | `Driftline` / `Driftline` app | Free plan; app installed and added only to `#new-channel` (`C0BRGFUSADA`) | Bot scopes: `channels:history`, `chat:write`; no paid plan or billing added |
| Confluence site / space | `https://mikeyerke.atlassian.net` / `DRIFT` (`Driftline`) | Free plan; dedicated space and gateway connector verified | Atlassian API gateway cloud ID `7ed26020-ee58-470a-8fbb-3340925348ce`; page writes are restricted to `DRIFT` |
| Secret Manager | `driftline-confluence-token` | Retained for recoverable cleanup; not mounted by the active revision | Historical deployment-wide secret; active connector calls use `driftline-tenant-driftline-demo-confluence`; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-jira` | Active, version 1 verified; tenant binding active | Labels: `app=driftline`, `environment=production`, `hackathon=all-things-agentic`, `tenant=driftline-demo`, `connector=jira`; accessor is the derived tenant identity only; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-confluence` | Active, version 1 verified; tenant binding active | Same isolated labels with `connector=confluence`; accessor is the derived tenant identity only; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-slack` | Active, version 1 verified; tenant binding active | Same isolated labels with `connector=slack`; accessor is the derived tenant identity only; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-github` | Active, version 1 verified; tenant binding active | Same isolated labels with `connector=github`; accessor is the derived tenant identity only; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-salesforce` | Active container, no credential version; reserved for tenant OAuth refresh token | Labels: `app=driftline`, `environment=production`, `hackathon=all-things-agentic`, `tenant=driftline-demo`, `connector=salesforce`; derived tenant identity has accessor and version-adder on this exact secret; no Salesforce consent has completed |
| Secret Manager | `driftline-tenant-operator-driftline-demo` | Active, version 1 verified; tenant-specific break-glass signer | Labels: `app=driftline`, `environment=production`, `hackathon=all-things-agentic`, `tenant=driftline-demo`, `kind=operator-signing`; accessor is the derived tenant identity only; not exposed through Cloud Run environment variables or API responses |
| Secret Manager | `driftline-tenant-driftline-demo-operator` | Active, version 1; unused recoverable provisioning artifact | Same Driftline/tenant/operator labels; not referenced by the deployed prefix and safe to delete later after review |

Cloud Build ID `51c869d8-e134-4664-8120-3ed1004001ea` completed successfully
in `global` and deployed revision `driftline-00049-q48` from runtime commit
`d016372`. It includes the Jira gateway environment, the
`driftline-jira-token:latest` Secret Manager binding, and an explicit
service/revision max-instance cap of one from the checked-in
`cloudbuild.yaml`. Historical image digest:
`sha256:1cf154d40da540d68319404e4e10ba57d5bc271f58328b9d578d0a5348dd0b17`.
Cloud Build and Cloud Run may enable Google-managed dependency APIs in addition
to the six explicitly requested application APIs; no Driftline code uses the
unrelated managed services. No existing project, bucket, database, service
account, API key, repository, or environment variable is reused.

## 2026-08-20 Evidence-integrity dismissal hardening release

- Source commit: `bf37f25` (dismissal now verifies the source evidence hash
  before recording a no-op), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `5fc1f638-610b-4a49-812e-87045223e3df` — `SUCCESS`; Artifact
  Registry image digest `sha256:658ac05936f6db4117bbd70b59550a198dc033c1f5db93ad7759325904c499b8`.
- Cloud Run revision `driftline-00081-8sv` serves 100% of traffic in the
  isolated project. Live `/health` returned Firestore persistence plus async
  jobs; a live dismissal returned `status=dismissed`, stable card
  `card-51b2caa0b18994ae6413`, closure `dismissed`, and zero action items. The
  revision error-log query returned no `ERROR` entries.
- Newest-revision async ADK smoke `job-4fae77ae92b9` reached
  `needs_approval` with `gemini-3.5-flash`, `execution_mode=google_adk`, exactly
  `inspect_source_change` and `get_workflow_state`, and no error.

## 2026-08-20 Stable Change Card idempotency release

- Source commit: `dc2a138` (deterministic Change Card/action identity and
  evidence-bound artifact paths), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `7f14cfe6-313e-4094-bd76-282b42563c86` — `SUCCESS`; Artifact
  Registry image digest `sha256:dd68363ec0f764960185e5d363a17d6b6db378ec6b74c7301039768b3c98aaf2`.
- Cloud Run revision `driftline-00080-d2v` serves 100% of traffic in the
  isolated project. `/health` returned Firestore persistence plus async jobs,
  and the revision error-log query returned no `ERROR` entries.
- Live idempotency smoke created and approved two independent workflows for
  the same source snapshot. Both returned Change Card
  `card-51b2caa0b18994ae6413`, action `action-51b2caa0b18994ae6413`, and
  stable owner keys beginning `card-51b2caa0b18994ae6413:`.
- Live async ADK smoke `job-f4681f586805` reached `needs_approval` with
  `gemini-3.5-flash`, `execution_mode=google_adk`, exactly
  `inspect_source_change` and `get_workflow_state`, and no error.

## 2026-08-20 Dismissed-state console polish release

- Source commit: `d61433a` (explicit dismissed-state timeline and connector
  copy), pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `9e0ca731-b2cc-4098-a7a0-957c489d5649` — `SUCCESS`; Artifact
  Registry image digest `sha256:8f183621023b0979f3b2b4086498346fd81488a927314ab825639d800d232271`.
- Cloud Run revision `driftline-00079-gdd` serves 100% of traffic in the
  isolated project. The public root served the new `index-BvcT1rW9.js` asset,
  `/health` returned Firestore persistence plus async jobs, and a live
  dismissal again returned `status=dismissed` with zero action items. The
  revision error-log query returned no `ERROR` entries.

## 2026-08-20 Auditable signal dismissal release

- Source commit: `9572770` (auditable non-material dismissal path), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `54ddd952-4ba1-40be-8c76-1c2172fdc225` — `SUCCESS`; Artifact
  Registry image digest `sha256:d082dabad54cbd5d707c5665e1f2265c2dca0684a4846f6c432634278fdca4ce`.
- Cloud Run revision `driftline-00078-mlg` serves 100% of traffic in the
  isolated project with the existing scale-to-zero, one-instance limits. The
  active gcloud project was verified as `driftline-hackathon-2026` immediately
  before deployment.
- Live public smoke created workflow `fc4a0227-e7c6-4507-b4e5-b92d5fcc6eeb`
  through `https://driftline-xvxczqg62a-uc.a.run.app`, dismissed it with the
  required reason `Not material for the current segment`, and verified
  `status=dismissed`, Change Card closure `dismissed`, zero action items, and
  `cards_dismissed=2` in `/api/ops/value-proof`.
- Live async ADK smoke job `job-b0a6012d25cd` reached `needs_approval` on this
  revision with `model=gemini-3.5-flash`, `execution_mode=google_adk`, exactly
  `inspect_source_change` and `get_workflow_state`, structured Gemini analysis,
  and no error. The revision error-log query returned no `ERROR` entries.

## 2026-08-20 Change Card, deadlines, and connector hardening release

- Source commit: `c2e7d14` (risk-based owner deadlines and overdue work
  signals on top of `ec1ce91`), pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `3018b0ed-733d-487e-92a3-a1da4ab270f4` — `SUCCESS`; Artifact
  Registry image digest `sha256:90074ab8a6e574ae622f5d29f6d3c14083b59de8208cfca772590307e1c19cea`.
- Cloud Run revision `driftline-00077-tvl` serves 100% of traffic at the public
  alias with scale-to-zero, one-instance cap, 512 MiB, concurrency 20, and
  300-second timeout. The active gcloud project was verified as
  `driftline-hackathon-2026` immediately before deployment.
- The deterministic Change Card now carries hash-bound evidence, materiality
  score/severity, decision window, source confidence, explicit contradiction
  review state, internal-exposure disclosure, role-specific packets, and
  append-only owner-action closure. Approved actions also carry high/medium/low
  priority and deterministic 48/96/168-hour due dates; overdue owner work is
  exposed in the card and value-proof endpoint. Synthetic runs explicitly show “not CRM
  data” and unavailable opportunity/renewal counts.
- Final live smoke workflow on revision `driftline-00077-tvl` reached the
  approval gate, approved into four owner action items with `external_write=false`,
  then undid back to `needs_approval` with all four action items marked
  `reversed`. `/api/ops/value-proof` observed the new card and named owners.
- Final asynchronous ADK job `job-28d666396a15` reached `needs_approval` on
  `driftline-00077-tvl` with
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, exactly
  `inspect_source_change` and `get_workflow_state`, and no error. Its response
  named the four affected work surfaces and stopped for human approval.
- `/health` returned Firestore persistence and async jobs enabled. The revision
  error-log query returned no `ERROR` entries after deployment. A historical
  connector failure caused by a newline in a copied token was hardened by
  trimming environment and Secret Manager values before HTTP use; no secret
  value is recorded here.

## Current connector release evidence

Cloud Build `c222b0de-9feb-4fa2-a9d7-906c99bff117` completed successfully from
commit `8267a32` and deployed revision `driftline-00061-lnj`. The active
project was verified as `driftline-hackathon-2026` before the build. This
release also corrected the scheduler OIDC audience to the exact public service
hostname.

- A signed `driftline-monitor` run fanned out five bounded monitor jobs. Jobs
  `job-f6d17dd46bd3`, `job-e5b2b8d9236a`, `job-1f4395e94328`,
  `job-dda8827a5706`, and `job-7a6a7f416178` each completed with
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, and
  `inspect_source_change`; Firestore now reports one or more public-source
  observations for all five registry entries and `/api/monitor/registry`
  reports `healthy=5`, `stale=0`, and `synthetic_only=0`.
- Release workflow `8b93182e-97ad-49f8-85f0-d1680e44277e` reached the human
  approval gate through the live async path, then approval created Jira `KAN-13`,
  reused Confluence page `524289`, posted Slack message
  `1787174535.367529`, and created GitHub issue `#6`. Undo returned the workflow
  to `needs_approval`, reversed the four connector markers, and wrote the
  private packet/rollback objects. Direct API checks found Jira label
  `driftline-reversed`, Confluence page version `4` with the named-human
  reversal note, the Slack reversal message, and GitHub issue `#6` open with
  `driftline-reversed`.
- `GET /api/ops/summary` returned project `driftline-hackathon-2026`, Firestore
  persistence, five-source guardrails, and all four isolated connectors enabled.
  Browser QA at 1280px loaded the new freshness panel with zero console errors;
  the existing 390px responsive gate remains documented below.

The research and product decision memo is tracked at
`docs/PM_OPERATIONAL_UTILITY_RESEARCH.md`; it records 20+ cited sources,
recurring PMM pain patterns, the competitive wedge, explicit non-goals, and the
ranked architecture backlog.

Cloud Build `cd9a8ce5-d4ee-42a8-bfca-44e3bbe6a330` completed successfully from
commit `16c53ba` and deployed Cloud Run revision `driftline-00059-jvr`. The
active project was verified as `driftline-hackathon-2026` before the build.

- Workflow `d1c90381-a2a4-489e-89c7-dfd565289389` reached `needs_approval`, was
  approved by the named human `Mike Yerke`, and created Confluence page `524289`
  in space `DRIFT` (`confluence_status=created`, `external_write=true`), Slack
  message `1787172434.198249` in channel `C0BRGFUSADA`, Jira `KAN-11`, and
  GitHub issue `#4`.
- Undo by `Mike Yerke` returned the workflow to `needs_approval`, persisted the
  rollback object, returned `confluence_status=reversed` and
  `slack_status=reversed`, and left the external records intact.
- Direct Confluence REST v2 inspection returned page `524289`, version `2`, and
  a body containing the named-human reversal note. Direct Slack API history
  returned both the original action marker and the reversal message.
- The earlier probe on revision `driftline-00057-fbt` correctly failed closed
  with `401 Unauthorized; scope does not match` when it attempted the legacy
  v1 route. That failure led to the v2-only gateway fix; no failed write was
  claimed as successful.
- The final idempotency/aggregate audit run reused Confluence page `524289`,
  reported `external_write=true` and `external_systems_changed=true`, then
  created and reversed new marker-scoped Slack/Jira/GitHub records. The final
  workflow state is again `needs_approval` with the external records retained.

## Verified live evidence

The current public release was built from runtime commit `0a0cd57` and is
exercised on revision `driftline-00040-jr6`:

- `GET /health` returned `{"status":"ok","service":"driftline-agent","persistence":"firestore","async_jobs":true}`.
- On the current revision, live job `job-f19289d4021b` reached
  `needs_approval` with `model=gemini-3.5-flash`, `execution_mode=google_adk`,
  and only `inspect_source_change` plus `get_workflow_state`. Approval created
  action `action-114761b1bb8d`, four durable owner items, a private packet, and
  Jira issue `KAN-4` (`jira_status=created`, `external_write=true`). The first
  owner item was claimed and completed by the named human actor. Undo returned
  the workflow to `needs_approval`, kept `KAN-4`, and recorded
  `jira_status=reversed` plus a versioned rollback marker.
- Two public deterministic competitor demos created workflows
  `42ef1bf4-f1bf-4808-8d8d-2c6bef87efdd` and
  `48969538-53b9-4994-aafc-c04e440e67de`; both reached `await_approval`, were
  approved, and were undone. Each approval action persisted in Firestore with
  `jira_status=not_configured` and `external_write=false`; each undo persisted
  a separate rollback marker and returned the workflow to `needs_approval`.
  This proves the new connector boundary is observable and does not pretend to
  have performed an external write.
- A logged-out browser run completed the async scan at desktop width and at a
  true 390px device viewport; both had `bodyScrollWidth === innerWidth` and no
  horizontal overflow.
- The prior public-pricing verification (on the immediately preceding
  code-equivalent release) reached `needs_approval` and created workflow
  `b3fea38e-2f47-4cfb-af4c-b95ca518becf`.
  The persisted job recorded `model=gemini-3.5-flash`,
  `execution_mode=google_adk`, and only the allowlisted tools
  `inspect_source_change` and `get_workflow_state`; the source mode was
  `public_source` with a pinned snapshot URL and hash. The trace recorded
  `analysis.mode=gemini_structured`, a model summary/rationale, the matching
  evidence hash, and four artifacts. Approval created Firestore action record
  `action-e9d4c4d90442` (`active`), wrote a versioned packet object, and undo
  changed that same record to `reversed` while writing a rollback marker. The
  first action item was claimed and completed by the named human demo actor;
  its idempotency key and evidence hash remained attached through the lifecycle.
- That browser flow covered source-evidence modal, artifact selection, the
  deterministic human approval gate, per-artifact outcomes (`packet_ready`,
  `owner_review`, and `queued`), the evidence-bound sandbox packet, activity
  audit, and reopen/undo. The packet explicitly recorded that no external
  system was changed.
- Direct Firestore REST inspection for that run found the matching job document, workflow
  document, and eight-document `audit_events` subcollection. Approval
  synchronized the job to `complete`; reopening synchronized it back to
  `needs_approval`.
- A signed Cloud Scheduler run previously created monitor job `job-9668cbe22717`, which
  completed `baseline_established` with no workflow or approval invented. The
  Firestore snapshot ledger contains one `public/pricing` baseline document.
- A signed Scheduler run previously created monitor job
  `job-acc5973e452d`, completed `unchanged`, and created no workflow.
- A controlled ledger replay previously created monitor job `job-2813b664a871`, which
  detected `changed` with the exact before/after sentences and
  `confidence=0.99`, then reached the same deterministic approval gate. Its
  explicit structured-analysis fallback was safe and labelled; the final
  judge-facing demo run above is the verified `gemini_structured` path.
- The source registry now exposes a second realistic public source type,
  `public/terms`, with its own pinned fixture and independent snapshot key;
  the console shows both bounded monitors without exposing arbitrary URL input.
- The release also exposes three bounded competitor change types:
  `competitor/pricing`, `competitor/offerings`, and `competitor/blog`. A live
  logged-out run of `competitor/pricing` completed through the Google ADK path
  with `gemini-3.5-flash`, rendered a source-to-offering-to-business-impact
  graph, prepared target-specific Confluence/Jira/Slack handoff manifests, and
  paused on the deterministic competitive-response approval gate. The run
  created four competitor artifacts (Comparison map, Pricing battlecard, Deal
  desk guidance, and Executive weekly brief); the first action was claimed and
  completed by the named Demo operator. No external system write was claimed.
- The live competitor run on the current revision used job
  `job-3af8cbf0d1c2`, workflow `a2877c66-7de7-4341-b511-c67b702d3ae4`, and
  reached `needs_approval` with `model=gemini-3.5-flash`,
  `execution_mode=google_adk`, and only `inspect_source_change` and
  `get_workflow_state`. The persisted evidence hash was
  `3b2df1ed8f635d1cc7ab425f675df0baa9bac941aaeddbfbca81ecada501d957` and
  the structured analysis reported four artifacts. Approval created action
  `action-2fa6eea0d92f` and a real isolated Google Cloud operational output at
  `gs://driftline-artifacts-724959673622/operational-outputs/a2877c66-7de7-4341-b511-c67b702d3ae4/action-2fa6eea0d92f/approved.md`.
- Undo on that same live workflow wrote the reversal marker
  `gs://driftline-artifacts-724959673622/operational-outputs/a2877c66-7de7-4341-b511-c67b702d3ae4/action-2fa6eea0d92f/reversed.json` and left the original approved object intact.
- A signed Scheduler run on the current revision created monitor job
  `job-19b95cca8363`, completed `unchanged`, and the append-only history API
  returned its Firestore observation at
  `/api/sources/public/pricing/history`. A second signed run,
  `job-19e3895ac2f7`, also completed `unchanged`; the history endpoint now
  returns two distinct immutable observations for the same source hash.
- The artifact bucket is isolated from Cloud Build buckets and has no public
  IAM members. A successful approval writes a packet object; undo writes a
  separate rollback marker so the original object remains versioned evidence.
- The deployed Jira adapter is enabled only in the isolated Driftline runtime
  and is scoped to the free `KAN` / `Driftline` project. It uses a Jira-scoped
  Atlassian token through the required `api.atlassian.com/ex/jira/<cloudId>`
  gateway, performs marker-based idempotent create/reuse, and reverses by
  appending a comment plus `driftline-reversed` label rather than deleting
  customer work. The live approval smoke test on revision
  `driftline-00036-vnm` created `KAN-1` with
  `jira_status=created` and `external_write=true`; the live undo returned
  `jira_status=reversed`, left the issue intact, changed labels to
  `driftline-reversed`, and appended one reversal comment. The token value is
  not present in the repository, browser frontend, or documentation.
  The reproducibility deploy then repeated the complete round trip on
  `driftline-00038-tbj`: workflow
  `26ef9a10-22df-4e39-be0f-13a7ffd04d76` created `KAN-3` and undo returned
  `jira_status=reversed` with `external_write=true`.
- Historical release notes: the first post-deploy live run exposed and fixed an
  ADK mode incompatibility;
  one subsequent enqueue returned a transient queue-not-found while the
  service was warming. The final run succeeded; treat Cloud Run error logs as
  a release gate before submission.

The final capability release (revision `driftline-00049-q48`) directly verified
the new seams: `/api/memory/summary` returned append-only source/workflow
aggregates; the live visual registry returned a pair evidence hash and the
Gemini vision endpoint returned `mode=gemini_vision`, model
`gemini-3.5-flash`, `material_change=true`, and the matching hash; a live ADK
run reached `needs_approval` with a two-option Gemini decision brief and a
passing deterministic red-team review. A final approval/undo round trip created
and reversed Jira `KAN-6`; the GitHub connector then created and reversed
`mikeyerke/driftline#1` with `github_status=created`/`reversed`. The current
release also directly verifies Confluence page creation/reversal in `DRIFT` and
Slack message creation/reversal in the isolated `Driftline` workspace; each
status is persisted in the action record and is never inferred from a prepared
manifest.

The public live-agent endpoint is configured for at most 10 calls per hour and a
2,000-character query. Demo starts and approval/undo writes share a 30-mutation
hourly cap. These are spend guards, not production authentication.

## 2026-08-19 signed-write boundary release

- Source commit: `5c4f449` (`enforce signed connector writes and add value proof`).
- Cloud Build: `7a89863a-d149-4bb8-a09c-eb4a1f879a65` — `SUCCESS`.
- Artifact image digest: `sha256:e69e2b0f5ea635693bc6cf4b1d7c5b9c380bab5e86534177ffca8ec7c1dc78fe`.
- Cloud Run revision: `driftline-00063-fr9`; public alias remains
  `https://driftline-xvxczqg62a-uc.a.run.app`; `min=0`, `max=1`, `512MiB`,
  concurrency `20`, timeout `300s`.
- A dedicated `driftline-approval-signing-secret` was created in this project;
  version 2 is newline-free and is readable only by the isolated runtime
  service account. The value is never committed, logged, or returned.
- Public ADK workflow `job-b664393e9a28` / workflow
  `032a403d-4ea9-43da-909d-0b2453dea284` reached approval with
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, and tools
  `inspect_source_change`, `get_workflow_state`. Public approve and undo both
  returned `jira_status=prepared_only`, `confluence_status=prepared_only`,
  `slack_status=prepared_only`, `github_status=prepared_only`, and
  `external_write=false`.
- Signed operator smoke test workflow `7bfdac73-71e0-4431-9661-1c354c863356`
  used the secret-backed HMAC lane. Approval created isolated Jira `KAN-14`,
  Confluence page `720897`, Slack message `1787175918.332129`, and GitHub
  issue `mikeyerke/driftline#7`; signed undo returned all four statuses to
  `reversed`. No public actor was used for this write.
- `/health` returned `status=ok`, Firestore persistence, and async jobs enabled.
  `/api/ops/summary` reported project `driftline-hackathon-2026`, public demo
  packet-only, signed approvals enabled, and Salesforce `prepared_only`.
  `/api/ops/value-proof` reported observed records and explicitly listed hours
  saved, revenue lift, retention impact, and willingness-to-pay as unmeasured.
- Cloud Run error-log query for revision `driftline-00063-fr9` returned no
  `ERROR` entries after deployment and both approval-lane smoke tests.

## 2026-08-19 console copy release

- Source commit: `19cc28c` (`clarify public connector approval boundary`).
- Cloud Build: `0c90bf4a-3898-4d8c-8c17-6f6dcec7f128` — `SUCCESS`.
- Artifact image digest: `sha256:8cb778def6a9402924849e6a6c00822c363d0bf36f90826eb9fdd293c36571e3`.
- Cloud Run revision: `driftline-00064-m9k`, serving 100% of traffic at the
  existing public alias. The updated console now states that public packets
  are prepared-only and signed operator approval is required for writes.
- Latest ADK smoke `job-a866c705b0c7` / workflow
  `28d2f8fd-8c6f-4e8c-8cf3-bc25819173ff` reached approval with
  `gemini-3.5-flash`, `google_adk`, and the two allowlisted tools. Public
  approve/undo returned all four connector statuses as `prepared_only` with
  `external_write=false`.
- Latest signed connector smoke workflow
  `a193aecb-9c85-4824-b62b-806e27c26438` created Jira `KAN-15`, reused
  Confluence page `720897`, created Slack message `1787176373.596609`, and
  created GitHub issue `mikeyerke/driftline#8`; signed undo returned all four
  statuses to `reversed`.

## 2026-08-19 bounded monitoring and verified operator release

- Source commit: `f2cc09f` (bounded source onboarding, verified operator lane,
  and DNS-resolved source hardening), pushed to
  `https://github.com/mikeyerke/driftline`.
- Cloud Build `e2bef427-51b5-47d9-baa4-ab7b7de773ac` — `SUCCESS`; Artifact
  Registry image digest `sha256:7e45a251d154c93b3d7d281fef53295112b15ddb641a240114f07a6c93c1b658`.
- Cloud Run revision `driftline-00066-vhw` serves 100% of traffic at the
  existing public alias with `min=0`, `max=1`, `512MiB`, concurrency `20`, and
  timeout `300s`. The active project was verified as
  `driftline-hackathon-2026` before deployment.
- The source registry still reports five healthy pinned fixtures. The new
  signed `/api/operator/sources` path persists exact operator-registered HTTPS
  HTML/text URLs in the isolated Firestore registry, with an 8-second fetch,
  128KB body limit, redirect/query-credential/private-DNS-address rejection, and a
  25-source scheduler cap. No competitor URL was invented or registered in
  this release.
- The operator lane accepted a Google OIDC identity token for the allowlisted
  `mikeyerke@gmail.com` identity. Workflow
  `f30a4766-6293-4ea5-a11d-0e4ec886c8ce` created and reversed Jira `KAN-17`,
  reused the dedicated Confluence page `720897`, created and reversed Slack
  message `1787179614.144379` and GitHub issue `mikeyerke/driftline#10`; the
  audit record stored the verified subject and email, not the token. A separate
  public demo workflow
  `c24a90ed-8f47-44f9-912e-614ea1c079fe` returned all four connector statuses
  as `prepared_only` with `external_write=false`.
- The live `/api/agent/run` path completed on the final revision with
  `model=gemini-3.5-flash`, `execution_mode=google_adk`, and tools limited to
  `inspect_source_change` and `get_workflow_state` (workflow
  `73f8648c-3410-49fc-953d-becf26f2c2f1`). Firestore-backed
  `/api/ops/value-proof` observed 3 workflows, 8 source observations, 2
  approval-latency samples (p50/p90 0.50s), and 0% action-item completion in
  the final smoke window. These are deployment observations only;
  customer hours saved, revenue/win-rate lift, retention impact, and
  willingness-to-pay remain unmeasured.
- Salesforce remains `not_configured` / `prepared_only`; no Salesforce org,
  Connected App, OAuth consent, or token was available to verify, so no CRM
  authentication claim is made. The latest Cloud Run revision produced no
  `ERROR` log entries during the smoke checks.

## 2026-08-19 verified competitor sources and outcome-collection release

- Source commit: `8a41077` (`Add verified sources and outcome measurement lane`).
  Cloud Build `f6945a83-0384-4ef3-a73e-de3f080c760a` — `SUCCESS`; image digest
  `sha256:3d99ffdbeab6d194725d915880b5dd6e8f8d1b22a8b2a47be3e081e04f5f5bb1`;
  Cloud Run revision `driftline-00067-kfs` serves 100% of traffic.
- Three operator-registered public competitor sources were added through the
  Google OIDC lane and persisted in isolated Firestore:
  `custom/crayon-pricing` → `https://www.crayon.co/pricing-inquiry`,
  `custom/kompyte-intel` →
  `https://www.kompyte.com/blog/real-time-competitive-intelligence`, and
  `custom/visualping-monitoring` →
  `https://help.visualping.io/en/articles/4438913`.
- All three completed live Google ADK monitor jobs and established public
  baselines. The Crayon source was fetched twice afterward with the same
  append-only snapshot hash; registry health is now 8/8 healthy sources.
  These are public pages from the vendors' own domains, not synthetic fixtures
  or invented competitors.
- Manual monitor execution for registered sources now requires a signed or
  Google-verified operator identity; an unauthenticated request returned 401.
- Added signed `POST /api/ops/outcomes` and redacted `GET /api/ops/outcomes`.
  The live ledger currently contains zero records and truthfully reports hours
  saved, revenue/win-rate lift, retention impact, and willingness-to-pay as
  `not_measured`; no customer result was fabricated.
- Salesforce remains `not_configured` because there is still no Salesforce
  org, Connected App, OAuth consent, or token available in the isolated
  project. The read-only contract and readiness reporting remain in place.

## Cleanup and disablement

The following commands target only the Driftline project. Review the inventory
before running destructive commands and never paste credentials or tokens into
the repository:

```bash
PROJECT=driftline-hackathon-2026
REGION=us-central1

gcloud scheduler jobs delete driftline-monitor --project="$PROJECT" --location="$REGION"
gcloud iam service-accounts delete driftline-scheduler@$PROJECT.iam.gserviceaccount.com --project="$PROJECT"
gcloud run services delete driftline --project="$PROJECT" --region="$REGION"
gcloud tasks queues delete driftline-jobs --project="$PROJECT" --location="$REGION"
gcloud artifacts repositories delete driftline --project="$PROJECT" --location="$REGION"
gcloud storage buckets delete gs://724959673622-us-central1-cloudbuild-logs
gcloud storage buckets delete gs://driftline-hackathon-2026_us-central1_cloudbuild
gcloud storage buckets delete gs://driftline-hackathon-2026_cloudbuild
gcloud storage buckets delete gs://driftline-artifacts-724959673622
gcloud firestore databases delete --database='(default)' --project="$PROJECT"
gcloud projects delete "$PROJECT"
```

Project deletion is irreversible and should be the final reviewed action. The
free trial closes automatically on 2026-11-17 unless the full paid account is
activated; do not click the Cloud Console “Activate” upsell while the project
is no longer needed.
## Production hardening additions

- Salesforce OAuth scaffolding is deployed in code and remains unconnected
  until a real org completes consent and the callback. The callback is
  `https://driftline-xvxczqg62a-uc.a.run.app/api/connectors/salesforce/oauth/callback`.
- Isolated Secret Manager secrets `driftline-sf-client-id` and
  `driftline-sf-client-secret` contain the Salesforce External Client App
  credentials. The tenant refresh-token secret
  `driftline-sf-driftline-demo` exists but has no version until OAuth consent
  completes. No credential values are in source control, logs, or browser
  responses.
- Runtime service account can access and add versions only to the dedicated
  tenant Salesforce secret; it has no browser-visible credential path.
- Cloud Tasks `driftline-jobs` retry policy is bounded to three attempts with a
  five-second minimum and 60-second maximum backoff, one concurrent dispatch,
  and 0.2 dispatches per second.
- Job, workflow, source snapshot, source-failure, and outcome records carry a
  bounded `expires_at` retention field. Firestore TTL is `ACTIVE` for
  `driftline_jobs`, `driftline_workflows`, `driftline_source_snapshots`,
  `driftline_source_failures`, `driftline_outcome_measurements`, and
  `driftline_salesforce_oauth_states`; tenant control-plane metadata remains
  owner-retained until explicit deprovisioning.
- Signed operator requests now resolve a tenant and role from
  the durable Firestore membership directory; the public demo remains
  packet-only.

## 2026-08-20 value-proof display release (live)

- Source commit: `d24d22d` (`Format value proof latency for humans`), pushed to
  the public `main` branch after the frontend production build and CI run
  `32429786135` passed.
- Cloud Build `39c63067-6bda-45de-ab78-0f3d8c84b7fb` — `SUCCESS`; the build
  used the checked-in `driftline-build` service identity and produced the
  isolated Artifact Registry image for this commit.
- Cloud Run revision `driftline-00032-fwl` serves 100% of traffic at the
  existing public URL with `min=0`, `max=1`, `512Mi`, one CPU, 300-second
  timeout, and concurrency 20.
- Live checks after rollout: `/health` returned HTTP 200 with Firestore
  persistence and async jobs enabled; `/api/jobs/demo` returned a queued demo
  job; `/api/ops/value-proof` returned the explicitly labelled sandbox scope
  and `not_measured` customer outcomes. A direct `/api/agent/run` request
  completed with HTTP 200 in Cloud Run logs and exercised the live ADK path;
  the endpoint is intentionally not treated as a synchronous low-latency
  probe because Gemini execution may exceed a short client timeout.
- The value-proof latency card now renders bounded seconds (for example,
  `104.7s`) instead of an unformatted floating-point value. This is a display
  correction only; it does not change stored telemetry or imply customer ROI.

## 2026-08-20 final live verification on `driftline-00032-fwl`

- Chrome DevTools exercised the public `/api/agent/run` path twice after the
  rollout. The second direct response was HTTP 200 with `persisted=true`,
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and an agent trace
  containing exactly `inspect_source_change` and `get_workflow_state`; the
  trace recorded Gemini structured analysis and a human approval requirement.
- Desktop and mobile Lighthouse navigation audits each passed all 57 checks:
  accessibility 100, best practices 100, SEO 100, and agentic browsing 100.
  Chrome reported no console messages on the refreshed public console. The
  snapshot showed the corrected `104.7s` value-proof rendering, explicit
  synthetic/public-source labels, and the anonymous packet-only guardrail.
- A tenant-signed live connector binding-health probe returned HTTP 200 with
  four healthy, namespace-verified connectors (Jira, Confluence, Slack,
  GitHub), zero attention items, and Salesforce `not_configured`. The response
  confirmed `credential_values_exposed=false` and returned only profile keys,
  never secret values.
- A tenant-signed aggregate context probe returned HTTP 200 for Jira project
  `KAN` (18 open issues), Confluence space `DRIFT` (5 pages), Slack channel
  `C0BRGFUSADA` (27 recent messages), and GitHub repository
  `mikeyerke/driftline` (0 open issues and 0 open pull requests). Its contract
  remained `aggregate_metadata_only`, `persisted=false`, and no message or
  document bodies were returned.
- These are live deployment and connector-read checks, not customer-pilot
  outcomes. Salesforce still requires the owner to complete the open login and
  consent handoff; no Salesforce data claim is made. A real pilot still needs a
  participating team and before/after evidence before any ROI, time-saved,
  revenue, retention, or willingness-to-pay field can be populated.

## 2026-08-20 Salesforce PKCE and source-alignment release

- Source commit: `37cf155` (public privacy/terms pages) on top of `f6a6442`
  (Salesforce PKCE flow), pushed to `https://github.com/mikeyerke/driftline`.
- Cloud Build `f967f007-4a96-40a1-84f9-1c89519ed1eb` — `SUCCESS`; Artifact
  Registry image digest `sha256:8534d03fa25b91bf3df7e0eeb3aaac9e0df9feab8abb8b778c0cc5485501d2f2`.
- Cloud Run revision `driftline-00073-7jk` serves 100% of traffic at the
  existing public alias with scale-to-zero and the existing one-instance cap.
  `/health`, `/privacy.html`, and `/terms.html` were verified after rollout.
- Salesforce authorization now generates an S256 PKCE challenge and stores
  only the short-lived verifier in server-side OAuth state. The fresh start
  response was verified to include `code_challenge_method=S256`, contain no
  client secret, and expire in 10 minutes.
- The Salesforce client ID and secret are present only in the isolated project
  Secret Manager bindings. Salesforce consent/callback is intentionally still
  pending; no connected-org or CRM read claim is made until the operator
  completes the browser consent and the callback plus aggregate health probe
  succeed.

## 2026-08-21 metric-label clarity release (live)

- Source commit: `5bfc57c` (`Clarify change memory reversal metric`), pushed
  to `main` after GitHub Actions run `32430823596` completed successfully.
- Cloud Build `187446bb-3446-473c-ab80-a3b52cf1702f` — `SUCCESS`; active
  Cloud Run revision `driftline-00033-r8x` serves 100% of traffic in the
  isolated project.
- The Change Memory card now labels its count `reversed owner items`, matching
  the backend's action-item aggregation instead of implying it is a workflow
  count. A fresh isolated browser context rendered the new label.
- Final live UI checks on the new revision passed all 57 Lighthouse audits on
  desktop and mobile (100 accessibility, best practices, SEO, and agentic
  browsing) with no console messages.
- A fresh direct agent probe on the same revision returned HTTP 200 with
  `persisted=true`, `execution_mode=google_adk`, `model=gemini-3.5-flash`, and
  exactly `inspect_source_change` plus `get_workflow_state` in the trace.

## 2026-08-21 value-proof sample-context release (live)

- Source commit: `668e301` (`Expose value proof sample context`), pushed after
  CI run `32431496244` completed successfully.
- Cloud Build `c4ca5915-0210-4241-943d-8f91154a2fe9` — `SUCCESS`; Cloud Run
  revision `driftline-00034-8pf` serves 100% of traffic in the isolated
  project.
- The public Value Proof card now shows the approval-latency sample count and
  p90 alongside p50. A fresh browser context rendered `approval latency p50 ·
  n=6` and `Approval latency p90 128.3s`; the panel continues to label
  customer outcomes as unmeasured.

## 2026-08-21 final connector and workflow gate recheck (live)

- The active gcloud project was confirmed as `driftline-hackathon-2026`; Cloud
  Run service `driftline` revision `driftline-00034-8pf` serves 100% of traffic.
  `/health` returned HTTP 200 with `persistence=firestore` and
  `async_jobs=true`. Cloud Logging returned no `ERROR` entries for the active
  revision.
- A direct public `/api/agent/run` request returned HTTP 200 with
  `persisted=true`, `execution_mode=google_adk`, `model=gemini-3.5-flash`, and
  exactly the allowlisted tool calls `inspect_source_change` and
  `get_workflow_state`. The trace included Gemini structured analysis and a
  human approval requirement.
- A fresh demo workflow was approved as the named demo actor, persisted a
  Firestore-backed packet, then undone. Approval returned `complete` with
  `external_systems_changed=false`; undo returned `needs_approval`, marked the
  action `reversed`, and persisted a separate rollback marker. This is a
  packet-only demo proof, not a claim that an external customer system changed.
- A tenant-signed binding-health read returned four healthy,
  namespace-verified connectors (Jira, Confluence, Slack, GitHub), zero
  attention items, and Salesforce `not_configured`. The response confirmed
  `credential_values_exposed=false`.
- A tenant-signed aggregate context read returned HTTP 200 for Jira project
  `KAN` (18 open issues), Confluence space `DRIFT` (5 pages), Slack channel
  `C0BRGFUSADA` (27 recent messages), and GitHub `mikeyerke/driftline` (0 open
  issues, 0 open pull requests). The contract remained
  `aggregate_metadata_only`, `persisted=false`; no message, page, issue, or
  repository bodies were returned.
- Desktop and 390px mobile Lighthouse navigation audits each passed all 57
  checks (100 accessibility, best practices, SEO, and agentic browsing), and
  Chrome reported no console warnings or errors.
- The signed tenant pilot report still returned `status=not_measured` and
  `record_count=0`. `docs/PILOT_PACKET.md` and
  `scripts/record_pilot_measurement.sh` now provide a secret-safe, aggregate
  measurement path, but no customer result is claimed until a real team
  supplies dated before/after evidence. Salesforce likewise remains pending
  the browser login/consent handoff; no Salesforce data claim is made.

## 2026-08-21 truthfulness correction and final live gate recheck (current)

- Source commit `f73b067` (`Do not imply unverified CRM exposure`) was pushed
  after backend regression coverage was added for anonymous public-source
  runs. GitHub Actions `32433166812` completed successfully.
- Cloud Build `edfd813b-96ad-4c58-9edc-a940caa28430` completed `SUCCESS`; Cloud
  Run revision `driftline-00035-htz` serves 100% of traffic in the isolated
  `driftline-hackathon-2026` project. `/health` returned HTTP 200 with
  Firestore persistence and async jobs enabled. The active gcloud project was
  re-confirmed before the checks.
- A fresh public scan reached `needs_approval` with
  `execution_mode=google_adk` and `model=gemini-3.5-flash`. The rendered Change
  Card now says `CRM context unavailable` and `No CRM context was read in this
  run`; it does not claim permissioned business context for an anonymous run.
- A fresh signed tenant source-list read returned only the five pinned judge
  fixtures. Research references in the README are not registered live sources;
  no arbitrary competitor target is claimed.
- A direct anonymous `POST /api/agent/run` canary on the same public revision
  returned HTTP 200 with `persisted=true`, `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and a Firestore-backed workflow in
  `needs_approval`.
- A fresh public-source workflow was approved with the reviewed
  `grandfather-existing-contracts` copilot option. The action record reported
  `storage_status=persisted`, a private Cloud Storage packet URI, four
  evidence-bound artifacts, and `external_systems_changed=false`. Public
  connector statuses remained `prepared_only`.
- The same workflow was undone immediately. It returned to `needs_approval`,
  marked the action `reversed`, persisted separate rollback and operational
  reversal artifacts, and kept `external_write=false`.
- Desktop and 390px mobile Lighthouse navigation audits each passed all 57
  checks (100 accessibility, best practices, SEO, and agentic browsing).
  Chrome reported no console messages after the mobile navigation audit.
- A fresh tenant-signed binding-health read returned four healthy,
  namespace-verified connectors (Jira, Confluence, Slack, GitHub), zero
  attention items, and Salesforce `not_configured`; all credential values
  remained redacted. A fresh signed aggregate context read returned Jira `KAN`
  (18 open issues), Confluence `DRIFT` (5 pages), Slack `C0BRGFUSADA` (27 recent
  messages), and GitHub `mikeyerke/driftline` (0 open issues and 0 open pull
  requests), with `aggregate_metadata_only` and `persisted=false`.
- The signed pilot report still returns `status=not_measured` and
  `record_count=0`. The pilot packet and measurement helper are ready, but a
  real participating team must supply dated before/after observations before
  Driftline can claim customer time saved, revenue, retention, or willingness
  to pay. Salesforce remains pending the owner-controlled login/consent
  callback; no Salesforce data claim is made.

## 2026-08-21 Artifact Registry retention hardening (live)

- The isolated `driftline` Artifact Registry repository was measured at
  approximately 13.7 GB across 209 image versions. The active Cloud Run image
  digest was verified before changing retention controls.
- `infra/artifact-registry-cleanup-policy.json` now keeps the 10 most recent
  `driftline` package versions and deletes untagged or tagged versions older
  than 30 days. The policy was first applied with dry-run enabled, then
  re-applied with dry-run disabled after the policy shape and rollback window
  were verified. The initial policy application itself was non-destructive;
  the explicit cleanup below was performed afterward against exact digests.
- Repository labels remain `app=driftline`, `environment=production`, and
  `hackathon=all-things-agentic`. Cloud Run remains scale-to-zero with
  `maxScale=1`; this retention control is isolated to the Driftline project
  and does not affect any other repository or service.
- After the retention window was verified, 199 older exact digest versions
  (and their Cloud Build tags) were deleted, leaving exactly 10 rollback
  candidates. Artifact Registry reports the image-version count at 10; blob
  garbage collection is asynchronous, so the displayed repository byte count
  may lag the deletion.

## 2026-08-21 public lane clarity release (live)

- Source commit `0c5f327` (`Clarify public production lane`) passed the local
  backend gate (224 tests and Ruff) plus the frontend production build, then
  Cloud Build `bd48453f-e1fa-4ef7-9524-64c8785db413` completed `SUCCESS`.
- Cloud Run revision `driftline-00053-pck` serves 100% of traffic with image
  digest `sha256:221e06a64be1a99bf577d695d13f14b99f9bac51b1611979fcd1f55dccee23ae`.
  The active project remained `driftline-hackathon-2026`, and the dedicated
  runtime service account and production labels were unchanged.
- The public browser rendered `Public demo lane`, `Production · packet-safe`,
  and `Ready for review` after a fresh scan. The live scan reached the human
  approval gate with `google_adk`, `gemini-3.5-flash`, Firestore state, and the
  two allowlisted tools `inspect_source_change` and `get_workflow_state`.
  The 1280px browser layout had no horizontal overflow, browser diagnostics
  had no errors, `/health` returned HTTP 200, and current-revision Cloud
  Logging returned no `severity>=ERROR` entries.

## 2026-08-21 build-context hardening release (live)

- Source commit `d4ee7ef` (`Bound Docker build context`) passed all GitHub
  Actions gates: 224 backend tests with Ruff, frontend production build, and
  standalone production-image build. `.dockerignore` now excludes repository
  metadata, local environment files, virtual environments, dependency trees,
  generated output, caches, and archives from Docker build context.
- Cloud Build `38145a16-6eab-46e7-90b5-2b2d4b41d09f` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00054-zsp` at 100% traffic. The image
  digest is `sha256:a8ca49d3f1ac752fba32f4987b91beeb3793bf74ec9cf9940f7cfc6673e51513`.
  `/health` returned HTTP 200 and the active-revision log query returned no
  `severity>=ERROR` entries.
- The post-deploy repository inventory was reconciled after the two new
  images were added: the two oldest exact digests were deleted, leaving 10
  versions including the active image and rollback candidates. Automatic
  cleanup remains enabled for future builds.
- Final API smoke on revision `driftline-00054-zsp` created workflow
  `de3f6c7f-4a59-4005-ad24-4968bf3a50c4`; it reached `needs_approval` with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and exactly
  `inspect_source_change` plus `get_workflow_state` in the trace. Signed
  public-demo approval persisted four evidence-bound packets with all
  connector writes `prepared_only` and `external_write=false`; immediate
  undo persisted the rollback marker and returned the workflow to
  `needs_approval`. Current-revision logs remained free of `ERROR` entries.

## 2026-08-21 anonymous boundary recheck (live)

- Public requests to tenant directory, membership, credential inventory,
  credential-access, connector bindings, job-failure, and pilot-report routes
  failed closed (401/403/422) without exposing tenant or credential data.
- Supplying `approval_token` or `identity_token` in query strings to public
  routes returned HTTP 400 with `Query authentication is disabled; use request
  headers.` The deployed request guard prevents secrets from being accepted
  through URLs or accidentally retained in browser history and access logs.

## 2026-08-21 OIDC-only hosted operator hardening (live)

- Source commit `6897d5c` (`Require Google identity for hosted operator lane`)
  passed 225 backend tests, Ruff, the frontend production build, and the
  repository diff check. GitHub Actions run `32446039737` completed `success`.
- Cloud Build `690dfea8-efe4-4840-b68f-54df2a1ccebb` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00055-lvp` at 100% traffic with image
  digest `sha256:4ac0dc7d345bad18f39c163d9e5d7ae8bad70ac8f3aef2f33755f7bdad40a88c`.
  The active project remained `driftline-hackathon-2026`; Cloud Run remains
  `minScale=0`, `maxScale=1`, 512 MiB, one CPU, 20 concurrency, and 300-second
  timeout.
- The deployed environment now has `DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY=true`.
  A direct signed-route probe without Google identity returned HTTP 401 with
  `Google operator identity is required for this deployment`; the query-string
  authentication probe remained HTTP 400. This closes the hosted HMAC
  break-glass path while preserving it for explicit local/bootstrap use.
- `/health` returned HTTP 200 and the current-revision Cloud Logging query had
  no `severity>=ERROR` entries. A fresh public scan reached `needs_approval`
  with `execution_mode=google_adk`, `model=gemini-3.5-flash`, and exactly the
  allowlisted tools `inspect_source_change` and `get_workflow_state`.
- The named demo approval persisted four Firestore-backed packets with
  `storage_status=persisted`, all connector statuses `prepared_only`, and
  `external_write=false`; immediate undo persisted the rollback marker and
  returned the workflow to `needs_approval`. No external provider write is
  claimed by this public smoke.

## 2026-08-21 tenant bootstrap repair and authenticated connector canary (live)

- Source commit `f937d60` (`Repair incomplete tenant bootstrap membership`)
  passed GitHub Actions run `32446842617` (`success`). Cloud Build
  `dbde9432-0fdc-437f-ae57-1ef4c1f09f16` completed `SUCCESS` and deployed
  `driftline-00056-d8c` at 100% traffic. The active image digest is
  `sha256:a8b93e677951e5c23ca91da3abdfafc554e8b185bfcfb8a294052f9c9e88a3d9`.
  The active project remained `driftline-hackathon-2026`; Cloud Run remains
  scale-to-zero with max one instance, 512 MiB, one CPU, 20 concurrency, and
  a 300-second timeout.
- `/health` returned HTTP 200 with Firestore persistence and async jobs; the
  current-revision Cloud Logging query returned no `severity>=ERROR` entries.
- With a short-lived Google OIDC identity, the isolated `driftline-demo`
  tenant was repaired from an existing tenant document with no membership to
  one owner membership. The signed tenant directory, aggregate context, and
  binding-health routes then returned only redacted metadata: Jira,
  Confluence, Slack, and GitHub healthy; Salesforce not configured.
- Authenticated `tenant_demo` job `job-6efbdab733c5` reached
  `needs_approval` with workflow `b6332414-3bc3-4eb4-b5fc-43041abe35d3`,
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and the allowlisted
  tools `inspect_source_change` plus `get_workflow_state`. Signed approval
  reactivated the idempotent Jira task `KAN-18` and the configured
  Confluence/Slack/GitHub markers. Signed undo reversed those Driftline-owned
  external markers, preserved the Jira issue, and persisted a rollback object
  and audit event. No credential value was returned or written to the repo.

## 2026-08-21 authenticated operator console release (live)

- Source commit `57da6d2` (`Add authenticated operator console lane`) passed
  GitHub Actions run `32447925481` (`success`), 227 backend tests, Ruff, the
  frontend production build, and `git diff --check`.
- Cloud Build `270b4d31-643f-4601-9e9a-527e5ab244c2` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00057-25v` at 100% traffic. The image
  digest is `sha256:13a95547bde16e4cec06b9f47c853d9eef14090bbefd7b7cdea51f4cae60dffb`.
  `/health` returned HTTP 200, and the current-revision log query returned no
  `severity>=ERROR` entries.
- `/api/auth/config` returns only the public Google web client id and explicitly
  labels the anonymous lane `packet_only`. The deployed UI rendered the Google
  sign-in control and operator-lane copy without exposing any credential.
- A fresh current-revision OIDC canary discovered the one active
  `driftline-demo` owner membership, reached `needs_approval` through Gemini
  3.5 Flash/ADK, and completed signed approval plus undo. Provider results were
  `reactivated` for Jira, Confluence, and Slack; GitHub correctly returned
  `blocked_closed` because its matching issue was already human-closed. Undo
  returned Jira, Confluence, Slack, and GitHub to `reversed`, retained the Jira
  issue, and persisted the rollback audit artifact. No credential values were
  returned.

## 2026-08-21 signed packet and scenario access hardening (live)

- Source commit `2801354` (`Complete authenticated operator packet flows`)
  passed GitHub Actions run `32448509896` (`success`), including the backend
  suite, Ruff, frontend production build, and standalone image build.
- Cloud Build `9b504b21-e8d0-46cb-a707-af83f92caad5` completed `SUCCESS` and
  deployed `driftline-00058-8jj` at 100% traffic. The active image digest is
  `sha256:1700dcd566b12eba440bdc8647c7304fc6f60735a43525695b8268f94fee0a35`.
  `/health` and `/api/auth/config` returned successfully.
- Tenant packet downloads now use an authenticated fetch with the OIDC bearer
  header rather than placing identity material in a URL. A current tenant
  packet returned HTTP 200 with 2,074 bytes; the same request without OIDC
  returned HTTP 401. Tenant scenario reads use the same header-bound path.
- The public browser still rendered the Google operator control and the
  packet-safe public lane after a fresh navigation. No credentials are stored
  in browser storage or exposed to the packet URL.

## 2026-08-21 registered-source onboarding proof (live)

- Source commit `a4f675a` (`Harden pinned source fetch compatibility`) passed
  GitHub Actions run `32449633360` (`success`), including 95 targeted source
  and API tests, Ruff, and the frontend production build. The pinned HTTPS
  adapter now consumes Python-version-specific `check_hostname` arguments
  without weakening SSL hostname verification.
- Cloud Build `dd23aeae-fec2-45e9-b383-9e956367e7d7` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00061-46f` at 100% traffic. The active
  image digest is
  `sha256:8cdd40105bd51c275e42f2af3cc1d99a9be92e22181c44b56c8f68351d4a2a14`.
  The active project remained `driftline-hackathon-2026`; Cloud Run remains
  scale-to-zero with max one instance, 512 MiB, one CPU, 20 concurrency, and a
  300-second timeout.
- `/health` returned HTTP 200 and `/api/auth/config` confirmed Google OIDC is
  enabled while the anonymous lane remains `packet_only`. The current
  revision had no new `severity>=ERROR` entries after deployment.
- A signed OIDC operator registered the exact public URL
  `https://raw.githubusercontent.com/mikeyerke/driftline/main/README.md` as
  `custom/driftline-readme` for tenant `driftline-demo`. The API returned HTTP
  200 with `status=registered`, `baseline.status=baseline_established`, and
  an append-only snapshot hash. A subsequent signed registry read returned six
  sources including the custom source; the monitor registry reported it as
  `healthy` with one observation. No competitor target was invented or
  registered.
- The first live attempt on revision `driftline-00059-8rr` exposed a real
  Python 3.12 adapter defect and returned HTTP 500; that error was not hidden.
  The compatibility fix was deployed and the same authenticated action then
  completed successfully on `driftline-00061-46f`. This is the production
  source-onboarding evidence; it is not a claim of arbitrary crawling.
- A fresh signed tenant workflow on `driftline-00061-46f` reached
  `needs_approval` with `execution_mode=google_adk`, `model=gemini-3.5-flash`,
  tenant `driftline-demo`, and exactly the allowlisted tools
  `inspect_source_change` and `get_workflow_state`. Selecting the cited
  `opt-grandfather-existing` copilot option returned HTTP 200 and persisted the
  workflow through the authenticated connector lane; the configured Jira,
  Confluence, and Slack adapters were idempotently reused/reactivated, while
  GitHub correctly remained `blocked_closed` for its human-closed matching
  issue. Signed undo returned HTTP 200, persisted `reversed` state for all four
  adapters, retained the Jira issue, and set `external_systems_changed=true`.
  These are isolated Driftline connector operations, not customer ROI or live
  competitor-monitoring claims.
- A post-canary Cloud Logging query for revision `driftline-00061-46f` after
  `2026-08-21T05:14:00Z` returned no `severity>=ERROR` entries.

## 2026-08-21 exact-source monitor binding hardening (live)

- Source commit `6244197` (`Bind monitor jobs to exact source IDs`) passed
  GitHub Actions run `32450568459` (`success`), the complete 230-test backend
  suite, Ruff, frontend production build, and standalone image build.
- Cloud Build `0eca42b4-8477-496b-9f27-580f947d9236` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00062-p6h` at 100% traffic. The image
  digest is
  `sha256:b7f88a16e5de610f44f87978c452ab51d160ec8d695fd06963eb6bd2056d7c3a`.
  The active project remained `driftline-hackathon-2026`; `/health` returned
  HTTP 200 and the service retained scale-to-zero/max-one guardrails.
- The exact existing Cloud Scheduler job `driftline-monitor` was invoked
  through Google Scheduler's own OIDC identity and returned HTTP 200. Its
  fan-out created the tenant-bound monitor job
  `job-23366d759170` for `custom/driftline-readme`; the job completed with
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, exactly one tool call
  (`inspect_source_change`), and no workflow because the source was unchanged.
  The monitor response explicitly named `custom/driftline-readme`, proving the
  model could not silently substitute another source.
- The signed monitor registry then reported the custom source `healthy` with
  four observations, latest data mode `operator_registered_public`, and the
  stable snapshot hash. This closes the source-selection gap between scheduler
  fan-out, ADK execution, and the append-only ledger.

## 2026-08-21 durable monitor source identity (live)

- Source commit `cfa77f0` (`Persist source IDs on monitor jobs`) passed GitHub
  Actions run `32451032570` (`success`) with the complete 230-test suite, Ruff,
  frontend production build, and standalone image build.
- Cloud Build `edc7669a-2766-4e8d-b608-70cd161bffb3` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00063-sz6` at 100% traffic. The image
  digest is
  `sha256:ebf6450c9b69be38c25be139adf2e2262aa8a7f93a81c529b63329a6361097fb`.
  `/health` returned HTTP 200 with Firestore persistence and async jobs.
- A new Cloud Scheduler invocation created monitor job `job-7d20de5a8866`.
  Its durable API record explicitly contains `source_id=custom/driftline-readme`,
  `run_mode=monitor`, `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and one `inspect_source_change` tool call. It
  completed unchanged with no workflow, while the signed monitor registry
  advanced the custom source to five observations and `healthy`. Earlier jobs
  created before this release are retained as historical records; new jobs no
  longer require source inference from free-text query fields.
- A post-run Cloud Logging query for the active revision returned no
  `severity>=ERROR` entries after the canary window.

## 2026-08-21 operator run-history source visibility (live)

- Source commit `eb54fe9` (`Surface source IDs in run history`) passed GitHub
  Actions run `32451382326` (`success`) with the locked frontend production
  build; the backend suite, Ruff, and standalone image build also remained
  green in the same workflow.
- Cloud Build `483392d9-2d3b-441e-b718-3461204eef2d` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00064-jdq` at 100% traffic. The image
  digest is
  `sha256:ebc6a775037068deab4de5c7550bf3adced2ec76dc7c2bf56ef1d063e3d64314`.
  The public `/health` and `/api/auth/config` probes returned successfully;
  Google OIDC remains enabled and the anonymous lane remains `packet_only`.
- The operator run-history UI now displays the durable source ID alongside
  each monitor/scan run, so source identity is visible without opening logs.

## 2026-08-21 request-auth log hardening (live)

- Source commit `795fd25` (`Keep operator tokens out of request URLs`) passed
  GitHub Actions run `32451977898` (`success`) with 231 backend tests, Ruff,
  frontend production build, and standalone image build.
- Cloud Build `1ab60ce7-1adb-4739-94fc-7211244bfdb3` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00065-rw4` at 100% traffic. The image
  digest is
  `sha256:652261c030b20dc80c3253e74fd31c056a0e23dc55e31cf9a925af7f3850df8e`.
  The active runtime explicitly sets `DRIFTLINE_REJECT_QUERY_AUTH=true` and
  `DRIFTLINE_REQUIRE_GOOGLE_OPERATOR_IDENTITY=true`.
- A live header-authenticated signed source read returned HTTP 200 and six
  sources, including `custom/driftline-readme`. A GET containing a fake query
  token returned HTTP 400 with the fail-closed guidance. A bounded Cloud
  Logging query for the new revision after the header-authenticated request
  found zero token-shaped URL fields (`identity_token`, `approval_token`,
  bearer/JWT patterns).
- Historical access logs from before this release may retain the earlier
  middleware-generated token URLs; those records are not retroactively
  rewritten. New requests no longer copy header credentials into the query
  string, and the middleware now resolves them through request-scoped memory.
- A fresh secured tenant scan on revision `driftline-00065-rw4` returned HTTP
  200, reached `needs_approval`, and persisted workflow
  `8548fc6c-35e8-4aa8-b908-19532b8d11e4` with `source_id=public/pricing`,
  `run_mode=tenant_demo`, `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, and exactly the two allowlisted tool calls
  `inspect_source_change` and `get_workflow_state`. No approval or connector
  write was invoked in this security canary.
- A post-canary error query for the active revision returned zero entries, and
  a token-pattern scan of the new revision's request logs returned zero
  matches.

## 2026-08-21 public packet safety naming (live)

- Source commit `a55b236` (`Name public packet safety tier for production`)
  passed the complete 231-test backend suite, Ruff, frontend production build,
  and diff checks before release. The public approval identity now emits the
  production-facing scope `public_packet_only`; the API still accepts the
  legacy `sandbox_packet_only` value for backwards compatibility with older
  local/persisted identities.
- Cloud Build `4cc832a0-6f76-43ef-9e48-655b07a39d35` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00066-75v` at 100% traffic. The image
  digest is
  `sha256:d71686e0822aad8150bba80bc3cc0f71fa5acf54813f2c4dbb0dd2856809af91`.
  The active project remained `driftline-hackathon-2026`.
- `/health` returned HTTP 200 with Firestore persistence and async jobs;
  `/api/auth/config` returned Google OIDC enabled with
  `anonymous_lane=packet_only` and `credential_values_exposed=false`.
  A query-token probe returned HTTP 400, confirming the deployed
  fail-closed request-auth boundary remains active.

## 2026-08-21 public ADK/Gemini judge-path canary (live)

- The anonymous public `POST /api/jobs/demo` path was exercised on revision
  `driftline-00066-75v` with the fixed `public/pricing` source. The returned
  job `job-f91d2df5eea1` completed at `needs_approval` with HTTP 200 polling,
  workflow `cec4fae3-b2d3-41da-9444-574fbe31994b`,
  `execution_mode=google_adk`, `model=gemini-3.5-flash`, and exactly the
  allowlisted tool calls `inspect_source_change` and `get_workflow_state`.
- The workflow persisted hash-bound source evidence, four downstream impacts,
  structured Gemini analysis, decision-copilot options, and the deterministic
  human approval gate. No external connector write was attempted. This proves
  the public judge path is a live ADK/Gemini product experience with
  packet-only safety, not a static front-end mock.

## 2026-08-21 partial-agent monitor recovery (live)

- Source commit `1e763fd` (`Preserve workflows after partial agent turns`) and
  follow-up commit `f17cc07` (`Recover workflows after monitor retries`) passed
  the complete 233-test suite, Ruff, frontend production build, and diff checks.
  The runtime now recovers a workflow ID from the ADK turn context and, if a
  transient model failure occurs after source inspection, attaches the newest
  exact-source workflow to the durable job instead of advancing the baseline
  and losing the approval work.
- Cloud Build `0208c362-95d8-44bc-b373-5e8b9b53bb86` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00068-48k` at 100% traffic. The image
  digest is
  `sha256:6b946e0bfe5bd99491935e49247b11d29c2d4b8998b56ae6957e1632c2f10c0b`.
- After a harmless README source update, Scheduler created monitor job
  `job-d8819695c976`. The job reached `needs_approval` with
  `workflow_id=232dcd43-1ce5-487f-a50c-f44cc70b4c81`,
  `source_id=custom/driftline-readme`, tenant `driftline-demo`,
  `model=gemini-3.5-flash`, and `execution_mode=google_adk`. Its durable
  response explicitly records that evidence was preserved after a bounded
  agent retry; the linked workflow is `needs_approval` with the new snapshot
  hash. No external connector write was attempted.

## 2026-08-21 rejected-query log hardening (live)

- Source commit `d1367f3` (`Strip rejected auth parameters from logs`) passed
  234 backend tests, Ruff, the frontend production build, and diff checks.
  Hosted GET requests that contain `approval_token` or `identity_token` are
  rejected and those parameters are removed from the mutable ASGI query scope
  before the access logger can record the request line.
- Cloud Build `bb993352-fe78-425b-b14f-14345801ec98` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00070-ckt` at 100% traffic. The image
  digest is
  `sha256:6a1da1d77f9a8c759283eca31d309cb44325e565d74066b0e89cb8c871fc5436`.
- `/health` and `/api/auth/config` returned successfully. A deployed fake
  query-token probe returned HTTP 400; subsequent Cloud Logging scans for the
  revision found zero `identity_token` query fields, zero request URLs
  containing that parameter, and zero `severity>=ERROR` entries.

## 2026-08-21 tenant approval fail-closed guard (live)

- Source commit `8cceefa` (`Fail closed when tenant copilot is unavailable`)
  passed 235 backend tests, Ruff, the frontend production build, and diff
  checks. Tenant workflows carrying a real ADK trace cannot be approved
  without a reviewed decision-copilot option; recovered workflows now persist
  an explicit unavailable marker, and the operator UI disables approval until
  a new scan produces a reviewed option. Legacy packet-only synthetic workflows
  remain compatible.
- Cloud Build `8f2b9e64-8c4c-4dca-8e03-0f6a1d12f243` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00071-rhd` at 100% traffic. The image
  digest is
  `sha256:79749d28a2e61ec3ad72782b18c1252d611da712eed44231b2fa29ae2f97a82f`.
- `/health`, `/api/auth/config`, and the public HTML title returned
  successfully; the latest-revision Cloud Logging scan contained zero
  `severity>=ERROR` entries.

## 2026-08-21 competitive-intelligence first-run release (live)

- Source commit `a093952` (`Lead with competitive intelligence workflow`)
  passed GitHub Actions run `32470332244` with the 241-test backend suite,
  Ruff, frontend production build, and standalone image build. Cloud Build
  `bd21d914-4a88-46df-8f52-e8e5a234d82d` completed `SUCCESS` and deployed
  Cloud Run revision `driftline-00094-n2l` at 100% traffic.
- The anonymous first-run console now opens on the strongest product wedge:
  an explicitly labelled competitor pricing fixture moving Competitor Pro
  from `$49` to `$59` per seat per month. The preview impact map, approval
  question, artifacts, and evidence all agree on the competitor scenario;
  own-product pricing and terms remain selectable alternatives.
- A live anonymous job `job-9e0fea5f4ccd` on the revision completed at
  `needs_approval` with `execution_mode=google_adk`,
  `model=gemini-3.5-flash`, exactly the two allowlisted tools
  `inspect_source_change` and `get_workflow_state`, and a Gemini structured
  analysis tied to the competitor evidence hash. It returned
  `competitor/pricing`, title `Competitor pricing moved`, and the four
  downstream surfaces `Comparison map`, `Pricing battlecard`, `Deal desk
  guidance`, and `Executive weekly brief`. This probe did not claim a customer
  system write or customer outcome.
- `scripts/verify_production.sh` passed on the same revision with Firestore
  persistence, async jobs, enabled Scheduler, running Tasks, active uptime
  monitoring, and zero recent Cloud Run errors. The public browser showed the
  coherent competitor first-run state after deployment.

## 2026-08-21 pre-scan truthfulness release (live)

- Source commit `2f7865d` (`Label pre-scan evidence as preview`) passed the
  local 241-test backend suite, Ruff, frontend production build, and diff
  checks. Cloud Build `c1ffee0f-3ebd-44b3-8ec1-8b2e82979c32` completed
  `SUCCESS` and deployed Cloud Run revision `driftline-00095-nph` at 100%
  traffic.
- Before a scan starts, the console now labels confidence as `Preview`, risk
  as `Scenario risk`, and the source panel as `Preview fixture · not captured`.
  After a live workflow exists, those labels return to verified evidence and
  the captured snapshot hash. This prevents the static judge fixture from
  being mistaken for a completed monitor run.
- A fresh production browser load showed the preview labels with no console
  errors; `/health` and `scripts/verify_production.sh` passed with zero recent
  Cloud Run errors.

## 2026-08-21 multimodal disclosure release (live)

- Source commit `510be63` (`Clarify multimodal reference evidence`) passed the
  local 241-test backend suite, Ruff, frontend production build, and diff
  checks. Cloud Build `49245582-02c4-4cf8-b9a3-97763eaf1a2a` completed
  `SUCCESS` and deployed Cloud Run revision `driftline-00096-shm` at 100%
  traffic.
- The visual panel now calls its bounded allowlisted concept asset a
  `Multimodal reference pair` and discloses that the selected source's text
  evidence and hash remain authoritative. The Gemini vision seam remains
  available without implying that the concept image is a screenshot of the
  selected competitor source.
- A fresh production browser load showed the disclosure and no console errors
  or warnings; `/health` and `scripts/verify_production.sh` passed with zero
  recent Cloud Run errors.

## 2026-08-21 structured-analysis recovery release (live)

- Source commit `c8966fa` (`Retry transient structured analysis shape errors`)
  passed 242 backend tests, Ruff, frontend production build, and diff checks.
  Cloud Build `8d62f466-d179-4a54-bfb9-0d90fbfa7c4c` completed `SUCCESS` and
  deployed Cloud Run revision `driftline-00097-rdn` at 100% traffic.
- The strict Gemini impact-analysis seam now retries a transient schema-shape
  failure with an explicit JSON string-type repair instruction, while still
  rejecting wrong evidence hashes, unknown artifacts, and policy violations.
  A regression test proves the first malformed `summary` response is retried
  and the repaired response remains evidence-bound.
- A fresh browser-driven default competitor scan completed with
  `gemini_structured` analysis, `gemini-3.5-flash`, exactly
  `inspect_source_change` and `get_workflow_state`, four evidence-bound
  artifacts, and no fallback or browser console errors. The workflow remained
  at the deterministic human approval gate.
- `/health` and `scripts/verify_production.sh` passed on the same revision with
  zero recent Cloud Run errors.

## 2026-08-21 billing guardrail hardening (live)

- The isolated billing budget `Driftline $10 Guardrail`
  (`77e23b49-d3b8-45de-91b7-f0c6172dfd9b`) remains filtered to only project
  `driftline-hackathon-2026` (`724959673622`) with a `$10 USD` monthly amount.
- The budget now alerts at 10%, 25%, 50%, 75%, 90%, and 100% of current spend.
  Notifications use the billing account's default recipients; no custom
  notification channel or cross-project filter was added.
- `scripts/update_budget_guardrail.sh` is idempotent, prints the resulting
  budget, and exits before making a change if the active gcloud project is not
  `driftline-hackathon-2026`. Re-running it directly verified the exact amount,
  project filter, and six fractional threshold values through gcloud.
- This control-plane change did not redeploy the app. Cloud Run remains on
  revision `driftline-00092-9cn` at 100% traffic, and the production
  verification script still passes with zero recent Cloud Run errors.
