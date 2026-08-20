# Driftline resource inventory

This inventory is intentionally scoped to the isolated Google Cloud project
`driftline-hackathon-2026`. The active gcloud configuration was checked during
the release run:

```text
core.account: mikeyerke@gmail.com
core.project: driftline-hackathon-2026
project number: 724959673622
```

Before any future mutation, verify the target explicitly:

```bash
gcloud config set project driftline-hackathon-2026
test "$(gcloud config get-value project 2>/dev/null)" = driftline-hackathon-2026
```

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

## Resources

| Resource | Name / scope | Verified status | Labels / notes |
| --- | --- | --- | --- |
| Google Cloud project | `driftline-hackathon-2026` (`724959673622`) | Active, created 2026-08-18 | `app=driftline`, `environment=hackathon`, `hackathon=all-things-agentic` |
| Billing account | `billingAccounts/01B9B8-321AE7-ECA02B` | Free trial linked and billing enabled | Trial credit `$300`, start 2026-08-18, end 2026-11-17; paid-account activation was not enabled |
| Billing budget | `77e23b49-d3b8-45de-91b7-f0c6172dfd9b` | Active `$10 USD` monthly guardrail filtered to project 724959673622 | Current-spend thresholds 25%, 50%, 75%, 90%, 100%; no custom notification channel created |
| Cloud Run service | `driftline` in `us-central1` | Ready, latest revision `driftline-00117-lp7` from commit `869ca30` | Public URL: https://driftline-xvxczqg62a-uc.a.run.app/; min 0, service and revision max 1, 1 CPU, 512 MiB, concurrency 20, tenant-bound sources/reads/writes/action-lifecycle/quotas require signed identity; connector credentials are tenant-bound through isolated Secret Manager bindings with owner-only revocation, append-only lifecycle audit, soft offboarding, durable usage metering, transactional tenant quota reservations, durable per-tenant target profiles, and both legacy global credential and hosted deployment-target fallbacks disabled |
| Cloud Run runtime identity | `driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Project roles: `roles/aiplatform.user`, `roles/datastore.user` |
| Cloud Tasks queue | `driftline-jobs` in `us-central1` | Active, max 1 concurrent dispatch, 0.2 dispatches/second | OIDC target is the Driftline Cloud Run URL; task worker verifies the dedicated runtime identity |
| Cloud Scheduler job | `driftline-monitor` in `us-central1` | Enabled, every 6 hours UTC | OIDC calls `/api/scheduler/tick` as the dedicated scheduler identity; monitor mode records historical snapshots and does not invent workflows on no-change |
| Cloud Scheduler identity | `driftline-scheduler@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Dedicated `roles/run.invoker` on Driftline Cloud Run only; no reuse of runtime or build identity |
| Cloud Build identity | `driftline-build@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Build, deploy, service-usage roles; can impersonate only the Driftline runtime identity |
| Artifact Registry | `driftline` Docker repo in `us-central1` | Active | Latest verified image: `us-central1-docker.pkg.dev/driftline-hackathon-2026/driftline/driftline@sha256:4e8c5b46588c39f9c7a22b19b7c2b216ba51842d2b21e1c7746501822af5302f` |
| Firestore database | `(default)` Native in `us-central1` | Active, directly write/read verified | `driftline_jobs`, `driftline_workflows`, `audit_events`, tenant control-plane metadata, `driftline_tenant_audit_events`, `driftline_tenant_usage`, `driftline_tenant_rate_limits`, and `driftline_tenant_connector_profiles`; tenant lifecycle, usage, rate-limit, profile, and binding records are metadata-only and have no content TTL |
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
| Secret Manager | `driftline-tenant-driftline-demo-jira` | Active, version 1 verified; tenant binding active | Labels: `app=driftline`, `environment=production`, `hackathon=all-things-agentic`, `tenant=driftline-demo`, `connector=jira`; accessor is the Driftline runtime service account only; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-confluence` | Active, version 1 verified; tenant binding active | Same isolated labels with `connector=confluence`; accessor is the Driftline runtime service account only; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-slack` | Active, version 1 verified; tenant binding active | Same isolated labels with `connector=slack`; accessor is the Driftline runtime service account only; no token value is stored in Git or docs |
| Secret Manager | `driftline-tenant-driftline-demo-github` | Active, version 1 verified; tenant binding active | Same isolated labels with `connector=github`; accessor is the Driftline runtime service account only; no token value is stored in Git or docs |

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
- Job, workflow, source snapshot, and outcome records now carry a bounded
  `expires_at` retention field. Firestore TTL operations were requested for the
  relevant collection groups; verify their state before calling retention
  cleanup complete.
- Signed operator requests now resolve a tenant and role from
  `DRIFTLINE_TENANT_MEMBERS`; the public demo remains packet-only.

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
