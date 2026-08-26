from app.portfolio import build_decision_inbox
from app.workflow import DriftlineWorkflow


def test_portfolio_deduplicates_repeated_changes_and_links_commitments() -> None:
    workflow = DriftlineWorkflow()
    first = workflow.start_demo(source_id="competitor/pricing")
    repeated = workflow.start_demo(source_id="competitor/pricing")
    related = workflow.start_demo(source_id="competitor/offerings")

    inbox = build_decision_inbox([first, repeated, related])

    assert inbox["summary"]["decision_threads"] == 2
    assert inbox["summary"]["duplicate_observations_collapsed"] == 1
    assert inbox["counts"]["needs_decision"] == 2
    assert all(item["automation"]["external_writes"] is False for item in inbox["items"])
    assert any(item["related_decision_ids"] for item in inbox["items"])
    assert inbox["relationships"][0]["types"]
    assert inbox["commitment_health"][0]["state"] == "attention_required"
    assert {finding["kind"] for finding in inbox["findings"]} >= {
        "recurring_signal",
        "decision_dependency",
    }


def test_portfolio_keeps_closed_and_dismissed_work_quiet() -> None:
    workflow = DriftlineWorkflow()
    pending = workflow.start_demo(source_id="competitor/pricing")
    dismissed = workflow.start_demo(source_id="competitor/blog")
    dismissed = workflow.dismiss(
        dismissed.workflow_id,
        "Named reviewer",
        "Not material to an active commitment",
    )

    inbox = build_decision_inbox([pending, dismissed])

    assert inbox["summary"]["requires_attention"] == 1
    assert inbox["summary"]["monitoring_quietly"] == 1
    quiet = next(item for item in inbox["items"] if item["lane"] == "monitoring_normally")
    assert "Monitor quietly" in quiet["next_action"]


def test_portfolio_promotes_reopened_outcome_without_automating_the_pm() -> None:
    workflow = DriftlineWorkflow()
    state = workflow.start_demo(source_id="public/pricing")
    state.events.append({"outcome": "decision_reopened"})

    inbox = build_decision_inbox([state])
    item = inbox["items"][0]

    assert item["lane"] == "outcomes_to_review"
    assert item["automation"]["requires_human"].startswith("Approve")
    assert inbox["automation_boundary"]["external_writes"] is False


def test_empty_portfolio_makes_no_fixture_or_customer_claim() -> None:
    inbox = build_decision_inbox([])

    assert inbox["mode"] == "empty"
    assert inbox["items"] == []
    assert inbox["summary"]["requires_attention"] == 0
    assert inbox["findings"] == []
