import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app import api, source
from app.api import app
from app.models import JobState

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_monitor_registry_and_ops_summary_are_safe_for_operator_console() -> None:
    registry = client.get("/api/monitor/registry")
    assert registry.status_code == 200
    registry_payload = registry.json()
    assert registry_payload["append_only"] is True
    assert registry_payload["summary"]["total"] == 5
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

    value_proof = client.get("/api/ops/value-proof")
    assert value_proof.status_code == 200
    assert value_proof.json()["scope"] == "observed_driftline_sandbox_records"
    assert "willingness_to_pay" in value_proof.json()["not_measured"]
    assert "change_cards" in value_proof.json()["observed"]
    assert "high_materiality_cards" in value_proof.json()["observed"]
    assert "cards_dismissed" in value_proof.json()["observed"]
    assert "overdue_owner_actions" in value_proof.json()["observed"]
    outcomes = client.get("/api/ops/outcomes")
    assert outcomes.status_code == 200
    assert outcomes.json()["status"] == "not_measured"


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
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]
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
    started = client.post("/api/workflows/demo")
    workflow_id = started.json()["workflow_id"]

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
