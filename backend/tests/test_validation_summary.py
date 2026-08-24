import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "summarize_validation.py"
SPEC = importlib.util.spec_from_file_location("summarize_validation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
summarize = MODULE.summarize


def _condition_order(participant_number: int) -> str:
    return "manual_first" if participant_number % 2 else "driftline_first"


def test_validation_summary_refuses_to_claim_small_sample() -> None:
    report = summarize([{"participant_id": "P01"}])
    assert "incomplete" in report
    assert "No win claim" in report


def test_validation_summary_calculates_preregistered_thresholds() -> None:
    rows = [
        {
            "participant_id": f"P{index:02d}",
            "baseline_seconds": "600",
            "driftline_seconds": "300",
            "baseline_coverage_0_5": "3",
            "driftline_coverage_0_5": "5",
            "baseline_confidence_1_5": "3",
            "driftline_confidence_1_5": "4",
            "would_use_weekly": "yes",
            "recovery_understood": "yes",
            "human_control_understood": "yes",
            "moderator_hints": "0",
            "condition_order": _condition_order(index),
            "protocol_deviation": "false",
        }
        for index in range(1, 7)
    ]
    report = summarize(rows)
    assert "thresholds met" in report
    assert "50.0%" in report
    assert "+2.0 / 5" in report


def test_validation_summary_treats_partial_rows_as_incomplete() -> None:
    rows = [{"participant_id": f"P{index:02d}"} for index in range(1, 7)]
    assert "incomplete" in summarize(rows)


def test_validation_summary_rejects_duplicates_and_out_of_range_values() -> None:
    base = {
        "participant_id": "P01",
        "condition_order": "manual_first",
        "baseline_seconds": "600",
        "driftline_seconds": "300",
        "baseline_coverage_0_5": "3",
        "driftline_coverage_0_5": "5",
        "baseline_confidence_1_5": "3",
        "driftline_confidence_1_5": "4",
        "would_use_weekly": "yes",
        "recovery_understood": "yes",
        "human_control_understood": "yes",
        "moderator_hints": "0",
        "protocol_deviation": "false",
    }
    assert "invalid" in summarize([dict(base) for _ in range(6)])
    rows = [dict(base, participant_id=f"P{index:02d}") for index in range(1, 7)]
    rows[0]["driftline_coverage_0_5"] = "6"
    assert "invalid" in summarize(rows)


def test_validation_summary_requires_human_control_comprehension() -> None:
    rows = [
        {
            "participant_id": f"P{index:02d}",
            "condition_order": _condition_order(index),
            "baseline_seconds": "600",
            "driftline_seconds": "300",
            "baseline_coverage_0_5": "3",
            "driftline_coverage_0_5": "5",
            "baseline_confidence_1_5": "3",
            "driftline_confidence_1_5": "4",
            "would_use_weekly": "yes",
            "recovery_understood": "yes",
            "human_control_understood": "no" if index == 1 else "yes",
            "moderator_hints": "0",
            "protocol_deviation": "false",
        }
        for index in range(1, 7)
    ]
    assert "thresholds not yet met" in summarize(rows)


def test_validation_summary_rejects_noncanonical_condition_order() -> None:
    rows = [
        {
            "participant_id": f"P{index:02d}",
            "condition_order": "alternating",
            "baseline_seconds": "600",
            "driftline_seconds": "300",
            "baseline_coverage_0_5": "3",
            "driftline_coverage_0_5": "5",
            "baseline_confidence_1_5": "3",
            "driftline_confidence_1_5": "4",
            "would_use_weekly": "yes",
            "recovery_understood": "yes",
            "human_control_understood": "yes",
            "moderator_hints": "0",
            "protocol_deviation": "false",
        }
        for index in range(1, 7)
    ]

    report = summarize(rows)

    assert "invalid" in report
    assert "condition_order" in report
    assert "thresholds met" not in report


def test_validation_summary_rejects_order_mismatched_to_participant() -> None:
    rows = [
        {
            "participant_id": f"P{index:02d}",
            "condition_order": _condition_order(index),
            "baseline_seconds": "600",
            "driftline_seconds": "300",
            "baseline_coverage_0_5": "3",
            "driftline_coverage_0_5": "5",
            "baseline_confidence_1_5": "3",
            "driftline_confidence_1_5": "4",
            "would_use_weekly": "yes",
            "recovery_understood": "yes",
            "human_control_understood": "yes",
            "moderator_hints": "0",
            "protocol_deviation": "false",
        }
        for index in range(1, 7)
    ]
    rows[0]["condition_order"] = "driftline_first"

    report = summarize(rows)

    assert "invalid" in report
    assert "condition_order" in report
    assert "P01" in report
    assert "thresholds met" not in report
