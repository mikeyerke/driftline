import hashlib
import hmac
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import api, source
from app.api import app
from app.connectors import ConnectorError, _tenant_secret_or_env
from app.decision_copilot import fallback_copilot, red_team_review
from app.models import JobState
from app.tenant import principal_for_hmac, tenant_operator_signing_secret_name

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tenant_metrics_exclude_tenantless_and_other_tenant_records() -> None:
    tenantless = SimpleNamespace(tenant_id=None)
    own = SimpleNamespace(tenant_id="acme")
    other = SimpleNamespace(tenant_id="other-acme")

    assert api._visible_tenant_record(tenantless, None) is True
    assert api._visible_tenant_record(own, None) is False
    assert api._visible_tenant_record(tenantless, {"tenant_id": "acme"}) is False
    assert api._visible_tenant_record(own, {"tenant_id": "acme"}) is True
    assert api._visible_tenant_record(other, {"tenant_id": "acme"}) is False


def test_durable_record_merge_does_not_underreport_after_instance_restart(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "firestore")
    local = JobState(job_id="job-local", created_at="2026-08-20T00:02:00+00:00")
    durable = JobState(job_id="job-durable", created_at="2026-08-20T00:01:00+00:00")
    refreshed = JobState(job_id="job-local", created_at="2026-08-20T00:03:00+00:00")

    merged = api._merge_durable_records(
        [local],
        lambda _limit: [durable, refreshed],
        limit=20,
        key=lambda item: item.job_id,
    )

    assert {item.job_id for item in merged} == {"job-local", "job-durable"}
    # The in-flight local copy wins over an older or concurrently written
    # durable snapshot; the durable-only record must still be included.
    assert next(item for item in merged if item.job_id == "job-local").created_at.endswith("02:00+00:00")


def test_available_tenants_is_identity_only_and_filters_disabled_memberships(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_GOOGLE_OPERATOR_AUDIENCE", "test-audience")
    monkeypatch.setattr(
        api,
        "_verify_google_identity_claims",
        lambda _token, _audience: {
            "email": "member@example.com",
            "sub": "subject-available",
        },
    )
    api.persist_tenant({"tenant_id": "available-acme", "status": "active"})
    api.persist_tenant({"tenant_id": "available-disabled", "status": "disabled"})
    api.persist_tenant_membership(
        {
            "tenant_id": "available-acme",
            "email": "member@example.com",
            "role": "operator",
            "status": "active",
        }
    )
    api.persist_tenant_membership(
        {
            "tenant_id": "available-disabled",
            "email": "member@example.com",
            "role": "owner",
            "status": "active",
        }
    )

    response = client.get(
        "/api/tenants/available", params={"identity_token": "opaque-token"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "member@example.com"
    assert payload["selection_required"] is False
    assert payload["tenants"] == [
        {
            "tenant_id": "available-acme",
            "role": "operator",
            "membership_id": payload["tenants"][0]["membership_id"],
            "status": "active",
        }
    ]
    assert payload["credential_values_exposed"] is False


def test_monitor_registry_and_ops_summary_are_safe_for_operator_console() -> None:
    registry = client.get("/api/monitor/registry")
    assert registry.status_code == 200
    registry_payload = registry.json()
    assert registry_payload["append_only"] is True
    assert registry_payload["summary"]["total"] == 5
    assert registry_payload["summary"]["source_failed"] == 0
    assert all(
        "token" not in str(item).casefold() for item in registry_payload["sources"]
    )

    ops = client.get("/api/ops/summary")
    assert ops.status_code == 200
    ops_payload = ops.json()
    assert ops_payload["project_id"]
    assert set(ops_payload["connectors"]) == {"jira", "confluence", "slack", "github"}
    assert "guardrails" in ops_payload
    assert ops_payload["crm"]["salesforce"]["mode"] == "prepared_only"
    assert ops_payload["approval_security"]["external_writes_require_signed"] is True
    assert ops_payload["approval_security"]["credential_model"]["tenant_bound"] is True
    assert ops_payload["jobs"]["dead_lettered"] == 0

    value_proof = client.get("/api/ops/value-proof")
    assert value_proof.status_code == 200
    assert value_proof.json()["scope"] == "observed_driftline_sandbox_records"
    assert "willingness_to_pay" in value_proof.json()["not_measured"]
    assert "change_cards" in value_proof.json()["observed"]
    assert "workflow_data_modes" in value_proof.json()["observed"]
    assert "job_run_modes" in value_proof.json()["observed"]
    assert "tenantless_workflows" in value_proof.json()["observed"]
    assert "high_materiality_cards" in value_proof.json()["observed"]
    assert "cards_dismissed" in value_proof.json()["observed"]
    assert "overdue_owner_actions" in value_proof.json()["observed"]
    outcomes = client.get("/api/ops/outcomes")
    assert outcomes.status_code == 200
    assert outcomes.json()["status"] == "not_measured"


def test_source_registry_and_freshness_can_be_bound_to_signed_tenant(monkeypatch) -> None:
    """Tenant operators can read only their signed source metadata surface."""
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "source-registry-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    actor = "Tenant reader"
    tenant_id = "driftline-demo"

    sources_token = hmac.new(
        secret.encode(), f"sources:list:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    sources = client.get(
        "/api/sources",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": sources_token,
        },
    )
    assert sources.status_code == 200
    assert len(sources.json()["sources"]) == 5
    assert all("token" not in str(item).casefold() for item in sources.json()["sources"])

    registry_token = hmac.new(
        secret.encode(), f"monitor-registry:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    registry = client.get(
        "/api/monitor/registry",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": registry_token,
        },
    )
    assert registry.status_code == 200
    assert registry.json()["summary"]["total"] == 5
    assert all("token" not in str(item).casefold() for item in registry.json()["sources"])


def test_signed_tenant_usage_is_aggregate_and_not_billing(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "usage-route-secret"
    actor = "Usage reader"
    tenant_id = "usage-route-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.record_tenant_usage(tenant_id, "agent_calls", period="2026-08")
    api.record_tenant_usage(tenant_id, "workflow_mutations", amount=2, period="2026-08")
    token = hmac.new(
        secret.encode(), f"tenant-usage:{actor}".encode(), hashlib.sha256
    ).hexdigest()

    response = client.get(
        "/api/tenants/usage",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "period": "2026-08",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["usage"] == {
        "agent_calls": 1,
        "workflow_mutations": 2,
        "monitor_jobs": 0,
    }
    assert payload["metering"]["durable"] is True
    assert payload["metering"]["billing_enabled"] is False
    assert payload["credential_values_exposed"] is False


def test_signed_job_failure_ledger_is_tenant_filtered_and_redacted(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "failure-ledger-secret"
    actor = "Failure reader"
    tenant_id = "failure-ledger-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.persist_job_failure(
        {
            "job_id": "job-terminal-1",
            "tenant_id": tenant_id,
            "attempts": 3,
            "failed_at": "2026-08-20T00:00:00+00:00",
            "exception_text": "must never be retained",
        }
    )
    token = hmac.new(
        secret.encode(), f"job-failures:{actor}".encode(), hashlib.sha256
    ).hexdigest()

    response = client.get(
        "/api/ops/job-failures",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["failures"][0]["status"] == "dead_lettered"
    assert payload["failures"][0]["attempts"] == 3
    assert "exception_text" not in str(payload)
    assert payload["credential_values_exposed"] is False


def test_job_failure_ledger_requires_signed_operator() -> None:
    response = client.get("/api/ops/job-failures")
    assert response.status_code == 422


def test_outcome_measurements_require_signed_operator(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    response = client.post(
        "/api/ops/outcomes",
        json={
            "operator": "Anonymous",
            "source_type": "pilot_log",
            "cohort_label": "pilot-a",
            "changes_observed": 1,
            "baseline_minutes": 60,
            "driftline_minutes": 20,
            "evidence_ref": "artifact://pilot-a",
        },
    )
    assert response.status_code == 401


def test_connector_context_summary_is_signed_and_redacted(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "context-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setattr(
        api,
        "_connector_context_info",
        lambda _tenant_id: {
            "jira": {
                "status": "ok",
                "scope": "read_only_project",
                "external_read": True,
                "open_issue_count": 2,
                "redaction": "aggregate_metadata_only",
            }
        },
    )
    token = hmac.new(
        secret.encode(), b"connector-context-summary:Signed operator", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Signed operator",
            "tenant_id": "driftline-demo",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "driftline-demo"
    assert payload["context_contract"]["persisted"] is False
    assert payload["context_contract"]["redaction"] == "aggregate_metadata_only"
    assert payload["connectors"]["jira"]["open_issue_count"] == 2
    assert "private" not in str(payload)


def test_connector_context_summary_rejects_unsigned_public_request(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    response = client.post(
        "/api/connectors/context/summary",
        json={"operator": "Anonymous"},
    )
    assert response.status_code == 401


def test_hmac_tenant_allowlist_rejects_unknown_tenant(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", "allowlist-secret")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    token = hmac.new(
        b"allowlist-secret",
        b"connector-context-summary:Tenant context",
        hashlib.sha256,
    ).hexdigest()
    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Tenant context",
            "tenant_id": "other-tenant",
            "approval_token": token,
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "tenant_not_allowlisted"


def test_hmac_can_require_a_tenant_specific_signing_secret(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS", "true")
    monkeypatch.setenv("DRIFTLINE_TENANT_SIGNING_SECRET_PREFIX", "driftline-signer-")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "signer-acme")
    tenant_secret = "signer-acme-secret"

    def fake_read_secret(name: str) -> str:
        assert name == tenant_operator_signing_secret_name(
            "signer-acme", "driftline-signer-"
        )
        return tenant_secret

    monkeypatch.setattr(api, "read_secret", fake_read_secret)
    token = hmac.new(
        tenant_secret.encode(),
        b"connector-context-summary:Tenant signer",
        hashlib.sha256,
    ).hexdigest()
    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Tenant signer",
            "tenant_id": "signer-acme",
            "approval_token": token,
        },
    )
    assert response.status_code == 200

    wrong_token = hmac.new(
        b"deployment-wide-secret",
        b"connector-context-summary:Tenant signer",
        hashlib.sha256,
    ).hexdigest()
    rejected = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Tenant signer",
            "tenant_id": "signer-acme",
            "approval_token": wrong_token,
        },
    )
    assert rejected.status_code == 401


def test_hmac_required_tenant_signer_fails_closed_when_secret_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_REQUIRE_TENANT_SIGNING_SECRETS", "true")
    monkeypatch.setenv("DRIFTLINE_TENANT_SIGNING_SECRET_PREFIX", "driftline-signer-")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "missing-acme")

    def missing_secret(_name: str) -> str:
        raise api.ConnectorError("missing")

    monkeypatch.setattr(api, "read_secret", missing_secret)
    response = client.post(
        "/api/connectors/context/summary",
        json={
            "operator": "Missing signer",
            "tenant_id": "missing-acme",
            "approval_token": "anything",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Tenant signing secret is unavailable"


def test_hmac_can_use_the_durable_tenant_directory_without_redeployment(monkeypatch) -> None:
    tenant_id = "durable-directory-acme"
    monkeypatch.setenv("DRIFTLINE_PERSISTENCE", "memory")
    monkeypatch.setenv("DRIFTLINE_ALLOW_DURABLE_HMAC_TENANTS", "true")
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "")
    api.persist_tenant({"tenant_id": tenant_id, "status": "active"})

    principal = principal_for_hmac(tenant_id)

    assert principal.tenant_id == tenant_id
    assert principal.role == "owner"

    api.persist_tenant({"tenant_id": tenant_id, "status": "disabled"})
    with pytest.raises(PermissionError, match="tenant_not_allowlisted"):
        principal_for_hmac(tenant_id)

    with pytest.raises(PermissionError, match="tenant_not_allowlisted"):
        principal_for_hmac("directory-missing-acme")


def test_platform_tenant_provisioning_creates_metadata_only_bootstrap(monkeypatch) -> None:
    tenant_id = "platform-bootstrap-acme"
    monkeypatch.setattr(
        api,
        "_verify_platform_operator",
        lambda _token: {
            "identity": "google_oidc_platform_operator",
            "subject": "platform-subject",
            "email": "platform@example.com",
        },
    )
    response = client.post(
        "/api/platform/tenants",
        json={
            "operator": "Platform bootstrap",
            "tenant_id": tenant_id,
            "owner_email": "owner@example.com",
            "identity_token": "opaque-test-token",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["owner_email"] == "owner@example.com"
    assert payload["credential_values_exposed"] is False
    assert payload["secret_references"]["jira"] == (
        f"driftline-tenant-{tenant_id}-jira"
    )
    assert payload["secret_references"]["salesforce"] == (
        f"driftline-tenant-{tenant_id}-salesforce"
    )
    assert payload["operator_signing_secret"] == (
        f"driftline-tenant-operator-{tenant_id}"
    )
    assert "token" not in str(payload).casefold()
    assert api.load_tenant(tenant_id)["status"] == "active"
    assert api.list_tenant_memberships(tenant_id)[0]["role"] == "owner"


def test_platform_tenant_provisioning_rejects_duplicate_active_tenant(monkeypatch) -> None:
    tenant_id = "platform-duplicate-acme"
    api.persist_tenant({"tenant_id": tenant_id, "status": "active"})
    monkeypatch.setattr(
        api,
        "_verify_platform_operator",
        lambda _token: {"identity": "google_oidc_platform_operator", "email": "platform@example.com"},
    )
    response = client.post(
        "/api/platform/tenants",
        json={
            "operator": "Platform bootstrap",
            "tenant_id": tenant_id,
            "owner_email": "owner@example.com",
            "identity_token": "opaque-test-token",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "tenant_already_exists"


def test_salesforce_callback_cannot_rebind_deprovisioned_tenant(monkeypatch) -> None:
    writes: list[str] = []
    monkeypatch.setattr(
        api,
        "_consume_salesforce_state",
        lambda _state: {
            "tenant_id": "callback-acme",
            "email": "owner@example.com",
            "expires_at": 9_999_999_999,
            "code_verifier": "verifier",
        },
    )
    monkeypatch.setattr(
        api,
        "exchange_salesforce_code",
        lambda *_args, **_kwargs: {
            "refresh_token": "refresh-token",
            "instance_url": "https://callback.my.salesforce.com",
        },
    )
    monkeypatch.setattr(api, "load_tenant", lambda _tenant_id: {"status": "disabled"})
    monkeypatch.setattr(
        api,
        "write_secret_version",
        lambda secret_name, _value: writes.append(secret_name),
    )

    response = client.get(
        "/api/connectors/salesforce/oauth/callback",
        params={"code": "one-time-code", "state": "opaque-state"},
    )

    assert response.status_code == 503
    assert writes == []


def test_salesforce_oauth_start_is_owner_only(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "_verify_approval_mode",
        lambda *_args, **_kwargs: {
            "tenant_id": "salesforce-acme",
            "role": "operator",
            "identity": "signed_operator",
        },
    )

    response = client.post(
        "/api/connectors/salesforce/start",
        json={"operator": "Operator", "tenant_id": "salesforce-acme"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant owner role is required"


def test_owner_can_register_metadata_only_tenant_binding(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "binding-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "binding-acme")
    monkeypatch.setattr(api, "read_secret", lambda name: "tenant-token")
    token = hmac.new(
        secret.encode(), b"connector-binding:jira:Binding owner", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/connectors/jira/binding",
        json={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "active"
    assert payload["secret_name"] == "driftline-tenant-binding-acme-jira"
    assert payload["secret_version"] == "latest"
    assert payload["credential_value_accepted"] is False
    listed = client.get(
        "/api/connectors/bindings",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"connector-bindings-list:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert listed.status_code == 200
    assert listed.json()["credential_values_exposed"] is False
    assert listed.json()["bindings"][0]["secret_name"] == payload["secret_name"]
    revoked = client.post(
        "/api/connectors/jira/binding/revoke",
        json={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(),
                b"connector-binding-revoke:jira:Binding owner",
                hashlib.sha256,
            ).hexdigest(),
        },
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["credential_value_exposed"] is False
    assert client.get(
        "/api/connectors/bindings",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"connector-bindings-list:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    ).json()["bindings"][0]["status"] == "revoked"
    audit = client.get(
        "/api/tenants/audit",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"tenant-audit:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert audit.status_code == 200
    assert audit.json()["append_only"] is True
    assert {event["event_type"] for event in audit.json()["events"]} >= {
        "connector_binding_activated",
        "connector_binding_revoked",
    }
    assert audit.json()["credential_values_exposed"] is False
    assert "tenant-token" not in str(audit.json())
    tenant_metadata = client.get(
        "/api/tenants",
        params={
            "operator": "Binding owner",
            "tenant_id": "binding-acme",
            "approval_token": hmac.new(
                secret.encode(), b"tenant-metadata:Binding owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert tenant_metadata.status_code == 200
    assert tenant_metadata.json()["tenant"]["tenant_id"] == "binding-acme"
    assert tenant_metadata.json()["credential_values_exposed"] is False


def test_owner_can_enroll_a_tenant_connector_without_submitting_a_secret(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "enrollment-test-secret"
    tenant_id = "enrollment-route-acme"
    operator = "Enrollment owner"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)

    start_token = hmac.new(
        secret.encode(),
        b"credential-enrollment:jira:Enrollment owner",
        hashlib.sha256,
    ).hexdigest()
    started = client.post(
        "/api/connectors/jira/credential-enrollment",
        json={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": start_token,
        },
    )
    assert started.status_code == 200
    enrollment = started.json()
    assert enrollment["status"] == "awaiting_secret"
    assert enrollment["allowed_operations"] == ["read_context", "runtime"]
    assert enrollment["secret_name"] == f"driftline-tenant-{tenant_id}-jira"
    assert enrollment["credential_value_exposed"] is False
    assert "opaque-token" not in str(enrollment)

    monkeypatch.setattr(api, "_read_tenant_secret", lambda *_args, **_kwargs: "opaque-token")
    monkeypatch.setattr(api, "_tenant_secret_version", lambda *_args, **_kwargs: "3")
    enrollment_id = enrollment["enrollment_id"]
    complete_token = hmac.new(
        secret.encode(),
        f"credential-enrollment-complete:jira:{enrollment_id}:Enrollment owner".encode(),
        hashlib.sha256,
    ).hexdigest()
    completed = client.post(
        f"/api/connectors/jira/credential-enrollment/{enrollment_id}/complete",
        json={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": complete_token,
        },
    )
    assert completed.status_code == 200
    payload = completed.json()
    assert payload["status"] == "active"
    assert payload["secret_version"] == "3"
    assert payload["allowed_operations"] == ["read_context", "runtime"]
    assert payload["credential_value_exposed"] is False
    assert "opaque-token" not in str(payload)
    assert api.load_connector_binding(tenant_id, "jira")["allowed_operations"] == [
        "read_context",
        "runtime",
    ]


def test_owner_can_inspect_credential_broker_inventory_and_access_ledger(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "credential-inventory-test-secret"
    tenant_id = "credential-inventory-acme"
    operator = "Credential owner"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": "jira",
            "secret_name": f"driftline-tenant-{tenant_id}-jira",
            "credential_id": "cred-inventory-jira-1",
            "status": "active",
            "secret_version": "4",
            "allowed_operations": ["runtime", "create_issue"],
        }
    )
    inventory = client.get(
        "/api/connectors/credentials",
        params={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(),
                b"connector-credentials-list:Credential owner",
                hashlib.sha256,
            ).hexdigest(),
        },
    )
    assert inventory.status_code == 200
    payload = inventory.json()
    assert payload["credentials"][0]["credential_id"] == "cred-inventory-jira-1"
    assert payload["credentials"][0]["allowed_operations"] == [
        "create_issue",
        "runtime",
    ]
    assert payload["credential_values_exposed"] is False
    assert "secret_name" not in str(payload)

    monkeypatch.setattr(
        api,
        "list_credential_access_events",
        lambda _tenant, limit=100: [
            {
                "tenant_id": tenant_id,
                "credential_id": "cred-inventory-jira-1",
                "connector": "jira",
                "operation": "create_issue",
                "secret_version": "4",
                "outcome": "resolved",
            }
        ],
    )
    access = client.get(
        "/api/connectors/credentials/access",
        params={
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(),
                b"connector-credentials-access:Credential owner",
                hashlib.sha256,
            ).hexdigest(),
        },
    )
    assert access.status_code == 200
    assert access.json()["append_only"] is True
    assert access.json()["events"][0]["credential_id"] == "cred-inventory-jira-1"
    assert access.json()["credential_values_exposed"] is False


def test_owner_rotation_fails_closed_until_binding_is_reverified(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "rotation-test-secret"
    tenant_id = "rotation-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    monkeypatch.setattr(api, "read_secret", lambda _name: "replacement-ready")
    api.persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": "jira",
            "secret_name": f"driftline-tenant-{tenant_id}-jira",
            "status": "active",
            "scope": "tenant_bound_connector_credential",
        }
    )
    token = hmac.new(
        secret.encode(),
        b"connector-binding-rotate:jira:Rotation owner",
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/connectors/jira/binding/rotate",
        json={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "reason": "scheduled credential rotation",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rotation_pending"
    assert payload["rotation_id"].startswith("rotation-")
    assert payload["credential_value_exposed"] is False
    assert api.load_connector_binding(tenant_id, "jira")["status"] == "rotation_pending"
    repeated = client.post(
        "/api/connectors/jira/binding/rotate",
        json={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "reason": "retry after timeout",
            "approval_token": token,
        },
    )
    assert repeated.status_code == 200
    assert repeated.json()["already_pending"] is True
    assert repeated.json()["rotation_id"] == payload["rotation_id"]
    with pytest.raises(ConnectorError, match="jira_tenant_binding_missing"):
        _tenant_secret_or_env(tenant_id, "jira", "DRIFTLINE_JIRA_TOKEN")

    reactivate = client.post(
        "/api/connectors/jira/binding",
        json={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(), b"connector-binding:jira:Rotation owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert reactivate.status_code == 200
    assert reactivate.json()["status"] == "active"
    audit = client.get(
        "/api/tenants/audit",
        params={
            "operator": "Rotation owner",
            "tenant_id": tenant_id,
            "approval_token": hmac.new(
                secret.encode(), b"tenant-audit:Rotation owner", hashlib.sha256
            ).hexdigest(),
        },
    )
    assert audit.status_code == 200
    assert "connector_binding_rotation_requested" in {
        event["event_type"] for event in audit.json()["events"]
    }


def test_connector_binding_health_reconciles_without_exposing_credentials(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "health-test-secret"
    tenant_id = "health-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    monkeypatch.setattr(
        api,
        "list_connector_bindings",
        lambda _tenant: [
            {
                "tenant_id": tenant_id,
                "connector": "jira",
                "secret_name": f"driftline-tenant-{tenant_id}-jira",
                "status": "active",
            },
            {
                "tenant_id": tenant_id,
                "connector": "slack",
                "secret_name": f"driftline-tenant-{tenant_id}-slack",
                "status": "rotation_pending",
            },
        ],
    )
    monkeypatch.setattr(
        api,
        "load_connector_profile",
        lambda _tenant, connector: (
            {"status": "active", "settings": {"project_key": "KAN"}}
            if connector == "jira"
            else None
        ),
    )
    monkeypatch.setattr(api, "read_secret", lambda _name: "token-not-returned")
    token = hmac.new(
        secret.encode(),
        b"connector-bindings-health:Health owner",
        hashlib.sha256,
    ).hexdigest()

    response = client.get(
        "/api/connectors/bindings/health",
        params={
            "operator": "Health owner",
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {
        "total": 5,
        "healthy": 1,
        "attention": 1,
        "not_configured": 3,
    }
    jira = next(item for item in payload["checks"] if item["connector"] == "jira")
    assert jira["status"] == "healthy"
    assert jira["secret_status"] == "readable"
    assert jira["profile_status"] == "healthy"
    assert jira["profile_configured_keys"] == ["project_key"]
    slack = next(item for item in payload["checks"] if item["connector"] == "slack")
    assert slack["status"] == "attention"
    assert slack["secret_status"] == "not_checked"
    assert slack["profile_status"] == "not_configured"
    assert "token-not-returned" not in str(payload)
    assert payload["credential_values_exposed"] is False


def test_owner_can_register_non_secret_connector_profile(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "profile-route-test-secret"
    tenant_id = "profile-route-acme"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    token = hmac.new(
        secret.encode(), b"connector-profile:jira:Profile owner", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/connectors/jira/profile",
        json={
            "operator": "Profile owner",
            "tenant_id": tenant_id,
            "settings": {
                "base_url": "https://profile.atlassian.net",
                "project_key": "PROF",
            },
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["settings"]["project_key"] == "PROF"
    assert payload["credential_values_accepted"] is False

    read_token = hmac.new(
        secret.encode(),
        b"connector-profile-read:jira:Profile owner",
        hashlib.sha256,
    ).hexdigest()
    read = client.get(
        "/api/connectors/jira/profile",
        params={
            "operator": "Profile owner",
            "tenant_id": tenant_id,
            "approval_token": read_token,
        },
    )
    assert read.status_code == 200
    assert read.json()["settings"]["base_url"] == "https://profile.atlassian.net"
    assert read.json()["credential_values_exposed"] is False
    assert "secret" not in str(read.json()).casefold()


def test_owner_can_provision_durable_member_without_credentials(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "membership-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "membership-acme")
    token = hmac.new(
        secret.encode(),
        b"tenant-member-provision:Membership owner",
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/api/tenants/members",
        json={
            "operator": "Membership owner",
            "tenant_id": "membership-acme",
            "email": "operator@example.com",
            "role": "operator",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "membership-acme"
    assert payload["role"] == "operator"
    assert payload["credential_values_exposed"] is False
    assert "secret" not in str(payload).casefold()


def test_owner_can_soft_deprovision_tenant_and_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "deprovision-test-secret"
    tenant_id = "deprovision-acme"
    actor = "Deprovision owner"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    api.persist_connector_binding(
        {
            "tenant_id": tenant_id,
            "connector": "jira",
            "secret_name": f"driftline-tenant-{tenant_id}-jira",
            "status": "active",
            "scope": "tenant_bound_connector_credential",
        }
    )
    api.persist_tenant_membership(
        {
            "tenant_id": tenant_id,
            "email": "member@example.com",
            "role": "operator",
            "status": "active",
        }
    )
    token = hmac.new(
        secret.encode(), b"tenant-deprovision:Deprovision owner", hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/tenants/deprovision",
        json={
            "operator": actor,
            "tenant_id": tenant_id,
            "confirmation": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
    assert response.json()["revoked_binding_count"] == 1
    assert response.json()["disabled_membership_count"] == 1
    assert response.json()["credential_values_exposed"] is False
    metadata_token = hmac.new(
        secret.encode(), b"tenant-metadata:Deprovision owner", hashlib.sha256
    ).hexdigest()
    blocked = client.get(
        "/api/tenants",
        params={
            "operator": actor,
            "tenant_id": tenant_id,
            "approval_token": metadata_token,
        },
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "tenant_disabled"


def test_scheduler_tick_fans_out_only_allowlisted_sources(monkeypatch) -> None:
    monkeypatch.setattr(api, "_verify_scheduler_request", lambda request: None)
    monkeypatch.setattr(
        api,
        "_start_job",
        lambda **kwargs: JobState(job_id=f"job-{kwargs['query'].split()[-2]}"),
    )
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post("/api/scheduler/tick")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_ids"] == [
        "public/pricing",
        "public/terms",
        "competitor/pricing",
        "competitor/offerings",
        "competitor/blog",
    ]
    assert len(payload["jobs"]) == 5


def test_scheduler_tick_carries_custom_source_tenant(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    source.register_operator_source(
        source_id="custom/tenant-pricing",
        name="Tenant pricing",
        category="Competitor pricing",
        change_type="Pricing move",
        url="https://example.com/pricing",
        owner="Product Marketing",
        cadence="24h",
        freshness_sla_hours=48,
        tenant_id="acme",
    )
    monkeypatch.setattr(api, "_verify_scheduler_request", lambda request: None)
    captured: list[dict[str, object]] = []

    def fake_start_job(**kwargs):
        captured.append(kwargs)
        return JobState(job_id=f"job-{len(captured)}")

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    monkeypatch.setenv("DRIFTLINE_MONITOR_MAX_SOURCES", "6")
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._tenant_agent_call_times.clear()

    response = client.post("/api/scheduler/tick")
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert response.status_code == 200
    custom = next(item for item in captured if item.get("tenant_id") == "acme")
    assert "custom/tenant-pricing" in str(custom["query"])


def test_signed_operator_can_onboard_an_exact_public_source(monkeypatch) -> None:
    source._CUSTOM_SOURCE_DEFINITIONS.clear()
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    source_id = "custom/example-pricing"
    message = f"source-onboarding:{source_id}:Signed operator".encode()
    token = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/operator/sources",
        json={
            "source_id": source_id,
            "name": "Example pricing",
            "category": "Competitor pricing",
            "change_type": "Pricing move",
            "url": "https://example.com/pricing",
            "owner": "Product Marketing",
            "cadence": "24h",
            "freshness_sla_hours": 48,
            "parser": "html",
            "registered_by": "Signed operator",
            "approval_token": token,
        },
    )
    source._CUSTOM_SOURCE_DEFINITIONS.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "registered"
    assert (
        response.json()["source"]["allowlist"] == "exact operator-registered HTTPS URL"
    )


def test_manual_monitor_job_requires_signed_operator(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setattr(
        api,
        "_start_job",
        lambda **kwargs: JobState(job_id="job-monitor-test"),
    )
    denied = client.post(
        "/api/jobs/demo",
        json={"run_mode": "monitor", "source_id": "public/pricing"},
    )
    assert denied.status_code == 401

    operator = "Signed operator"
    message = f"monitor:public/pricing:{operator}".encode()
    token = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    allowed = client.post(
        "/api/jobs/demo",
        json={
            "run_mode": "monitor",
            "source_id": "public/pricing",
            "operator": operator,
            "approval_token": token,
        },
    )
    assert allowed.status_code == 200


def test_signed_monitor_job_carries_authenticated_tenant(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "tenant-monitor-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo")
    captured: dict[str, object] = {}

    def fake_start_job(**kwargs):
        captured.update(kwargs)
        return JobState(job_id="job-tenant-monitor", tenant_id=kwargs["tenant_id"])

    monkeypatch.setattr(api, "_start_job", fake_start_job)
    actor = "Tenant monitor operator"
    token = hmac.new(
        secret.encode(), f"monitor:public/pricing:{actor}".encode(), hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/jobs/demo",
        json={
            "run_mode": "monitor",
            "source_id": "public/pricing",
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert captured["tenant_id"] == "driftline-demo"
    assert response.json()["tenant_id"] == "driftline-demo"


def test_signed_operator_cannot_approve_another_tenant_workflow(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "cross-tenant-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "other-acme")
    state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(state)
    token = hmac.new(
        secret.encode(), f"{state.workflow_id}:Other operator".encode(), hashlib.sha256
    ).hexdigest()

    response = client.post(
        f"/api/workflows/{state.workflow_id}/approve",
        json={
            "approver": "Other operator",
            "approval_mode": "signed",
            "tenant_id": "other-acme",
            "approval_token": token,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "workflow_tenant_mismatch"


def test_tenant_bound_reads_require_matching_signed_identity(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "tenant-read-test-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", "driftline-demo,other-acme")
    state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(state)
    job = JobState(job_id="job-tenant-read", tenant_id="driftline-demo")
    with api._jobs_lock:
        api._jobs[job.job_id] = job

    public = client.get(f"/api/workflows/{state.workflow_id}")
    assert public.status_code == 403
    assert public.json()["detail"] == "Tenant-scoped resource requires signed approval"
    action_public = client.post(
        f"/api/workflows/{state.workflow_id}/actions/action-1/claim",
        json={"actor": "Action actor"},
    )
    assert action_public.status_code == 403
    assert action_public.json()["detail"] == "Tenant-scoped workflow requires signed approval"
    assert client.get("/api/jobs/job-tenant-read").status_code == 403
    assert all(item["job_id"] != job.job_id for item in client.get("/api/jobs").json()["jobs"])
    assert state.workflow_id not in str(client.get("/api/memory/summary").json())
    assert state.workflow_id not in str(client.get("/api/ops/summary").json())
    public_value = client.get("/api/ops/value-proof").json()

    actor = "Tenant reader"
    token = hmac.new(
        secret.encode(), f"{state.workflow_id}:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    signed_params = {
        "operator": actor,
        "tenant_id": "driftline-demo",
        "approval_token": token,
    }
    assert client.get(f"/api/workflows/{state.workflow_id}", params=signed_params).status_code == 200
    assert client.get(
        f"/api/workflows/{state.workflow_id}/actions", params=signed_params
    ).status_code == 200
    assert client.get(
        f"/api/workflows/{state.workflow_id}/scenarios", params=signed_params
    ).status_code == 200
    assert client.get(
        f"/api/workflows/{state.workflow_id}/packet", params=signed_params
    ).status_code == 200
    memory_token = hmac.new(
        secret.encode(), f"memory:summary:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    signed_memory = client.get(
        "/api/memory/summary",
        params={
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": memory_token,
        },
    )
    assert signed_memory.status_code == 200
    assert state.workflow_id in str(signed_memory.json())
    value_token = hmac.new(
        secret.encode(), f"ops:value-proof:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    signed_value = client.get(
        "/api/ops/value-proof",
        params={
            "operator": actor,
            "tenant_id": "driftline-demo",
            "approval_token": value_token,
        },
    )
    assert signed_value.status_code == 200
    signed_value_payload = signed_value.json()
    assert signed_value_payload["scope"] == "observed_tenant_records"
    assert signed_value_payload["observed"]["tenant_scoped_workflows"] >= 1
    assert signed_value_payload["observed"]["tenantless_workflows"] == 0
    assert (
        signed_value_payload["observed"]["workflows"]
        >= public_value["observed"]["workflows"] + 1
    )

    wrong_token = hmac.new(
        secret.encode(), f"{state.workflow_id}:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    wrong = client.get(
        f"/api/workflows/{state.workflow_id}",
        params={
            "operator": actor,
            "tenant_id": "other-acme",
            "approval_token": wrong_token,
        },
    )
    assert wrong.status_code == 403
    assert wrong.json()["detail"] == "workflow_tenant_mismatch"


def test_rate_limits_are_isolated_per_tenant(monkeypatch) -> None:
    monkeypatch.setattr(api, "AGENT_MAX_CALLS", 1)
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 1)
    api._tenant_agent_call_times.clear()
    api._tenant_demo_mutation_times.clear()

    assert api._reserve_agent_call("tenant-a") is True
    assert api._reserve_agent_call("tenant-a") is False
    assert api._reserve_agent_call("tenant-b") is True
    assert api._reserve_demo_mutation("tenant-a") is True
    assert api._reserve_demo_mutation("tenant-a") is False
    assert api._reserve_demo_mutation("tenant-b") is True


def test_demo_approval_and_undo_round_trip() -> None:
    started = client.post("/api/workflows/demo")
    assert started.status_code == 200
    workflow_id = started.json()["workflow_id"]

    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "complete"
    assert approved.json()["action_record"]["operational_status"] == "not_configured"
    assert approved.json()["action_record"]["jira_status"] == "prepared_only"

    undone = client.post(
        f"/api/workflows/{workflow_id}/undo",
        json={"actor": "Demo operator"},
    )
    assert undone.status_code == 200
    assert undone.json()["status"] == "needs_approval"
    assert undone.json()["action_record"]["operational_status"] == "not_configured"
    assert undone.json()["action_record"]["jira_status"] == "prepared_only"


def test_demo_dismissal_records_reason_without_creating_work() -> None:
    started = client.post("/api/workflows/demo")
    assert started.status_code == 200
    workflow_id = started.json()["workflow_id"]

    dismissed = client.post(
        f"/api/workflows/{workflow_id}/dismiss",
        json={
            "actor": "Demo operator",
            "reason": "Not material for the current segment",
        },
    )

    assert dismissed.status_code == 200
    payload = dismissed.json()
    assert payload["status"] == "dismissed"
    assert payload["approval"]["decision"] == "dismissed"
    assert payload["approval"]["reason"] == "Not material for the current segment"
    assert payload["change_card"]["closure"]["state"] == "dismissed"
    assert payload["action_items"] == []

    packet = client.get(f"/api/workflows/{workflow_id}/packet")
    assert packet.status_code == 200
    assert "Decision reason: Not material for the current segment" in packet.text


def test_same_demo_snapshot_exposes_stable_change_card_identity() -> None:
    first = client.post("/api/workflows/demo").json()
    second = client.post("/api/workflows/demo").json()
    assert first["change_card"]["change_card_id"] == second["change_card"]["change_card_id"]

    approved = client.post(
        f"/api/workflows/{first['workflow_id']}/approve",
        json={"approver": "Demo operator"},
    )
    assert approved.status_code == 200
    assert approved.json()["action_record"]["change_card_id"] == first["change_card"]["change_card_id"]


def test_demo_approval_never_calls_configured_connectors(monkeypatch) -> None:
    """Public named actors receive a packet even if connector env is present."""
    calls: list[str] = []

    def forbidden(state):
        calls.append("write")
        raise AssertionError("demo approval crossed the external-write boundary")

    monkeypatch.setenv("DRIFTLINE_JIRA_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_CONFLUENCE_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_SLACK_ENABLED", "true")
    monkeypatch.setenv("DRIFTLINE_GITHUB_ENABLED", "true")
    monkeypatch.setattr(
        api,
        "_CONNECTOR_HANDOFFS",
        tuple((name, forbidden, forbidden) for name, _, _ in api._CONNECTOR_HANDOFFS),
    )

    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Public demo reviewer"},
    )

    assert approved.status_code == 200
    action = approved.json()["action_record"]
    assert not calls
    assert action["external_write"] is False
    assert action["external_write_authorized"] is False
    assert all(
        action[f"{name}_status"] == "prepared_only"
        for name in ("jira", "confluence", "slack", "github")
    )


def test_signed_approval_can_cross_connector_boundary_when_enabled(monkeypatch) -> None:
    calls: list[str] = []

    def create(state):
        calls.append("write")
        return {"jira_status": "created", "external_write": True}

    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setattr(
        api,
        "_CONNECTOR_HANDOFFS",
        (("jira", create, create),),
    )
    tenant_state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(tenant_state)
    workflow_id = tenant_state.workflow_id
    actor = "Signed operator"
    token = hmac.new(
        secret.encode(), f"{workflow_id}:{actor}".encode(), hashlib.sha256
    ).hexdigest()
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": actor,
            "approval_mode": "signed",
            "approval_token": token,
        },
    )

    assert approved.status_code == 200
    assert calls == ["write"]
    assert approved.json()["action_record"]["external_write_authorized"] is True


def test_source_history_endpoint_is_explicitly_append_only() -> None:
    response = client.get("/api/sources/public/pricing/history")
    assert response.status_code == 200
    assert response.json()["append_only"] is True
    assert "memory" in response.json()


def test_memory_summary_is_ui_ready_and_bounded() -> None:
    response = client.get("/api/memory/summary?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["append_only"] is True
    assert "change_genomes" in payload
    assert set(payload["work_summary"]) >= {
        "unresolved",
        "reversed",
        "unresolved_count",
        "reversed_count",
    }


def test_competitor_source_builds_offering_impact_graph_and_handoffs() -> None:
    started = client.post("/api/workflows/demo?source_id=competitor/pricing")
    assert started.status_code == 200
    payload = started.json()
    assert payload["evidence"]["source_id"] == "competitor/pricing"
    assert payload["impact_graph"]["summary"]["category"] == "Competitor pricing"
    assert "Comparison map" in {item["name"] for item in payload["impacts"]}
    assert {item["system"] for item in payload["integration_targets"]} >= {
        "Jira",
        "Confluence",
        "Slack",
    }
    approved = client.post(
        f"/api/workflows/{payload['workflow_id']}/approve",
        json={
            "approver": "Demo operator",
            "decision": "approve_competitive_response",
            "artifact_decisions": {
                item["name"]: "packet" if item["risk"] == "high" else "owner_review"
                for item in payload["impacts"]
            },
        },
    )
    assert approved.status_code == 200
    assert approved.json()["approval"]["decision"] == "approve_competitive_response"


def test_custom_copilot_routing_keeps_reviewed_option_and_audit_reason() -> None:
    state = api.workflow_store.start_demo()
    copilot = fallback_copilot(state)
    state.agent_trace = {
        "decision_copilot": {
            **copilot.model_dump(),
            "policy_review": red_team_review(copilot, state).model_dump(),
        }
    }
    api.persist_workflow(state)
    option = copilot.options[0]
    custom = dict(option.artifact_decisions)
    custom["Renewal playbook"] = "owner_review"

    response = client.post(
        f"/api/workflows/{state.workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": option.workflow_decision,
            "artifact_decisions": custom,
            "copilot_option_id": option.option_id,
            "copilot_artifact_override": True,
            "copilot_override_reason": "Narrow renewal work to owner review",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval"]["copilot_option_id"] == option.option_id
    assert payload["approval"]["copilot_artifact_override"] is True
    assert payload["approval"]["copilot_override_reason"] == (
        "Narrow renewal work to owner review"
    )
    recorded = next(
        event for event in payload["events"] if event["outcome"] == "approval_recorded"
    )
    assert recorded["copilot_artifact_override"] is True
    assert recorded["override_reason"] == "Narrow renewal work to owner review"


def test_approved_action_item_can_be_claimed_and_completed_by_same_human() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    actions = approved.json()["action_items"]
    assert len(actions) == 4
    item_id = actions[0]["item_id"]

    claimed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    assert claimed.status_code == 200
    assert (
        next(
            item
            for item in claimed.json()["action_items"]
            if item["item_id"] == item_id
        )["status"]
        == "claimed"
    )

    wrong_actor = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Taylor Lee"},
    )
    assert wrong_actor.status_code == 409

    completed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )
    assert completed.status_code == 200
    assert (
        next(
            item
            for item in completed.json()["action_items"]
            if item["item_id"] == item_id
        )["status"]
        == "completed"
    )

    duplicate_complete = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )
    assert duplicate_complete.status_code == 200


def test_action_claim_is_idempotent_for_the_same_human() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]

    first = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    event_count = len(first.json()["events"])
    duplicate = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert len(duplicate.json()["events"]) == event_count
    assert duplicate.json()["action_items"][0]["attempts"] == 1


def test_failed_action_can_be_retried_and_repeated_retry_is_idempotent() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]
    claimed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    assert claimed.status_code == 200

    failed = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/fail",
        json={"actor": "Alex Kim", "reason": "Owner review timed out"},
    )
    assert failed.status_code == 200
    retried = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/retry",
        json={"actor": "Alex Kim"},
    )
    duplicate_retry = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/retry",
        json={"actor": "Alex Kim"},
    )

    assert retried.status_code == 200
    assert duplicate_retry.status_code == 200
    item = duplicate_retry.json()["action_items"][0]
    assert item["status"] == "queued"
    assert item["retry_count"] == 1


def test_completed_action_can_be_reversed_idempotently() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )
    item_id = approved.json()["action_items"][0]["item_id"]
    client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/claim",
        json={"actor": "Alex Kim"},
    )
    client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/complete",
        json={"actor": "Alex Kim"},
    )

    reversed_once = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/reverse",
        json={"actor": "Alex Kim"},
    )
    reversed_twice = client.post(
        f"/api/workflows/{workflow_id}/actions/{item_id}/reverse",
        json={"actor": "Alex Kim"},
    )

    assert reversed_once.status_code == 200
    assert reversed_twice.status_code == 200
    assert reversed_twice.json()["action_items"][0]["status"] == "reversed"


def test_live_agent_query_is_bounded_before_execution() -> None:
    response = client.post("/api/agent/run", json={"query": "x" * 2001})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_live_agent_route_binds_an_allowlisted_source(monkeypatch) -> None:
    captured: dict[str, str] = {}

    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        captured["query"] = query
        captured["user_id"] = user_id
        return {"status": "ok"}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post(
        "/api/agent/run",
        json={
            "query": "Inspect the pricing change",
            "user_id": "operator-1",
            "source_id": "public/pricing",
        },
    )

    assert response.status_code == 200
    assert captured["user_id"] == "operator-1"
    assert 'source_id "public/pricing"' in captured["query"]


@pytest.mark.asyncio
async def test_live_agent_route_propagates_signed_tenant(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_run_agent_task(
        query: str,
        user_id: str,
        run_mode: str = "demo",
        *,
        tenant_id: str | None = None,
    ) -> dict:
        captured.update(
            query=query,
            user_id=user_id,
            run_mode=run_mode,
            tenant_id=tenant_id,
        )
        return {"status": "ok", "tenant_id": tenant_id}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    monkeypatch.setenv("DRIFTLINE_SIGNED_APPROVALS_ENABLED", "true")
    secret = "agent-tenant-secret"
    tenant_id = "agent-tenant"
    operator = "Tenant operator"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    monkeypatch.setenv("DRIFTLINE_HMAC_TENANTS", tenant_id)
    token = hmac.new(
        secret.encode(),
        f"agent-run:public/pricing:{operator}".encode(),
        hashlib.sha256,
    ).hexdigest()
    with api._agent_call_lock:
        api._agent_call_times.clear()
        api._tenant_agent_call_times.clear()

    response = client.post(
        "/api/agent/run",
        json={
            "query": "Inspect the tenant source",
            "user_id": "tenant-operator",
            "source_id": "public/pricing",
            "operator": operator,
            "tenant_id": tenant_id,
            "approval_token": token,
        },
    )

    assert response.status_code == 200
    assert captured["tenant_id"] == tenant_id
    assert captured["run_mode"] == "live"
    assert 'source_id "public/pricing"' in str(captured["query"])


def test_live_agent_route_rejects_partial_signed_identity() -> None:
    response = client.post(
        "/api/agent/run",
        json={"query": "Inspect it", "tenant_id": "agent-tenant"},
    )
    assert response.status_code == 401


def test_live_agent_route_rejects_unallowlisted_source() -> None:
    response = client.post(
        "/api/agent/run",
        json={"query": "Inspect it", "source_id": "https://evil.example"},
    )
    assert response.status_code == 422


def test_packet_endpoint_is_available_after_approval() -> None:
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Demo operator",
            "decision": "grandfather_existing_customers",
        },
    )

    assert approved.status_code == 200
    packet = client.get(f"/api/workflows/{workflow_id}/packet")
    assert packet.status_code == 200
    assert "External systems changed: **No**" in packet.text


def test_async_job_records_agent_trace_and_workflow(monkeypatch) -> None:
    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        state = api.workflow_store.start_demo()
        return {
            "workflow_id": state.workflow_id,
            "model": "test-model",
            "execution_mode": "google_adk",
            "tool_calls": ["inspect_source_change", "get_workflow_state"],
            "event_count": 4,
            "response": "Evidence verified; waiting for a human decision.",
            "agent_trace": {"model": "test-model", "event_count": 4},
        }

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()

    response = client.post("/api/jobs/demo", json={"query": "test"})

    assert response.status_code == 200
    queued = response.json()
    payload = client.get(f"/api/jobs/{queued['job_id']}").json()
    assert payload["status"] == "needs_approval"
    assert payload["workflow"]["status"] == "needs_approval"
    assert payload["tool_calls"] == [
        "inspect_source_change",
        "get_workflow_state",
    ]
    assert payload["workflow"]["agent_trace"]["model"] == "test-model"

    workflow_id = payload["workflow_id"]
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Alex Kim",
            "decision": "grandfather_existing_customers",
        },
    )
    assert approved.status_code == 200
    assert client.get(f"/api/jobs/{queued['job_id']}").json()["status"] == "complete"


def test_identity_free_demo_mutations_are_rate_limited(monkeypatch) -> None:
    monkeypatch.setattr(api, "DEMO_MAX_MUTATIONS", 1)
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()

    first = client.post("/api/workflows/demo")
    second = client.post("/api/workflows/demo")

    assert first.status_code == 200
    assert second.status_code == 429
    with api._demo_mutation_lock:
        api._demo_mutation_times.clear()


@pytest.mark.asyncio
async def test_duplicate_job_delivery_cannot_run_agent_twice(monkeypatch) -> None:
    calls = 0

    async def fake_run_agent_task(query: str, user_id: str) -> dict:
        nonlocal calls
        calls += 1
        state = api.workflow_store.start_demo()
        return {"workflow_id": state.workflow_id, "model": "test-model"}

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    with api._agent_call_lock:
        api._agent_call_times.clear()
    job = JobState(job_id="job-idempotent", query="test")
    api._set_job(job)

    await api._run_job(job.job_id)
    await api._run_job(job.job_id)

    assert calls == 1
    assert api._resolve_job(job.job_id).run_attempts == 1


@pytest.mark.asyncio
async def test_monitor_job_completes_without_inventing_a_workflow(monkeypatch) -> None:
    async def fake_run_agent_task(query: str, user_id: str, run_mode: str) -> dict:
        assert run_mode == "monitor"
        return {
            "model": "test-model",
            "execution_mode": "google_adk",
            "tool_calls": ["inspect_source_change"],
            "event_count": 2,
            "response": "No material source change was found.",
            "source_status": "unchanged",
            "change_detected": False,
        }

    monkeypatch.setattr(api, "run_agent_task", fake_run_agent_task)
    job = JobState(job_id="job-monitor-unchanged", query="monitor", run_mode="monitor")
    api._set_job(job)

    await api._run_job(job.job_id)

    result = api._resolve_job(job.job_id)
    assert result.status == "complete"
    assert result.workflow_id is None
    assert result.response == "No material source change was found."


def test_approval_requires_explicit_signed_token_when_signed_mode_enabled(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "signed")
    tenant_state = api.workflow_store.start_demo(tenant_id="driftline-demo")
    api.persist_workflow(tenant_state)
    workflow_id = tenant_state.workflow_id

    rejected = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Alex Kim"},
    )
    assert rejected.status_code == 403

    secret = "test-only-secret"
    monkeypatch.setenv("DRIFTLINE_APPROVAL_SIGNING_SECRET", secret)
    token = hmac.new(
        secret.encode(), f"{workflow_id}:Alex Kim".encode(), hashlib.sha256
    ).hexdigest()
    approved = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={
            "approver": "Alex Kim",
            "approval_mode": "signed",
            "approval_token": token,
        },
    )
    assert approved.status_code == 200
    assert approved.json()["approval"]["approval_identity"]["mode"] == "signed"


def test_failed_workflow_cas_restores_pending_state(monkeypatch) -> None:
    monkeypatch.setenv("DRIFTLINE_APPROVAL_MODE", "demo")
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
    monkeypatch.setattr(api, "compare_and_set_workflow", lambda state, expected: False)

    response = client.post(
        f"/api/workflows/{workflow_id}/approve",
        json={"approver": "Demo operator"},
    )

    assert response.status_code == 409
    assert client.get(f"/api/workflows/{workflow_id}").json()["status"] == (
        "needs_approval"
    )
