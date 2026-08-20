# Tenant onboarding and connector credential lifecycle

This runbook is the repeatable infrastructure path for a new Driftline
customer boundary. It is intentionally separate from the public demo and
never puts provider credentials in the API request, browser, repository, or
logs.

## 1. Create the isolated secret containers

First, a platform operator may create the durable tenant and owner metadata
with the OIDC-only `POST /api/platform/tenants` route. The route accepts a
tenant ID and owner email, but no credentials; it returns the deterministic
Secret Manager references needed by the infrastructure step below. Existing
active tenants are not overwritten, while disabled tenants can be reactivated
through the same controlled path.

Run from a machine authenticated to the Driftline project:

~~~bash
gcloud config set project driftline-hackathon-2026
bash scripts/provision_tenant_connector_secrets.sh acme
~~~

The helper is idempotent and refuses to run if the active project is anything
other than driftline-hackathon-2026. It creates only:

- driftline-tenant-acme-jira
- driftline-tenant-acme-confluence
- driftline-tenant-acme-slack
- driftline-tenant-acme-github
- driftline-tenant-acme-salesforce (OAuth refresh token, when enabled)

Each secret is labeled with the tenant and connector and grants
`roles/secretmanager.secretAccessor` only to the derived tenant service
identity. The shared Cloud Run runtime receives only
`roles/iam.serviceAccountTokenCreator` on that one tenant identity; it is not a
direct reader of tenant secrets. The Salesforce secret additionally grants the
tenant identity `roles/secretmanager.secretVersionAdder` on that exact resource
because its OAuth callback writes a refresh-token version after the tenant owner
consents. No other connector receives runtime write permission. The helper
never accepts a token value.

The helper also creates the deterministic service identity
`driftline-<tenant-prefix>-<hash>@driftline-hackathon-2026.iam.gserviceaccount.com`
and `driftline-tenant-operator-acme`, an empty
tenant-specific break-glass signer container. Google OIDC is the preferred
operator identity; if a signed fallback is needed, generate a random value
out of band and add it to that exact secret. Driftline's hosted release is
configured with `DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS=true`, so a
deployment-wide signer cannot authorize a tenant-scoped request.

## 2. Add provider values out of band

Use the provider's least-privilege token/OAuth flow to add a version directly
to the exact tenant secret. Do not paste the value into Driftline requests or
commit it:

~~~bash
printf '%s' 'VALUE_FROM_PROVIDER_FLOW' | gcloud secrets versions add \
  driftline-tenant-acme-jira --project=driftline-hackathon-2026 --data-file=-
~~~

The command above is an operator example; provider values and credentials must
not appear in shell history, logs, screenshots, or source control.

## 3. Bind and verify the connector

An authenticated tenant owner calls
POST /api/connectors/{connector}/binding. Driftline derives the same
deterministic secret name, verifies that a readable version exists, resolves
its concrete Secret Manager version when available, and stores only metadata
in the canonical tenant credential path
`driftline_tenants/{tenant}/credentials/{connector}`. The legacy
`driftline_connector_bindings` collection mirrors that record during the
rolling migration. Active connector calls use that pinned
version; they do not silently follow a later `latest` secret update. The
signed
GET /api/connectors/bindings and GET /api/tenants/audit routes expose status
and lifecycle events without returning credential values.

At request time, every adapter crosses the same credential-broker seam. The
broker accepts only the authenticated tenant, an allowlisted connector, and an
operation such as `read_context` or `create_issue`; it derives the exact
tenant secret name, checks the active binding and operation scope, and returns
a short-lived in-process lease for the pinned version. Cross-tenant secret
references, revoked/rotation-pending bindings, arbitrary operations, and
invalid versions fail closed. A binding namespace mismatch also fails before
Secret Manager is read. To migrate a pre-existing deployment, run
`scripts/migrate_tenant_credential_bindings.py` first without `--apply`, then
repeat with `--apply` after reviewing the bounded metadata plan. The signed
`GET /api/connectors/credentials` route exposes the metadata-only inventory,
while `GET /api/connectors/credentials/access` exposes the tenant-filtered
append-only lease trail. Neither route returns credential values. Lease audit
records are retained for the normal 30-day window in
`driftline_credential_access_events`.

Provision non-secret destinations through the owner-only
`POST /api/connectors/{connector}/profile` route. It stores only the
connector-specific allowlisted fields in
`driftline_tenant_connector_profiles`; request bodies cannot choose an
arbitrary target or credential. The older
`DRIFTLINE_TENANT_CONNECTOR_CONFIG` environment profile is a compatibility
fallback only, not the preferred multi-tenant path.

After binding or rotation, the signed
`GET /api/connectors/bindings/health` route reconciles all five fixed connector
namespaces against readable Secret Manager state. It is safe to run repeatedly
and returns metadata-only `healthy`, `attention`, and `not_configured` results.

## 4. Rotate or offboard

For a planned rotation, the owner first POSTs
`/api/connectors/{connector}/binding/rotate` with a reason. This records an
append-only audit event and moves the binding to `rotation_pending`, so runtime
connector calls fail closed while the credential is being changed. Add a
replacement secret version to the deterministic tenant secret, then re-run the
owner binding verification route; the new version is pinned at that point, and
revoke the old provider token. POST
/api/connectors/{connector}/binding/revoke blocks runtime use without deleting
the recoverable secret. POST /api/tenants/deprovision disables memberships
and revokes every binding; provider revocation and secret deletion remain
explicit infrastructure steps.

The current hackathon deployment has one live tenant (driftline-demo). This
runbook establishes the repeatable multi-tenant boundary; a second customer
tenant and self-serve billing have not been claimed or live-verified. In the
hosted configuration, the Firestore membership directory is the OIDC source of
truth: once infrastructure has created the tenant's signer and provisioned the
tenant control-plane metadata, subsequent signed requests use that durable
directory entry without a Cloud Run redeployment or a deployment-wide email
allowlist. A real OIDC identity is still preferred for the bootstrap step.
