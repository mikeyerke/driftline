"""Privacy-bounded evidence export for a real-PM Decision Twin session."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from .decision_twin import DecisionCase, evidence_review_status

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class PilotEvidenceError(ValueError):
    """Raised when a decision cannot produce a trustworthy pilot starter."""


def _is_pm_intake(case: DecisionCase) -> bool:
    return any(
        event.get("source_mode") == "pm_provided_unverified" for event in case.events
    )


def build_pilot_evidence_starter(
    case: DecisionCase,
    *,
    release_sha: str,
    verified_production: bool,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Bind machine-observed session facts without exporting PM text or identity."""
    if not _is_pm_intake(case):
        raise PilotEvidenceError(
            "pilot evidence export requires a PM-provided decision"
        )
    if not SHA_RE.fullmatch(release_sha) or release_sha == "0" * 40:
        raise PilotEvidenceError("pilot evidence export requires an exact release SHA")
    if case.measurement_contract is None:
        raise PilotEvidenceError(
            "pilot evidence export requires a measurement contract"
        )

    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC)
    case_hash = hashlib.sha256(case.case_id.encode()).hexdigest()
    session_number = int(case_hash[:8], 16) % 10_000
    source_count = max(0, len(case.evidence_nodes) - 1)
    option_count = len(case.council.options)
    review_days = case.measurement_contract.review_days
    external_writes_none = all(
        record.external_write is False for record in case.action_records
    )
    review_status = evidence_review_status(case)

    automated_fields = [
        "session_id",
        "session_date",
        "app_release_sha",
        "app_state",
        "plausible_option_count",
        "evidence_input_count",
        "review_window_days",
        "all_citations_reviewed",
    ]
    record: dict[str, Any] = {
        "session_id": f"RP{session_number:04d}",
        "session_date": timestamp.date().isoformat(),
        "app_release_sha": release_sha,
        "app_state": (
            "verified_production"
            if verified_production
            else "unreleased_local_candidate"
        ),
        "participant_role": None,
        "participant_independent": None,
        "participant_recruitment_channel": None,
        "participant_incentive_usd": None,
        "company_stage": None,
        "decision_type": None,
        "decision_due_days": None,
        "decision_authority": None,
        "plausible_option_count": option_count,
        "meaningful_downside": None,
        "safe_redaction_confirmed": None,
        "evidence_input_count": source_count,
        "before_confidence_1_7": None,
        "after_confidence_1_7": None,
        "minutes_to_brief": None,
        "decision_effect": None,
        "citation_error_count": None,
        "all_citations_reviewed": review_status["all_citations_reviewed"],
        "human_control_understood": None,
        "external_writes_none_understood": None,
        "primary_decision_pain": None,
        "incumbent_decision_workflow": None,
        "adoption_blocker": None,
        "willingness_to_reuse": None,
        "costly_commitments": None,
        "commercial_status": None,
        "paid_amount_usd": None,
        "public_anonymized_result_consent": None,
        "protocol_deviation": None,
        "review_window_days": review_days,
        "outcome_followup": None,
        "threshold_verdict": None,
        "participant_agreed_threshold_application": None,
    }
    manual_fields = sorted(set(record) - set(automated_fields))
    return {
        "schema_version": 1,
        "generated_at": timestamp.isoformat(),
        "evidence_binding": {
            "case_reference_hash": case_hash,
            "release_sha": release_sha,
            "generation": case.generation,
            "case_status": case.status,
            "evidence_manifest_hash": case.council.evidence_manifest_hash,
            "synthesis_hash": case.council.synthesis_hash,
            "evidence_input_count": source_count,
            "plausible_option_count": option_count,
            "review_window_days": review_days,
            "human_approval_present": case.approval is not None,
            "outcome_count": len(case.outcomes),
            "external_writes_none": external_writes_none,
            "cited_evidence_count": review_status["cited_evidence_count"],
            "reviewed_evidence_count": review_status["reviewed_evidence_count"],
            "all_citations_reviewed": review_status["all_citations_reviewed"],
            "review_receipt_hash": review_status["review_receipt_hash"],
        },
        "record": record,
        "automated_fields": automated_fields,
        "manual_fields": manual_fields,
        "disclosure": (
            "Private starter only. It contains no decision text, participant identity, "
            "customer data, consent, validation, or customer claim. A human must complete "
            "every manual field from the qualified session before summarization."
        ),
    }
