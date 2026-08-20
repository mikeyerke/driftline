# Tenant onboarding and connector credential lifecycle

This runbook is the repeatable infrastructure path for a new Driftline
customer boundary. It is intentionally separate from the public demo and
never puts provider credentials in the API request, browser, repository, or
logs.

## 1. Create the isolated secret containers

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

Each secret is labeled with the tenant and connector and grants
roles/secretmanager.secretAccessor only to the Driftline runtime service
account. The helper never accepts a token value.

The helper also creates `driftline-tenant-operator-acme`, an empty
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
printf '%s' 'VALUE_FROM_PROVIDER_FLOW' | +  gcloud secrets versions add driftline-tenant-acme-jira +  --project=driftline-hackathon-2026 --data-file=-
~~~

The command above is an operator example; provider values and credentials must
not appear in shell history, logs, screenshots, or source control.

## 3. Bind and verify the connector

An authenticated tenant owner calls
POST /api/connectors/{connector}/binding. Driftline derives the same
deterministic secret name, verifies that a readable version exists, and stores
only metadata in driftline_connector_bindings. The signed
GET /api/connectors/bindings and GET /api/tenants/audit routes expose status
and lifecycle events without returning credential values.

Provision non-secret destinations through the owner-only
`POST /api/connectors/{connector}/profile` route. It stores only the
connector-specific allowlisted fields in
`driftline_tenant_connector_profiles`; request bodies cannot choose an
arbitrary target or credential. The older
`DRIFTLINE_TENANT_CONNECTOR_CONFIG` environment profile is a compatibility
fallback only, not the preferred multi-tenant path.

## 4. Rotate or offboard

Add a replacement secret version, re-run the owner binding verification, and
then revoke the old provider token. POST
/api/connectors/{connector}/binding/revoke blocks runtime use without deleting
the recoverable secret. POST /api/tenants/deprovision disables memberships
and revokes every binding; provider revocation and secret deletion remain
explicit infrastructure steps.

The current hackathon deployment has one live tenant (driftline-demo). This
runbook establishes the repeatable multi-tenant boundary; a second customer
tenant and self-serve billing have not been claimed or live-verified. In the
hosted configuration, once infrastructure has created the tenant's signer and
the tenant control-plane metadata has been provisioned, subsequent signed
requests use that durable directory entry without a Cloud Run redeployment. A
real OIDC identity is still preferred for the bootstrap step.
