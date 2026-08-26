import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "summarize_real_pm_pilot.py"
SPEC = importlib.util.spec_from_file_location("summarize_real_pm_pilot", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_record() -> dict:
    return {
        "session_id": "RP01",
        "session_date": "2026-08-27",
        "app_release_sha": "a" * 40,
        "app_state": "unreleased_local_candidate",
        "participant_role": "fractional_product_leader",
        "company_stage": "seed",
        "decision_type": "segment",
        "decision_due_days": 14,
        "decision_authority": "owner",
        "plausible_option_count": 3,
        "meaningful_downside": True,
        "safe_redaction_confirmed": True,
        "evidence_input_count": 4,
        "before_confidence_1_7": 4,
        "after_confidence_1_7": 6,
        "minutes_to_brief": 18,
        "decision_effect": "sharpened",
        "citation_error_count": 0,
        "human_control_understood": True,
        "external_writes_none_understood": True,
        "adoption_blocker": "integration",
        "costly_commitments": ["second_live_decision"],
        "commercial_status": "none",
        "paid_amount_usd": 0,
        "public_anonymized_result_consent": False,
        "protocol_deviation": False,
        "review_window_days": 3,
        "outcome_followup": "pending",
        "threshold_verdict": "not_measured",
        "participant_agreed_threshold_application": False,
    }


def test_private_single_session_is_not_customer_or_public_proof() -> None:
    report = MODULE.summarize(valid_record())
    assert "qualified single-session evidence (n=1)" in report
    assert "not a customer" in report
    assert "Public claim gate: **blocked**" in report
    assert "No public pilot statement is authorized" in report
    assert "not causal or statistically representative" in report


def test_public_statement_discloses_unreleased_candidate_and_narrow_claim() -> None:
    record = valid_record()
    record["public_anonymized_result_consent"] = True
    report = MODULE.summarize(record)
    assert "approved for the bounded anonymized statement" in report
    assert "unreleased local candidate" in report
    assert "sharpened the decision" in report
    assert "stated confidence from 4 to 6" in report
    assert "ROI" in report


@pytest.mark.parametrize(
    ("key", "reason"),
    [
        ("human_control_understood", "human-authority boundary not understood"),
        ("external_writes_none_understood", "external-write boundary not understood"),
    ],
)
def test_public_statement_is_blocked_when_authority_is_misunderstood(
    key: str, reason: str
) -> None:
    record = valid_record()
    record["public_anonymized_result_consent"] = True
    record[key] = False
    report = MODULE.summarize(record)
    assert f"Public claim gate: **blocked** ({reason})" in report
    assert "No public pilot statement is authorized" in report


def test_public_statement_discloses_citation_errors() -> None:
    record = valid_record()
    record["public_anonymized_result_consent"] = True
    record["citation_error_count"] = 2
    assert "participant identified 2 citation errors" in MODULE.summarize(record)


@pytest.mark.parametrize(
    ("commercial_status", "commitment", "classification"),
    [
        ("signed_paid_pilot", "signed_paid_pilot", "signed paid-pilot customer evidence"),
        ("payment_received", "payment_received", "paid customer evidence"),
    ],
)
def test_customer_classification_requires_commercial_evidence(
    commercial_status: str, commitment: str, classification: str
) -> None:
    record = valid_record()
    record["commercial_status"] = commercial_status
    record["paid_amount_usd"] = 500
    record["costly_commitments"] = [commitment]
    assert classification in MODULE.summarize(record)


def test_paid_status_without_amount_or_matching_commitment_is_rejected() -> None:
    record = valid_record()
    record["commercial_status"] = "signed_paid_pilot"
    with pytest.raises(MODULE.PilotValidationError):
        MODULE.summarize(record)


def test_non_string_commitment_is_rejected_without_crashing() -> None:
    record = valid_record()
    record["costly_commitments"] = [{"raw": "forbidden"}]
    with pytest.raises(MODULE.PilotValidationError, match="unique list"):
        MODULE.summarize(record)


def test_identity_or_raw_data_fields_are_rejected() -> None:
    record = valid_record()
    record["participant_name"] = "Not Allowed"
    with pytest.raises(MODULE.PilotValidationError, match="unexpected fields"):
        MODULE.summarize(record)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("decision_due_days", 31),
        ("plausible_option_count", 1),
        ("evidence_input_count", 2),
        ("meaningful_downside", False),
        ("safe_redaction_confirmed", False),
    ],
)
def test_unqualified_session_is_rejected(key: str, value: object) -> None:
    record = valid_record()
    record[key] = value
    with pytest.raises(MODULE.PilotValidationError):
        MODULE.summarize(record)


def test_pending_followup_cannot_claim_outcome() -> None:
    record = valid_record()
    record["threshold_verdict"] = "validated"
    with pytest.raises(MODULE.PilotValidationError, match="pending follow-up"):
        MODULE.summarize(record)


def test_completed_followup_reports_threshold_result_without_roi_claim() -> None:
    record = valid_record()
    record["outcome_followup"] = "completed"
    record["threshold_verdict"] = "invalidated"
    record["participant_agreed_threshold_application"] = True
    report = MODULE.summarize(record)
    assert "precommitted threshold verdict: **invalidated**" in report
    assert "participant agreement: **yes**" in report
    assert "does not prove ROI" in report
