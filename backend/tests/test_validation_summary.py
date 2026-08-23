import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "summarize_validation.py"
SPEC = importlib.util.spec_from_file_location("summarize_validation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
summarize = MODULE.summarize


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
            "protocol_deviation": "false",
        }
        for index in range(1, 7)
    ]
    report = summarize(rows)
    assert "thresholds met" in report
    assert "50.0%" in report
    assert "+2.0 / 5" in report
