from app.workflow import DriftlineWorkflow


def test_change_card_is_evidence_bound_and_labels_demo_exposure() -> None:
    state = DriftlineWorkflow().start_demo(source_id="competitor/pricing")
    card = state.change_card

    assert card["source"]["evidence_hash"] == state.evidence.evidence_hash
    assert card["materiality"]["severity"] == "high"
    assert card["materiality"]["score"] >= 80
    assert card["exposure"]["mode"] == "synthetic_demo"
    assert card["exposure"]["available"] is False
    assert "not CRM data" in card["exposure"]["label"]
    assert card["source_quality"]["evidence_type"] == "synthetic_fixture"
    assert card["source_quality"]["contradiction_status"] == "not_checked"
    assert {item["role"] for item in card["role_packets"]} >= {"PMM", "Sales / RevOps"}
    assert card["closure"]["state"] == "approval_pending"


def test_change_card_closure_tracks_completed_owner_work() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo()
    state = workflow.approve(
        state.workflow_id, "Named reviewer", "grandfather_existing_customers"
    )
    assert state.change_card["closure"]["state"] == "in_progress"
    assert state.change_card["closure"]["item_count"] == 4
    assert all(item["due_at"] for item in state.action_items)
    assert {item["priority"] for item in state.action_items} == {
        "high",
        "medium",
        "low",
    }

    for item in state.action_items:
        item["status"] = "completed"
    workflow._refresh_change_card(state)
    assert state.change_card["closure"]["state"] == "closed"
    assert state.change_card["closure"]["completion_rate"] == 1.0
