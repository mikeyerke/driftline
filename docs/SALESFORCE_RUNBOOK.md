# Salesforce read-only connector runbook

This runbook is for the isolated `driftline-hackathon-2026` project. The
Salesforce connector has no write method and is disabled until an operator
provisions a tenant-scoped OAuth client and secret.

## What is implemented

- OAuth authorization-code start and one-time state callback.
- Google OIDC/HMAC signed operator gate before a connection can start.
- Tenant and role binding (`viewer`, `operator`, `owner`).
- Refresh-token storage in a dedicated Secret Manager secret named
  `driftline-sf-<tenant-id>`.
- Read-only allowlist for `Product2`, `PricebookEntry`, and `Opportunity`.
- Aggregate-only health probes: counts and field names, never CRM records.
- Firestore connection metadata without bearer or refresh tokens.
- Explicit disconnect metadata path; Salesforce app revocation remains an
  operator offboarding step.

## Operator setup

1. Confirm the active project is `driftline-hackathon-2026`.
2. Create the tenant secret before authorizing:

   ```bash
   gcloud secrets create driftline-sf-driftline-demo \
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
   Never put them in Git, a browser URL, or chat.
6. Set the corresponding runtime references and deploy a new revision.
7. Call the signed `/api/connectors/salesforce/start` endpoint. Open the
   returned `authorize_url` in the already-authenticated Salesforce browser.
8. After the callback, call signed `/api/connectors/salesforce/health`. The
   response must contain only object counts, field names, and
   `external_write=false`.

## Offboarding

1. Call signed `DELETE /api/connectors/salesforce` as the tenant owner.
2. Revoke the Driftline app/session in Salesforce.
3. Disable or destroy the tenant refresh-token secret after confirming the
   retention window and audit export requirements.

The application does not claim Salesforce is connected until the callback and
the aggregate read probe both succeed in the deployed environment.
