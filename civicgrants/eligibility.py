"""Grant eligibility matching helpers for CivicGrants v0.2.0."""

from __future__ import annotations

from dataclasses import dataclass

from civicgrants.opportunity_triage import DISCLAIMER, triage_opportunity


@dataclass(frozen=True)
class EligibilityMatch:
    opportunity_title: str
    status: str
    matched_factors: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    disclaimer: str = DISCLAIMER


def match_grant_eligibility(
    *,
    city_profile: str,
    opportunity_title: str,
    funding_area: str,
) -> EligibilityMatch:
    """Return sample eligibility factors; staff must verify official eligibility."""

    profile = city_profile.casefold()
    triage = triage_opportunity(opportunity_title=opportunity_title, funding_area=funding_area)
    matched: list[str] = []
    if "population" in profile:
        matched.append("Population profile supplied.")
    if "match" in profile or "local share" in profile:
        matched.append("Local match / cost-share context supplied.")
    if "plan" in profile or "capital" in profile:
        matched.append("Plan or capital-project alignment supplied.")
    unresolved = [
        "Confirm official applicant eligibility in the funder notice.",
        "Confirm authorized signer and governing-body approval path.",
    ]
    status = "needs-staff-verification" if matched else "insufficient-profile"
    return EligibilityMatch(
        opportunity_title=triage.opportunity_title,
        status=status,
        matched_factors=tuple(matched),
        unresolved_questions=tuple(unresolved),
    )
