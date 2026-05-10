"""Adversarial local integration contracts for CivicGrants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntegrationMockResult:
    scenario: str
    status: str
    review_required: bool
    findings: tuple[str, ...]
    boundary: str


def validate_grant_context_mocks(payload: dict[str, Any]) -> IntegrationMockResult:
    """Validate local CivicRecords/grant context payloads without external calls."""

    findings: list[str] = []
    scenario = str(payload.get("scenario", "grant-context"))

    if payload.get("role") not in {"staff", "service"}:
        findings.append("Rejected grant context without trusted staff or service role.")
    if not payload.get("records_context_id"):
        findings.append("Missing CivicRecords context ID; preserve the source grant file before drafting.")
    if not payload.get("grant_file_context_id"):
        findings.append("Missing grant file context ID; confirm the local grant file before review.")
    if payload.get("official_eligibility") is True:
        findings.append("Rejected attempted official eligibility determination in integration context.")
    if payload.get("application_submitted") is True:
        findings.append("Rejected attempted grant application submission in integration context.")
    if payload.get("award_accepted") is True:
        findings.append("Rejected attempted grant award acceptance in integration context.")
    if payload.get("legal_advice") is True:
        findings.append("Rejected legal-advice claim in grant integration context.")
    if payload.get("funder_feed_source") == "live":
        findings.append("Rejected live funder-feed claim; v1.0.0 uses local deterministic context only.")
    if payload.get("source_date_status") == "stale":
        findings.append("Stale records/grant context requires staff refresh before application drafting.")

    status = "ready-for-staff-review" if not findings else "blocked-for-staff-review"
    return IntegrationMockResult(
        scenario=scenario,
        status=status,
        review_required=True,
        findings=tuple(findings),
        boundary=(
            "CivicGrants validates local integration context only; it does not call live "
            "CivicRecords, funder feeds, LLM, submission portal, legal, award, or grant "
            "system-of-record services in v1.0.0."
        ),
    )
