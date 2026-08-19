import pytest

from app import analysis
from app.workflow import DriftlineWorkflow


def _payload(state) -> dict:
    evidence_hash = state.evidence.evidence_hash
    artifacts = [
        {
            "name": "Pricing battlecard",
            "owner": "Product Marketing",
            "action": "Replace claim",
            "risk": "high",
            "detail": "Replace the retention claim with the verified term.",
            "proposed": "Enterprise: 365-day audit-log retention.",
            "evidence_hash": evidence_hash,
        },
        {
            "name": "Renewal playbook",
            "owner": "Customer Success",
            "action": "Add exception path",
            "risk": "high",
            "detail": "Document the transition for existing customers.",
            "proposed": "Grandfather existing customers through their next renewal.",
            "evidence_hash": evidence_hash,
        },
        {
            "name": "Enterprise FAQ",
            "owner": "Support",
            "action": "Revise retention answer",
            "risk": "medium",
            "detail": "Answer the retention question with the verified term.",
            "proposed": "Enterprise audit logs are retained for 365 days.",
            "evidence_hash": evidence_hash,
        },
        {
            "name": "CRM guidance",
            "owner": "RevOps",
            "action": "Update qualification note",
            "risk": "low",
            "detail": "Prompt a retention-expectation check during qualification.",
            "proposed": "Confirm retention expectations before positioning Enterprise.",
            "evidence_hash": evidence_hash,
        },
    ]
    return {
        "evidence_hash": evidence_hash,
        "summary": "Retention language changed and requires coordinated updates.",
        "rationale": "The source snapshot is hash-bound and affects four owned artifacts.",
        "artifacts": artifacts,
    }


def test_structured_output_is_evidence_bound_and_replaces_drafts() -> None:
    state = DriftlineWorkflow().start_demo()
    result = analysis.validate_analysis(_payload(state), state.evidence.evidence_hash)

    analysis.apply_analysis(state, result)

    assert state.impacts[0].proposed.startswith("Enterprise: 365-day")
    assert all(
        item.evidence_hash == state.evidence.evidence_hash for item in state.impacts
    )


def test_structured_output_rejects_unknown_artifact() -> None:
    state = DriftlineWorkflow().start_demo()
    payload = _payload(state)
    payload["artifacts"][0]["name"] = "Slack announcement"

    with pytest.raises(analysis.AnalysisUnavailable, match="unapproved artifact"):
        analysis.validate_analysis(payload, state.evidence.evidence_hash)


def test_structured_output_rejects_wrong_evidence_hash() -> None:
    state = DriftlineWorkflow().start_demo()
    payload = _payload(state)
    payload["artifacts"][0]["evidence_hash"] = "0" * 64

    with pytest.raises(analysis.AnalysisUnavailable, match="Artifact is not bound"):
        analysis.validate_analysis(payload, state.evidence.evidence_hash)


def test_competitor_analysis_uses_competitor_profile_allowlist() -> None:
    state = DriftlineWorkflow().start_demo(source_id="competitor/pricing")
    allowed = analysis._allowed_artifacts_for_state(state)
    evidence_hash = state.evidence.evidence_hash
    payload = {
        "evidence_hash": evidence_hash,
        "summary": "Competitor pricing moved and changes comparison work.",
        "rationale": "The observed price point affects current positioning.",
        "artifacts": [
            {
                "name": name,
                "owner": owner,
                "action": "Review observed change",
                "risk": "medium",
                "detail": "Evidence-bound competitive review.",
                "proposed": "Use the captured source and timestamp.",
                "evidence_hash": evidence_hash,
            }
            for name, owner in allowed.items()
        ],
    }

    result = analysis.validate_analysis(payload, evidence_hash, allowed)
    analysis.apply_analysis(state, result, allowed)

    assert {item.name for item in state.impacts} == set(allowed)


@pytest.mark.asyncio
async def test_analysis_turn_uses_model_payload_and_not_fixture(monkeypatch) -> None:
    state = DriftlineWorkflow().start_demo()
    payload = _payload(state)

    async def fake_events(prompt: str) -> list[str]:
        assert state.evidence.evidence_hash in prompt
        return [__import__("json").dumps(payload)]

    monkeypatch.setattr(analysis, "_run_analysis_events", fake_events)
    result = await analysis.analyze_workflow(state)

    assert result.summary.startswith("Retention language changed")
    assert state.impacts[1].action == "Add exception path"


@pytest.mark.asyncio
async def test_analysis_turn_accepts_fenced_json_but_not_unvalidated_prose(
    monkeypatch,
) -> None:
    state = DriftlineWorkflow().start_demo()
    payload = _payload(state)

    async def fake_events(prompt: str) -> list[str]:
        return [
            "Here is the contract:\n```json\n",
            __import__("json").dumps(payload),
            "\n```",
        ]

    monkeypatch.setattr(analysis, "_run_analysis_events", fake_events)
    result = await analysis.analyze_workflow(state)

    assert result.evidence_hash == state.evidence.evidence_hash


@pytest.mark.asyncio
async def test_analysis_turn_retries_transient_empty_response(monkeypatch) -> None:
    state = DriftlineWorkflow().start_demo()
    payload = _payload(state)
    calls = 0

    async def flaky_events(prompt: str) -> list[str]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return []
        return [__import__("json").dumps(payload)]

    monkeypatch.setattr(analysis, "_run_analysis_events", flaky_events)
    result = await analysis.analyze_workflow(state)

    assert calls == 2
    assert result.artifacts[-1].name == "CRM guidance"


@pytest.mark.asyncio
async def test_analysis_turn_handles_split_adk_text_events(monkeypatch) -> None:
    state = DriftlineWorkflow().start_demo()
    payload = __import__("json").dumps(_payload(state))

    async def split_events(prompt: str) -> list[str]:
        return ["analysis wrapper ", payload, payload]

    monkeypatch.setattr(analysis, "_run_analysis_events", split_events)
    result = await analysis.analyze_workflow(state)

    assert result.evidence_hash == state.evidence.evidence_hash
