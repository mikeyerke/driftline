#!/usr/bin/env python3
"""Summarize anonymized Driftline validation results without inventing claims."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path


REQUIRED_FIELDS = {
    "participant_id",
    "condition_order",
    "baseline_seconds",
    "driftline_seconds",
    "baseline_coverage_0_5",
    "driftline_coverage_0_5",
    "baseline_confidence_1_5",
    "driftline_confidence_1_5",
    "would_use_weekly",
    "recovery_understood",
    "human_control_understood",
    "moderator_hints",
    "protocol_deviation",
}


def _number(
    row: dict[str, str], key: str, *, minimum: float, maximum: float | None = None
) -> float:
    value = row.get(key, "").strip()
    if not value:
        raise ValueError(f"{row.get('participant_id', 'unknown')}: missing {key}")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{row.get('participant_id', 'unknown')}: invalid {key}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{row.get('participant_id', 'unknown')}: invalid {key}")
    return number


def _yes(row: dict[str, str], key: str) -> bool:
    value = row.get(key, "").strip().casefold()
    if value not in {"yes", "true", "1", "no", "false", "0"}:
        raise ValueError(f"{row.get('participant_id', 'unknown')}: invalid {key}")
    return value in {"yes", "true", "1"}


def summarize(rows: list[dict[str, str]]) -> str:
    complete = [
        row
        for row in rows
        if all(row.get(field, "").strip() for field in REQUIRED_FIELDS)
    ]
    if len(complete) < 6:
        return (
            "# Driftline validation summary\n\n"
            f"Status: **incomplete** ({len(complete)}/6 minimum participants).\n\n"
            "No win claim should be published yet.\n"
        )
    participant_ids = [row["participant_id"].strip() for row in complete]
    if len(set(participant_ids)) != len(participant_ids):
        return "# Driftline validation summary\n\nStatus: **invalid** (participant IDs must be unique).\n\nNo win claim should be published.\n"
    try:
        baseline_time = [
            _number(row, "baseline_seconds", minimum=0) for row in complete
        ]
        driftline_time = [
            _number(row, "driftline_seconds", minimum=0) for row in complete
        ]
        baseline_coverage = [
            _number(row, "baseline_coverage_0_5", minimum=0, maximum=5)
            for row in complete
        ]
        driftline_coverage = [
            _number(row, "driftline_coverage_0_5", minimum=0, maximum=5)
            for row in complete
        ]
        baseline_confidence = [
            _number(row, "baseline_confidence_1_5", minimum=1, maximum=5)
            for row in complete
        ]
        driftline_confidence = [
            _number(row, "driftline_confidence_1_5", minimum=1, maximum=5)
            for row in complete
        ]
        moderator_hints = [
            _number(row, "moderator_hints", minimum=0) for row in complete
        ]
        weekly = sum(_yes(row, "would_use_weekly") for row in complete)
        recovery = sum(_yes(row, "recovery_understood") for row in complete)
        human_control = sum(
            _yes(row, "human_control_understood") for row in complete
        )
        deviations = sum(_yes(row, "protocol_deviation") for row in complete)
    except (TypeError, ValueError) as exc:
        return f"# Driftline validation summary\n\nStatus: **invalid** ({exc}).\n\nNo win claim should be published.\n"
    baseline_median = statistics.median(baseline_time)
    driftline_median = statistics.median(driftline_time)
    time_improvement = (
        ((baseline_median - driftline_median) / baseline_median) * 100
        if baseline_median
        else 0
    )
    coverage_delta = statistics.median(driftline_coverage) - statistics.median(
        baseline_coverage
    )
    confidence_delta = statistics.median(driftline_confidence) - statistics.median(
        baseline_confidence
    )
    passed = (
        time_improvement >= 30
        and coverage_delta >= 1
        and weekly >= 5
        and human_control == len(complete)
    )
    return f"""# Driftline validation summary

Status: **{'thresholds met' if passed else 'thresholds not yet met'}** across {len(complete)} anonymized participants.

| Pre-registered measure | Observed |
| --- | ---: |
| Median manual task time | {baseline_median:.0f}s |
| Median Driftline task time | {driftline_median:.0f}s |
| Median time improvement | {time_improvement:.1f}% |
| Median coverage delta | {coverage_delta:+.1f} / 5 |
| Median confidence delta | {confidence_delta:+.1f} / 5 |
| Would use weekly | {weekly} / {len(complete)} |
| Understood recovery | {recovery} / {len(complete)} |
| Understood human-only control | {human_control} / {len(complete)} |
| Median moderator hints | {statistics.median(moderator_hints):.1f} |
| Protocol deviations | {deviations} |

Interpretation must account for protocol deviations and the small, directional sample. Do not present this as causal or statistically representative evidence.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with args.results.open(newline="", encoding="utf-8") as handle:
        report = summarize(list(csv.DictReader(handle)))
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
