#!/usr/bin/env python3
"""Turn one anonymized real-PM pilot record into bounded evidence claims."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


class PilotValidationError(ValueError):
    """Raised when a pilot record cannot support an evidence claim."""


REQUIRED_FIELDS = {
    "session_id",
    "session_date",
    "app_release_sha",
    "app_state",
    "participant_role",
    "participant_independent",
    "participant_recruitment_channel",
    "participant_incentive_usd",
    "company_stage",
    "decision_type",
    "decision_due_days",
    "decision_authority",
    "plausible_option_count",
    "meaningful_downside",
    "safe_redaction_confirmed",
    "evidence_input_count",
    "before_confidence_1_7",
    "after_confidence_1_7",
    "minutes_to_brief",
    "decision_effect",
    "citation_error_count",
    "all_citations_reviewed",
    "human_control_understood",
    "external_writes_none_understood",
    "primary_decision_pain",
    "incumbent_decision_workflow",
    "adoption_blocker",
    "willingness_to_reuse",
    "costly_commitments",
    "commercial_status",
    "paid_amount_usd",
    "public_anonymized_result_consent",
    "protocol_deviation",
    "review_window_days",
    "outcome_followup",
    "threshold_verdict",
    "participant_agreed_threshold_application",
}

ENUMS = {
    "app_state": {"unreleased_local_candidate", "verified_production"},
    "participant_role": {
        "product_manager",
        "product_leader",
        "founder_operator",
        "fractional_product_leader",
        "product_operations",
        "product_marketing",
    },
    "participant_recruitment_channel": {
        "organic_opt_in",
        "paid_research_panel",
        "existing_relationship",
        "referral",
    },
    "company_stage": {
        "pre_seed",
        "seed",
        "series_a",
        "series_b",
        "growth",
        "studio_or_consultancy",
    },
    "decision_type": {
        "rollout",
        "roadmap",
        "pricing",
        "packaging",
        "platform",
        "segment",
        "positioning",
        "resource_allocation",
    },
    "decision_authority": {"owner", "recommender"},
    "decision_effect": {"changed", "sharpened", "unchanged"},
    "adoption_blocker": {
        "none",
        "data_entry_burden",
        "trust",
        "integration",
        "workflow_fit",
        "security",
        "timing",
        "other",
    },
    "primary_decision_pain": {
        "competing_priorities",
        "stakeholder_alignment",
        "evidence_synthesis",
        "strategy_time",
        "impact_proof",
        "ai_output_trust",
        "slow_adoption_feedback",
        "other",
    },
    "incumbent_decision_workflow": {
        "meeting_or_chat_only",
        "spreadsheet_or_document",
        "roadmap_or_ticket_tool",
        "dedicated_product_tool",
        "no_repeatable_process",
        "other",
    },
    "willingness_to_reuse": {"yes", "no", "unsure"},
    "commercial_status": {"none", "signed_paid_pilot", "payment_received"},
    "outcome_followup": {"pending", "completed"},
    "threshold_verdict": {"not_measured", "validated", "invalidated", "inconclusive"},
}

COMMITMENTS = {
    "second_live_decision",
    "teammate_invited",
    "qualified_introduction",
    "price_conversation",
    "signed_paid_pilot",
    "payment_received",
}

LABELS = {
    "unreleased_local_candidate": "unreleased local candidate",
    "verified_production": "verified production release",
    "product_manager": "product manager",
    "product_leader": "product leader",
    "founder_operator": "founder-operator",
    "fractional_product_leader": "fractional product leader",
    "product_operations": "product-operations leader",
    "product_marketing": "product-marketing leader",
    "pre_seed": "pre-seed",
    "seed": "seed-stage",
    "series_a": "Series A",
    "series_b": "Series B",
    "growth": "growth-stage",
    "studio_or_consultancy": "studio or consultancy",
    "resource_allocation": "resource-allocation",
}

STARTER_FIELDS = {
    "schema_version",
    "generated_at",
    "evidence_binding",
    "record",
    "automated_fields",
    "manual_fields",
    "disclosure",
}
AUTOMATED_FIELDS = {
    "session_id",
    "session_date",
    "app_release_sha",
    "app_state",
    "plausible_option_count",
    "evidence_input_count",
    "review_window_days",
    "all_citations_reviewed",
}
BINDING_FIELDS = {
    "case_reference_hash",
    "release_sha",
    "generation",
    "case_status",
    "evidence_manifest_hash",
    "synthesis_hash",
    "evidence_input_count",
    "plausible_option_count",
    "review_window_days",
    "human_approval_present",
    "outcome_count",
    "external_writes_none",
    "cited_evidence_count",
    "reviewed_evidence_count",
    "all_citations_reviewed",
    "review_receipt_hash",
}
HASH_RE = re.compile(r"[0-9a-f]{64}")


def _enum(record: dict[str, Any], key: str) -> str:
    value = record[key]
    if not isinstance(value, str) or value not in ENUMS[key]:
        raise PilotValidationError(f"invalid {key}")
    return value


def _bool(record: dict[str, Any], key: str) -> bool:
    value = record[key]
    if not isinstance(value, bool):
        raise PilotValidationError(f"invalid {key}")
    return value


def _number(
    record: dict[str, Any], key: str, *, minimum: float, maximum: float
) -> float:
    value = record[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PilotValidationError(f"invalid {key}")
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise PilotValidationError(f"invalid {key}")
    return number


def _integer(record: dict[str, Any], key: str, *, minimum: int, maximum: int) -> int:
    value = record[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise PilotValidationError(f"invalid {key}")
    if not minimum <= value <= maximum:
        raise PilotValidationError(f"invalid {key}")
    return value


def validate(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - record.keys())
    unexpected = sorted(record.keys() - REQUIRED_FIELDS)
    if missing:
        raise PilotValidationError(f"missing fields: {', '.join(missing)}")
    if unexpected:
        raise PilotValidationError(
            "unexpected fields are forbidden to reduce identity/raw-data risk: "
            + ", ".join(unexpected)
        )

    if not re.fullmatch(r"RP[0-9]{2,4}", str(record["session_id"])):
        raise PilotValidationError("invalid anonymized session_id")
    try:
        dt.date.fromisoformat(str(record["session_date"]))
    except ValueError as exc:
        raise PilotValidationError("invalid session_date") from exc
    if not re.fullmatch(r"[0-9a-f]{40}", str(record["app_release_sha"])):
        raise PilotValidationError("app_release_sha must be a full commit")
    if record["app_release_sha"] == "0" * 40:
        raise PilotValidationError("app_release_sha must not be a placeholder")

    for key in ENUMS:
        _enum(record, key)
    for key in (
        "meaningful_downside",
        "safe_redaction_confirmed",
        "participant_independent",
        "all_citations_reviewed",
        "human_control_understood",
        "external_writes_none_understood",
        "public_anonymized_result_consent",
        "protocol_deviation",
        "participant_agreed_threshold_application",
    ):
        _bool(record, key)

    due_days = _integer(record, "decision_due_days", minimum=1, maximum=30)
    option_count = _integer(record, "plausible_option_count", minimum=2, maximum=10)
    evidence_count = _integer(record, "evidence_input_count", minimum=3, maximum=10)
    _integer(record, "before_confidence_1_7", minimum=1, maximum=7)
    _integer(record, "after_confidence_1_7", minimum=1, maximum=7)
    _number(record, "minutes_to_brief", minimum=1, maximum=120)
    _integer(record, "citation_error_count", minimum=0, maximum=100)
    review_window = _integer(record, "review_window_days", minimum=3, maximum=30)
    if review_window not in {3, 7, 14, 30}:
        raise PilotValidationError("review_window_days must be 3, 7, 14, or 30")
    if not record["meaningful_downside"] or not record["safe_redaction_confirmed"]:
        raise PilotValidationError(
            "session did not pass the real-decision qualification gate"
        )
    if due_days > 30 or option_count < 2 or evidence_count < 3:
        raise PilotValidationError(
            "session did not pass the real-decision qualification gate"
        )

    commitments = record["costly_commitments"]
    if not isinstance(commitments, list) or any(
        not isinstance(item, str) for item in commitments
    ):
        raise PilotValidationError("costly_commitments must be a unique list")
    if len(commitments) != len(set(commitments)):
        raise PilotValidationError("costly_commitments must be a unique list")
    if any(item not in COMMITMENTS for item in commitments):
        raise PilotValidationError("invalid costly_commitments")

    commercial_status = record["commercial_status"]
    amount = _number(record, "paid_amount_usd", minimum=0, maximum=100000)
    incentive = _number(record, "participant_incentive_usd", minimum=0, maximum=5000)
    if (
        record["participant_recruitment_channel"] == "paid_research_panel"
        and incentive <= 0
    ):
        raise PilotValidationError(
            "paid research panel requires the participant incentive amount"
        )
    if commercial_status == "none" and amount != 0:
        raise PilotValidationError("paid_amount_usd requires a paid commercial status")
    if commercial_status == "signed_paid_pilot" and (
        amount <= 0 or "signed_paid_pilot" not in commitments
    ):
        raise PilotValidationError(
            "signed paid pilot requires price and matching commitment"
        )
    if commercial_status == "payment_received" and (
        amount <= 0 or "payment_received" not in commitments
    ):
        raise PilotValidationError("payment requires amount and matching commitment")

    outcome = record["outcome_followup"]
    verdict = record["threshold_verdict"]
    threshold_agreement = record["participant_agreed_threshold_application"]
    if outcome == "pending" and (verdict != "not_measured" or threshold_agreement):
        raise PilotValidationError("pending follow-up cannot claim a measured outcome")
    if outcome == "completed" and verdict == "not_measured":
        raise PilotValidationError("completed follow-up requires a threshold verdict")


def validate_starter(starter: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    """Verify that product-observed fields survive private completion unchanged."""
    if set(starter) != STARTER_FIELDS or starter.get("schema_version") != 1:
        raise PilotValidationError("invalid product-bound starter structure")
    try:
        generated_at = dt.datetime.fromisoformat(str(starter["generated_at"]))
    except ValueError as exc:
        raise PilotValidationError("invalid starter generated_at") from exc
    if generated_at.tzinfo is None:
        raise PilotValidationError("starter generated_at must include a timezone")

    starter_record = starter.get("record")
    if not isinstance(starter_record, dict) or set(starter_record) != REQUIRED_FIELDS:
        raise PilotValidationError("invalid starter record fields")
    automated = starter.get("automated_fields")
    manual = starter.get("manual_fields")
    if (
        not isinstance(automated, list)
        or set(automated) != AUTOMATED_FIELDS
        or len(automated) != len(AUTOMATED_FIELDS)
        or not isinstance(manual, list)
        or set(manual) != REQUIRED_FIELDS - AUTOMATED_FIELDS
        or len(manual) != len(REQUIRED_FIELDS - AUTOMATED_FIELDS)
    ):
        raise PilotValidationError("invalid starter field custody partition")
    if any(starter_record[field] is not None for field in manual):
        raise PilotValidationError("starter must not prefill human-observed fields")
    for field in automated:
        if record[field] != starter_record[field]:
            raise PilotValidationError(
                f"product-bound field changed after export: {field}"
            )

    binding = starter.get("evidence_binding")
    if not isinstance(binding, dict) or set(binding) != BINDING_FIELDS:
        raise PilotValidationError("invalid starter evidence binding")
    for field in (
        "case_reference_hash",
        "evidence_manifest_hash",
        "synthesis_hash",
        "review_receipt_hash",
    ):
        if not isinstance(binding[field], str) or not HASH_RE.fullmatch(binding[field]):
            raise PilotValidationError(f"invalid starter {field}")
    if (
        not isinstance(binding["release_sha"], str)
        or not re.fullmatch(r"[0-9a-f]{40}", binding["release_sha"])
        or binding["release_sha"] == "0" * 40
    ):
        raise PilotValidationError("invalid starter release_sha")
    if binding["release_sha"] != record["app_release_sha"]:
        raise PilotValidationError("starter release binding does not match record")
    for field in (
        "evidence_input_count",
        "plausible_option_count",
        "review_window_days",
    ):
        if binding[field] != record[field]:
            raise PilotValidationError(f"starter binding mismatch: {field}")
    if (
        isinstance(binding["generation"], bool)
        or not isinstance(binding["generation"], int)
        or binding["generation"] < 1
    ):
        raise PilotValidationError("invalid starter generation")
    if not isinstance(binding["case_status"], str) or not binding["case_status"]:
        raise PilotValidationError("invalid starter case_status")
    if (
        isinstance(binding["outcome_count"], bool)
        or not isinstance(binding["outcome_count"], int)
        or binding["outcome_count"] < 0
    ):
        raise PilotValidationError("invalid starter outcome_count")
    if not isinstance(binding["human_approval_present"], bool):
        raise PilotValidationError("invalid starter human_approval_present")
    for field in ("cited_evidence_count", "reviewed_evidence_count"):
        if (
            isinstance(binding[field], bool)
            or not isinstance(binding[field], int)
            or binding[field] < 0
        ):
            raise PilotValidationError(f"invalid starter {field}")
    if binding["reviewed_evidence_count"] > binding["cited_evidence_count"]:
        raise PilotValidationError("starter review count exceeds cited evidence count")
    expected_all_reviewed = (
        binding["cited_evidence_count"] > 0
        and binding["reviewed_evidence_count"] == binding["cited_evidence_count"]
    )
    if (
        not isinstance(binding["all_citations_reviewed"], bool)
        or binding["all_citations_reviewed"] is not expected_all_reviewed
        or binding["all_citations_reviewed"] is not record["all_citations_reviewed"]
    ):
        raise PilotValidationError("starter citation review binding is inconsistent")
    if binding["external_writes_none"] is not True:
        raise PilotValidationError(
            "starter does not prove the external-writes-none boundary"
        )
    if (
        not isinstance(starter.get("disclosure"), str)
        or "no decision text" not in starter["disclosure"]
    ):
        raise PilotValidationError("invalid starter privacy disclosure")
    return binding


def summarize(record: dict[str, Any], starter: dict[str, Any] | None = None) -> str:
    validate(record)
    binding = validate_starter(starter, record) if starter is not None else None
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    record_hash = hashlib.sha256(canonical).hexdigest()

    role = LABELS.get(record["participant_role"], record["participant_role"])
    stage = LABELS.get(record["company_stage"], record["company_stage"])
    decision = LABELS.get(record["decision_type"], record["decision_type"])
    app_state = LABELS[record["app_state"]]
    commitments = record["costly_commitments"]
    recruitment_channel = record["participant_recruitment_channel"].replace("_", " ")
    primary_pain = record["primary_decision_pain"].replace("_", " ")
    incumbent_workflow = record["incumbent_decision_workflow"].replace("_", " ")

    if record["commercial_status"] == "payment_received":
        customer_status = (
            f"**paid customer evidence** (${record['paid_amount_usd']:.0f} received)"
        )
    elif record["commercial_status"] == "signed_paid_pilot":
        customer_status = f"**signed paid-pilot customer evidence** (${record['paid_amount_usd']:.0f} committed)"
    else:
        customer_status = "**not a customer** (no payment or signed paid commitment)"

    public_claim_blockers = []
    if not record["public_anonymized_result_consent"]:
        public_claim_blockers.append("no anonymized-result publication consent")
    if not record["participant_independent"]:
        public_claim_blockers.append("participant independence not confirmed")
    if not record["all_citations_reviewed"]:
        public_claim_blockers.append("not every citation was reviewed")
    if record["protocol_deviation"]:
        public_claim_blockers.append("protocol deviation")
    if not record["human_control_understood"]:
        public_claim_blockers.append("human-authority boundary not understood")
    if not record["external_writes_none_understood"]:
        public_claim_blockers.append("external-write boundary not understood")

    if not public_claim_blockers:
        public_status = "**approved for the bounded anonymized statement below**"
        public_statement = (
            f"One anonymized {role} at a {stage} company used Driftline's "
            f"{app_state} on a real {decision} decision due within "
            f"{record['decision_due_days']:.0f} days. In "
            f"{record['minutes_to_brief']:.0f} minutes from complete intake, "
            f"the workflow {record['decision_effect']} the decision and moved "
            f"stated confidence from {record['before_confidence_1_7']:.0f} to "
            f"{record['after_confidence_1_7']:.0f} on a 1–7 scale."
        )
        if record["citation_error_count"]:
            public_statement += (
                f" The participant identified {record['citation_error_count']:.0f} "
                "citation errors."
            )
        if record["participant_incentive_usd"]:
            public_statement += (
                f" The participant received a ${record['participant_incentive_usd']:.0f} "
                "research incentive; this was evaluation spend, not customer revenue."
            )
    else:
        public_status = f"**blocked** ({'; '.join(public_claim_blockers)})"
        public_statement = "No public pilot statement is authorized."

    if record["outcome_followup"] == "completed":
        outcome_status = (
            f"Completed; precommitted threshold verdict: "
            f"**{record['threshold_verdict']}**; participant agreement: "
            f"**{'yes' if record['participant_agreed_threshold_application'] else 'no'}**."
        )
    else:
        outcome_status = "Pending; no measured outcome claim is allowed."

    commitment_text = ", ".join(commitments) if commitments else "none"
    if binding:
        custody = f"""- Evidence custody: **product-bound private starter verified**
- Private case reference SHA-256: `{binding["case_reference_hash"]}`
- Evidence manifest SHA-256: `{binding["evidence_manifest_hash"]}`
- Synthesis SHA-256: `{binding["synthesis_hash"]}`
- Exported case state: generation {binding["generation"]}; status `{binding["case_status"]}`; human approval present: **{"yes" if binding["human_approval_present"] else "no"}**; recorded outcomes: {binding["outcome_count"]}
- Product-observed external writes: **none**"""
        custody += f"\n- Product-observed citation review: **{binding['reviewed_evidence_count']} of {binding['cited_evidence_count']}** cited sources; receipt `{binding['review_receipt_hash']}`"
    else:
        custody = "- Evidence custody: **manual record only; not product-bound**"

    return f"""# Driftline real-PM pilot evidence

Status: **qualified single-session evidence (n=1)**.

- Session: `{record["session_id"]}` on {record["session_date"]}
- Application custody: **{app_state}** at `{record["app_release_sha"]}`
{custody}
- Participant: anonymized {role}; {stage}; decision authority: {record["decision_authority"]}
- Participant independent of the build and judging: **{"yes" if record["participant_independent"] else "no"}**
- Recruitment channel: **{recruitment_channel}**; participant research incentive: **${record["participant_incentive_usd"]:.0f}**
- Decision: {decision}; due in {record["decision_due_days"]:.0f} days; {record["plausible_option_count"]:.0f} plausible options; {record["evidence_input_count"]:.0f} redacted evidence inputs
- Decision effect: **{record["decision_effect"]}**; confidence {record["before_confidence_1_7"]:.0f} → {record["after_confidence_1_7"]:.0f} / 7; {record["minutes_to_brief"]:.0f} minutes from complete intake
- Citation errors identified: {record["citation_error_count"]:.0f}
- Every citation reviewed by the participant: **{"yes" if record["all_citations_reviewed"] else "no"}**
- Human authority understood: **{"yes" if record["human_control_understood"] else "no"}**
- External-writes-none boundary understood: **{"yes" if record["external_writes_none_understood"] else "no"}**
- Primary decision pain: **{primary_pain}**
- Incumbent decision workflow: **{incumbent_workflow}**
- Largest adoption blocker: {record["adoption_blocker"]}
- Stated willingness to reuse: **{record["willingness_to_reuse"]}**
- Costly commitments observed: {commitment_text}
- Commercial classification: {customer_status}
- Outcome follow-up: {outcome_status}
- Public claim gate: {public_status}
- Canonical record SHA-256: `{record_hash}`

## Bounded public statement

{public_statement}

## Interpretation boundary

This is one directional, self-reported session—not causal or statistically representative evidence. It does not prove ROI, revenue, retention, time saved across users, or product-market fit. Stated willingness to reuse is weaker than an observed costly commitment and cannot support a customer claim. A decision effect is not a measured business outcome. Recruiting fees and participant incentives are evaluation spend, never customer revenue. Customer status requires the commercial evidence shown above.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument(
        "--starter",
        type=Path,
        help="private starter exported by the originating Decision Twin browser",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise PilotValidationError("record must be a JSON object")
        starter = None
        if args.starter:
            starter = json.loads(args.starter.read_text(encoding="utf-8"))
            if not isinstance(starter, dict):
                raise PilotValidationError("starter must be a JSON object")
        report = summarize(record, starter)
    except (json.JSONDecodeError, OSError, PilotValidationError) as exc:
        raise SystemExit(f"Real-PM pilot record rejected: {exc}") from exc
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
