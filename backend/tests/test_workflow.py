from app.agent import root_agent
from app.models import Stage, WorkflowStatus
from app.workflow import DriftlineWorkflow, PolicyViolation


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
        "published",
        "published",
        "owner_review",
        "scheduled",
    ]


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
