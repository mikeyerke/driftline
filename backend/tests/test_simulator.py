from app.simulator import simulate_scenarios


def _impacts() -> list[dict[str, object]]:
    return [
        {
            "name": "Pricing battlecard",
            "owner": "Product Marketing",
            "risk": "high",
        },
        {"name": "CRM guidance", "owner": "RevOps", "risk": "low"},
    ]


def test_simulator_returns_three_no_write_counterfactuals() -> None:
    result = simulate_scenarios(
        _impacts(),
        "a" * 64,
        [{"system": "Jira", "external_write": False}],
    )

    assert [item["id"] for item in result["scenarios"]] == [
        "approve",
        "grandfather",
        "defer",
    ]
    assert result["external_writes"] is False
    assert all(item["evidence_hash"] == "a" * 64 for item in result["scenarios"])
    assert all(
        artifact["jira"]["external_write"] is False
        for scenario in result["scenarios"]
        for artifact in scenario["artifacts"]
    )


def test_simulator_outcomes_are_policy_distinct_and_deterministic() -> None:
    first = simulate_scenarios(_impacts(), None)
    second = simulate_scenarios(_impacts(), None)

    assert first == second
    outcomes = {
        scenario["id"]: [artifact["outcome"] for artifact in scenario["artifacts"]]
        for scenario in first["scenarios"]
    }
    assert outcomes["approve"] == ["packet_ready", "queued"]
    assert outcomes["grandfather"] == [
        "grandfathered_owner_review",
        "owner_review",
    ]
    assert outcomes["defer"] == ["deferred", "deferred"]
