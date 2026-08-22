# Salesforce read-only connector runbook

This runbook is for the isolated `driftline-hackathon-2026` project. The
Salesforce connector has no write method and is disabled until an operator
provisions a tenant-scoped OAuth client and secret.

## What is implemented

- OAuth authorization-code start and one-time state callback.
- PKCE authorization with an S256 code challenge; the verifier is kept only
  in the expiring server-side OAuth state and is never sent to the browser.
- Google OIDC signed operator gate before a connection can start; the hosted
  deployment rejects the local/bootstrap HMAC break-glass path.
- Tenant and role binding (`viewer`, `operator`, `owner`).
- Refresh-token storage in the same deterministic tenant connector namespace
  as every other connector: `driftline-tenant-<tenant-id>-salesforce`.
- Read-only allowlist for `Product2`, `PricebookEntry`, and `Opportunity`.
- Aggregate-only health probes: counts and field names, never CRM records.
- OAuth callback verification gate: Driftline executes the aggregate probe with
  the short-lived access token before it stores the refresh token or activates
  the tenant binding. A callback cannot claim “connected” when the read fails.
- Firestore connection metadata without bearer or refresh tokens.
- Explicit disconnect metadata path; Salesforce app revocation remains an
  operator offboarding step.

## Operator setup

1. Confirm the active project is `driftline-hackathon-2026`.
2. Create the tenant secret before authorizing:

   ```bash
   gcloud secrets create driftline-tenant-driftline-demo-salesforce \
     --project=driftline-hackathon-2026 \
     --replication-policy=automatic
   ```

   If it already exists, do not recreate it.

3. Create an External Client App/Connected App in the Salesforce org. Enable
   OAuth and use this exact callback URL:

   `https://driftline-xvxczqg62a-uc.a.run.app/api/connectors/salesforce/oauth/callback`

4. Request only the API scope and offline refresh scope needed for a
   read-only integration. Do not grant Salesforce write scopes.
5. Store the client ID and client secret in the isolated project’s Secret
   Manager secrets `driftline-sf-client-id` and `driftline-sf-client-secret`.
   These identify Driftline’s Salesforce app; each tenant’s refresh token is
   stored separately in its own `driftline-tenant-<tenant-id>-salesforce`
   secret. Never put either kind of credential in Git, a browser URL, or chat.
6. Set the corresponding runtime references and deploy a new revision.
7. Call the signed `/api/connectors/salesforce/start` endpoint. Open the
   returned `authorize_url` in the already-authenticated Salesforce browser.
   The URL includes `code_challenge_method=S256`; do not reuse an older URL
   that was created before PKCE was enabled.
8. After the callback, call signed `/api/connectors/salesforce/health`. The
   response must contain only object counts, field names, and
   `external_write=false`. The signed status and ops-summary routes also expose
   `aggregate_read_verified`, `aggregate_read_status`, and the bounded
   `aggregate_read_objects` proof; those fields are the evidence to use in a
   deployment review.

## Offboarding

1. Call signed `DELETE /api/connectors/salesforce` as the tenant owner.
2. Revoke the Driftline app/session in Salesforce.
3. Disable or destroy the tenant refresh-token secret after confirming the
   retention window and audit export requirements.

The application does not claim Salesforce is connected until the callback,
tenant binding, and aggregate read probe all succeed in the deployed
environment. A configured OAuth client, a stored refresh token, or an HTTP 200
from the health route alone is not connection evidence. If Salesforce rejects
the refresh token with `invalid_grant`, Driftline persists only the bounded
`reauthorization_required` health state and keeps aggregate-read proof false.
