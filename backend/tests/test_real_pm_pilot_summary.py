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
        "participant_independent": True,
        "participant_recruitment_channel": "organic_opt_in",
        "participant_incentive_usd": 0,
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
        "all_citations_reviewed": True,
        "human_control_understood": True,
        "external_writes_none_understood": True,
        "primary_decision_pain": "competing_priorities",
        "incumbent_decision_workflow": "meeting_or_chat_only",
        "adoption_blocker": "integration",
        "willingness_to_reuse": "yes",
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


def valid_starter(record: dict) -> dict:
    automated_fields = [
        "session_id",
        "session_date",
        "app_release_sha",
        "app_state",
        "plausible_option_count",
        "evidence_input_count",
        "review_window_days",
    ]
    starter_record = {
        key: value if key in automated_fields else None for key, value in record.items()
    }
    return {
        "schema_version": 1,
        "generated_at": "2026-08-27T15:30:00+00:00",
        "evidence_binding": {
            "case_reference_hash": "b" * 64,
            "release_sha": record["app_release_sha"],
            "generation": 2,
            "case_status": "approved",
            "evidence_manifest_hash": "c" * 64,
            "synthesis_hash": "d" * 64,
            "evidence_input_count": record["evidence_input_count"],
            "plausible_option_count": record["plausible_option_count"],
            "review_window_days": record["review_window_days"],
            "human_approval_present": True,
            "outcome_count": 0,
            "external_writes_none": True,
        },
        "record": starter_record,
        "automated_fields": automated_fields,
        "manual_fields": sorted(set(record) - set(automated_fields)),
        "disclosure": (
            "Private starter only. It contains no decision text, participant identity, "
            "customer data, consent, validation, or customer claim."
        ),
    }


def test_private_single_session_is_not_customer_or_public_proof() -> None:
    report = MODULE.summarize(valid_record())
    assert "qualified single-session evidence (n=1)" in report
    assert "not a customer" in report
    assert "Public claim gate: **blocked**" in report
    assert "No public pilot statement is authorized" in report
    assert "not causal or statistically representative" in report
    assert "Primary decision pain: **competing priorities**" in report
    assert "Incumbent decision workflow: **meeting or chat only**" in report
    assert "Stated willingness to reuse: **yes**" in report
    assert "weaker than an observed costly commitment" in report


def test_product_bound_starter_proves_machine_field_custody() -> None:
    record = valid_record()
    report = MODULE.summarize(record, valid_starter(record))
    assert "product-bound private starter verified" in report
    assert f"Private case reference SHA-256: `{'b' * 64}`" in report
    assert f"Evidence manifest SHA-256: `{'c' * 64}`" in report
    assert "Product-observed external writes: **none**" in report
    assert "human approval present: **yes**" in report


def test_product_bound_starter_rejects_changed_automated_field() -> None:
    record = valid_record()
    starter = valid_starter(record)
    record["evidence_input_count"] = 5
    with pytest.raises(MODULE.PilotValidationError, match="changed after export"):
        MODULE.summarize(record, starter)


def test_product_bound_starter_rejects_malformed_binding() -> None:
    record = valid_record()
    starter = valid_starter(record)
    starter["evidence_binding"]["synthesis_hash"] = "not-a-hash"
    with pytest.raises(MODULE.PilotValidationError, match="synthesis_hash"):
        MODULE.summarize(record, starter)


def test_manual_report_is_explicitly_weaker_custody() -> None:
    assert "manual record only; not product-bound" in MODULE.summarize(valid_record())


def test_public_statement_discloses_unreleased_candidate_and_narrow_claim() -> None:
    record = valid_record()
    record["public_anonymized_result_consent"] = True
    report = MODULE.summarize(record)
    assert "approved for the bounded anonymized statement" in report
    assert "unreleased local candidate" in report
    assert "sharpened the decision" in report
    assert "stated confidence from 4 to 6" in report
    assert "Participant independent of the build and judging: **yes**" in report
    assert "Every citation reviewed by the participant: **yes**" in report
    assert "ROI" in report


@pytest.mark.parametrize(
    ("key", "reason"),
    [
        ("human_control_understood", "human-authority boundary not understood"),
        ("external_writes_none_understood", "external-write boundary not understood"),
        ("participant_independent", "participant independence not confirmed"),
        ("all_citations_reviewed", "not every citation was reviewed"),
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
        (
            "signed_paid_pilot",
            "signed_paid_pilot",
            "signed paid-pilot customer evidence",
        ),
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


def test_paid_panel_discloses_incentive_as_evaluation_spend() -> None:
    record = valid_record()
    record["participant_recruitment_channel"] = "paid_research_panel"
    record["participant_incentive_usd"] = 100
    record["public_anonymized_result_consent"] = True
    report = MODULE.summarize(record)
    assert "Recruitment channel: **paid research panel**" in report
    assert "received a $100 research incentive" in report
    assert "evaluation spend, not customer revenue" in report


def test_paid_panel_without_incentive_amount_is_rejected() -> None:
    record = valid_record()
    record["participant_recruitment_channel"] = "paid_research_panel"
    with pytest.raises(MODULE.PilotValidationError, match="incentive amount"):
        MODULE.summarize(record)


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


def test_placeholder_release_sha_is_rejected() -> None:
    record = valid_record()
    record["app_release_sha"] = "0" * 40
    with pytest.raises(MODULE.PilotValidationError, match="placeholder"):
        MODULE.summarize(record)


@pytest.mark.parametrize(
    "key",
    [
        "primary_decision_pain",
        "incumbent_decision_workflow",
        "willingness_to_reuse",
    ],
)
def test_market_fit_fields_reject_unregistered_values(key: str) -> None:
    record = valid_record()
    record[key] = "unbounded_free_text"
    with pytest.raises(MODULE.PilotValidationError, match=f"invalid {key}"):
        MODULE.summarize(record)


@pytest.mark.parametrize(
    "key",
    [
        "decision_due_days",
        "plausible_option_count",
        "evidence_input_count",
        "before_confidence_1_7",
        "after_confidence_1_7",
        "citation_error_count",
        "review_window_days",
    ],
)
def test_count_and_scale_fields_reject_fractional_values(key: str) -> None:
    record = valid_record()
    record[key] = float(record[key]) + 0.5
    with pytest.raises(MODULE.PilotValidationError, match=f"invalid {key}"):
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
