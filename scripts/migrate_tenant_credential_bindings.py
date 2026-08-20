"""Migrate legacy flat connector bindings into the tenant credential namespace.

The migration is intentionally metadata-only. It never reads Secret Manager,
accepts a credential value, or changes a provider token. Run without
``--apply`` first to inspect the bounded plan, then run with ``--apply`` from
the isolated Driftline project.
"""

from __future__ import annotations

import argparse
import os
import sys

from google.cloud import firestore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.tenant import (
    tenant_credential_namespace,
    validate_connector_name,
    validate_tenant_id,
)

PROJECT = "driftline-hackathon-2026"
LEGACY_COLLECTION = "driftline_connector_bindings"
TENANTS_COLLECTION = "driftline_tenants"
CREDENTIALS_SUBCOLLECTION = "credentials"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT", PROJECT))
    parser.add_argument("--tenant", help="Migrate only one validated tenant")
    parser.add_argument("--apply", action="store_true", help="Write the migration")
    args = parser.parse_args()
    if args.project != PROJECT:
        raise SystemExit(f"refusing project {args.project!r}; expected {PROJECT!r}")
    tenant_filter = validate_tenant_id(args.tenant) if args.tenant else None

    client = firestore.Client(project=PROJECT, database="(default)")
    documents = list(client.collection(LEGACY_COLLECTION).stream())
    planned = 0
    for snapshot in documents:
        payload = snapshot.to_dict() or {}
        try:
            tenant_id = validate_tenant_id(str(payload.get("tenant_id", "")))
            connector = validate_connector_name(str(payload.get("connector", "")))
        except ValueError:
            print(f"skip {snapshot.id}: invalid tenant/connector metadata")
            continue
        if tenant_filter and tenant_id != tenant_filter:
            continue
        namespace = tenant_credential_namespace(tenant_id, connector, PROJECT)
        canonical = (
            client.collection(TENANTS_COLLECTION)
            .document(tenant_id)
            .collection(CREDENTIALS_SUBCOLLECTION)
            .document(connector)
        )
        print(
            f"{tenant_id}/{connector}: canonical={canonical.path} "
            f"service_account={namespace['service_account']}"
        )
        if args.apply:
            migrated = dict(payload)
            migrated["credential_namespace"] = namespace
            canonical.set(migrated)
            # Keep the legacy document readable during a rolling deployment.
            snapshot.reference.set(migrated)
        planned += 1
    mode = "applied" if args.apply else "dry-run"
    print(f"{mode}: {planned} binding(s); no credential values were read")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
