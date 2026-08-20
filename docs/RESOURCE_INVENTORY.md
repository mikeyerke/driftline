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
  `sawReopened=true`.
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

The authoritative live pointers for the latest release are Cloud Run revision
`driftline-00151-c7d` from source commit `f8313d5` and Artifact Registry image
digest
`sha256:1130748d28ec1c347ad4536f8d3b1f29ed4f369ca0324ad3b5c47b2cf5dcdd2e`.
The historical resource table below is retained as the broader inventory; the
release sections above record each subsequent deployment and its direct proof.

## Resources

| Resource | Name / scope | Verified status | Labels / notes |
| --- | --- | --- | --- |
| Google Cloud project | `driftline-hackathon-2026` (`724959673622`) | Active, created 2026-08-18 | `app=driftline`, `environment=hackathon`, `hackathon=all-things-agentic` |
| Billing account | `billingAccounts/01B9B8-321AE7-ECA02B` | Free trial linked and billing enabled | Trial credit `$300`, start 2026-08-18, end 2026-11-17; paid-account activation was not enabled |
| Billing budget | `77e23b49-d3b8-45de-91b7-f0c6172dfd9b` | Active `$10 USD` monthly guardrail filtered to project 724959673622 | Current-spend thresholds 25%, 50%, 75%, 90%, 100%; no custom notification channel created |
| Cloud Run service | `driftline` in `us-central1` | Ready, latest revision `driftline-00151-c7d` from commit `f8313d5` | Public URL: https://driftline-xvxczqg62a-uc.a.run.app/; min 0, service and revision max 1, 1 CPU, 512 MiB, concurrency 20; tenant-bound sources/reads/writes/action-lifecycle/quotas require signed identity; connector credentials use canonical tenant credential paths, exact Secret Manager resources, namespace schema validation, operation scopes, pinned versions, short-lived leases, owner-only lifecycle, metadata-only lease audit, and impersonated per-tenant service identities; untrusted source content is guarded only in model-visible copies; shared runtime has no direct live-tenant secret grants; Salesforce OAuth refresh tokens use the same broker namespace; both legacy global connector credential and hosted deployment-target fallbacks disabled | 
| Cloud Run runtime identity | `driftline-runtime@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Project roles: `roles/aiplatform.user`, `roles/datastore.user`; `roles/iam.serviceAccountTokenCreator` only on derived tenant identities |
| Tenant data-plane identity | `driftline-driftline-de-7f8fce0@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created; `driftline-demo` tenant | Secret Manager accessor only on that tenant's connector and signer secrets; Salesforce version-adder only on its Salesforce secret |
| Cloud Tasks queue | `driftline-jobs` in `us-central1` | Active, max 1 concurrent dispatch, 0.2 dispatches/second | OIDC target is the Driftline Cloud Run URL; task worker verifies the dedicated runtime identity |
| Cloud Scheduler job | `driftline-monitor` in `us-central1` | Enabled, every 6 hours UTC | OIDC calls `/api/scheduler/tick` as the dedicated scheduler identity; monitor mode records historical snapshots and does not invent workflows on no-change |
| Cloud Scheduler identity | `driftline-scheduler@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Dedicated `roles/run.invoker` on Driftline Cloud Run only; no reuse of runtime or build identity |
| Cloud Build identity | `driftline-build@driftline-hackathon-2026.iam.gserviceaccount.com` | Active, no key created | Build, deploy, service-usage roles; can impersonate only the Driftline runtime identity |
| Artifact Registry | `driftline` Docker repo in `us-central1` | Active | Latest verified image: `us-central1-docker.pkg.dev/driftline-hackathon-2026/driftline/driftline@sha256:1130748d28ec1c347ad4536f8d3b1f29ed4f369ca0324ad3b5c47b2cf5dcdd2e` |
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
