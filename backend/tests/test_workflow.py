import app.agent as agent_module
from app.agent import root_agent
from app.models import SourceEvidence, Stage, WorkflowStatus
from app.workflow import DriftlineWorkflow, PolicyViolation, packet_markdown


def test_demo_pauses_for_high_risk_human_decision() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()

    assert state.stage is Stage.AWAIT_APPROVAL
    assert state.status is WorkflowStatus.NEEDS_APPROVAL
    assert state.approval is None
    assert len(state.impacts) == 4
    assert state.evidence is not None
    assert len(state.evidence.evidence_hash) == 64


def test_named_approval_resumes_and_publishes_bounded_artifacts() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()
    result = workflow.approve(
        state.workflow_id,
        "Alex Kim",
        "grandfather_existing_customers",
    )

    assert result.stage is Stage.PUBLISH
    assert result.status is WorkflowStatus.COMPLETE
    assert result.approval["approver"] == "Alex Kim"
    assert [item.status for item in result.impacts] == [
        "packet_ready",
        "packet_ready",
        "owner_review",
        "queued",
    ]
    assert result.action_record["kind"] == "firestore_sandbox_packet"
    assert result.action_record["status"] == "active"
    assert result.action_record["external_systems_changed"] is False


def test_agent_cannot_self_approve_without_named_human() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()

    try:
        workflow.approve(
            state.workflow_id,
            "",
            "grandfather_existing_customers",
        )
    except PolicyViolation as exc:
        assert "human approver" in str(exc)
    else:
        raise AssertionError("Unnamed approval should be rejected")


def test_non_allowlisted_decision_is_rejected() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()

    try:
        workflow.approve(state.workflow_id, "Alex Kim", "publish_everything")
    except PolicyViolation as exc:
        assert "allowlisted" in str(exc)
    else:
        raise AssertionError("Unknown decision should be rejected")


def test_agent_tool_allowlist_has_no_approval_capability() -> None:
    tool_names = {getattr(tool, "__name__", "") for tool in root_agent.tools}
    assert tool_names == {"inspect_source_change", "get_workflow_state"}

    workflow = DriftlineWorkflow()
    state = workflow.start_demo()
    try:
        workflow.approve(
            state.workflow_id,
            "agent",
            "grandfather_existing_customers",
        )
    except PolicyViolation as exc:
        assert "cannot approve" in str(exc)
    else:
        raise AssertionError("Agent identity should never satisfy the human gate")


def test_undo_requires_a_recorded_human_decision() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()
    try:
        workflow.undo(state.workflow_id, "Demo operator")
    except PolicyViolation as exc:
        assert "no recorded human decision" in str(exc)
    else:
        raise AssertionError("A pending workflow should not have a decision to undo")

    workflow.approve(
        state.workflow_id,
        "Demo operator",
        "grandfather_existing_customers",
    )
    try:
        workflow.undo(state.workflow_id, "agent")
    except PolicyViolation as exc:
        assert "cannot approve or undo" in str(exc)
    else:
        raise AssertionError("An agent identity should not undo a human decision")


def test_approval_rejects_changed_evidence() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()
    state.evidence = SourceEvidence(
        source_id="public/pricing",
        source_name="Public pricing page",
        before="Changed before",
        after="Changed after",
        evidence_hash=state.evidence.evidence_hash,
        confidence=0.99,
        snapshot_label="Synthetic demo fixture · public/pricing",
    )
    try:
        workflow.approve(
            state.workflow_id,
            "Demo operator",
            "grandfather_existing_customers",
        )
    except PolicyViolation as exc:
        assert "Evidence hash" in str(exc)
    else:
        raise AssertionError("Approval must reject changed evidence")


def test_agent_source_tool_persists_the_created_workflow() -> None:
    persisted_ids: list[str] = []
    original_persist = agent_module.persist_workflow
    agent_module.persist_workflow = lambda state: persisted_ids.append(
        state.workflow_id
    )
    try:
        payload = agent_module.inspect_source_change("public/pricing")
    finally:
        agent_module.persist_workflow = original_persist

    assert payload["workflow_id"] in persisted_ids
    assert payload["data_mode"] == "synthetic_demo"


def test_agent_tenant_demo_is_explicitly_labeled_and_bound() -> None:
    persisted_ids: list[str] = []
    original_persist = agent_module.persist_workflow
    mode_token = agent_module.set_run_mode("tenant_demo")
    tenant_token = agent_module.set_tenant_id("driftline-demo")
    agent_module.persist_workflow = lambda state: persisted_ids.append(
        state.workflow_id
    )
    try:
        payload = agent_module.inspect_source_change("public/pricing")
        state = agent_module.workflow_store.get(payload["workflow_id"])
    finally:
        agent_module.persist_workflow = original_persist
        agent_module.reset_tenant_id(tenant_token)
        agent_module.reset_run_mode(mode_token)

    assert payload["workflow_id"] in persisted_ids
    assert payload["data_mode"] == "synthetic_tenant_demo"
    assert state.tenant_id == "driftline-demo"
    assert state.data_mode == "synthetic_tenant_demo"
    assert "Synthetic tenant replay fixture" in state.evidence.snapshot_label


def test_agent_resolves_placeholder_workflow_to_current_adk_turn() -> None:
    token = agent_module.set_workflow_id(None)
    try:
        payload = agent_module.inspect_source_change("public/pricing")
        resolved = agent_module.get_workflow_state("default")
    finally:
        agent_module.reset_workflow_id(token)

    assert resolved["workflow_id"] == payload["workflow_id"]


def test_approval_creates_evidence_bound_sandbox_packets() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()
    result = workflow.approve(
        state.workflow_id,
        "Alex Kim",
        "grandfather_existing_customers",
        {"Pricing battlecard": "packet", "Renewal playbook": "owner_review"},
    )

    assert len(result.artifact_packets) == 4
    assert result.artifact_packets[0]["status"] == "packet_ready"
    assert result.artifact_packets[1]["status"] == "owner_review"
    assert result.artifact_packets[0]["evidence_hash"] == result.evidence.evidence_hash
    packet_event_ids = {packet["event_id"] for packet in result.artifact_packets}
    assert len(packet_event_ids) == 4
    assert packet_event_ids.issubset({event["event_id"] for event in result.events})
    assert "External systems changed: **No**" in packet_markdown(result)
    packet = packet_markdown(result)
    assert "## Materiality and exposure" in packet
    assert "## Role packets" in packet
    assert "## Owner deadlines" in packet
    assert "not CRM data" in packet
    assert result.change_card["closure"]["state"] == "in_progress"


def test_reopen_is_not_claimed_as_external_undo() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()
    workflow.approve(state.workflow_id, "Alex Kim", "grandfather_existing_customers")
    reopened = workflow.undo(state.workflow_id, "Alex Kim")

    assert reopened.status is WorkflowStatus.NEEDS_APPROVAL
    assert reopened.artifact_packets == []
    assert reopened.action_record["status"] == "reversed"
    assert reopened.events[-1]["outcome"] == "decision_reopened"
