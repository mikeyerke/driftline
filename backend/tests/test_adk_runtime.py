import pytest

from app import adk_runtime
from app.analysis import AnalysisUnavailable


def test_structured_analysis_fallback_is_explicitly_demo_only() -> None:
    result = adk_runtime._analysis_failure_result(
        run_mode="demo",
        reason="Gemini returned no structured analysis",
        artifact_count=4,
    )

    assert result == {
        "mode": "deterministic_demo_fallback",
        "reason": "Gemini returned no structured analysis",
        "artifact_count": 4,
    }


@pytest.mark.parametrize("run_mode", ["monitor", "live", "production"])
def test_structured_analysis_failure_fails_closed_for_live_modes(run_mode: str) -> None:
    with pytest.raises(AnalysisUnavailable, match="Gemini unavailable"):
        adk_runtime._analysis_failure_result(
            run_mode=run_mode,
            reason="Gemini unavailable",
            artifact_count=4,
        )
