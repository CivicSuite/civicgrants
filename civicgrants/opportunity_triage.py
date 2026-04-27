"""Deterministic grant opportunity triage helpers for CivicGrants v0.1.0."""

from __future__ import annotations

from dataclasses import dataclass


DISCLAIMER = (
    "CivicGrants provides grant-support drafts only. Staff own every decision; "
    "the module does not determine eligibility, submit applications, or replace the grant system of record."
)


@dataclass(frozen=True)
class OpportunityTriage:
    opportunity_title: str
    funding_area: str
    priority: str
    recommended_owner: str
    triage_notes: tuple[str, ...]
    disclaimer: str = DISCLAIMER


def triage_opportunity(*, opportunity_title: str, funding_area: str, deadline: str = "") -> OpportunityTriage:
    """Return deterministic sample triage without live funder-feed calls."""

    area = funding_area.strip().casefold()
    owner = "Administration / grants coordinator"
    if "water" in area or "storm" in area:
        owner = "Public Works"
    elif "park" in area or "trail" in area:
        owner = "Parks and Recreation"
    elif "housing" in area or "community" in area:
        owner = "Community Development"
    deadline_note = f"Confirm deadline: {deadline.strip()}." if deadline.strip() else "Confirm deadline in source notice."
    return OpportunityTriage(
        opportunity_title=opportunity_title.strip() or "Untitled opportunity",
        funding_area=funding_area.strip() or "general",
        priority="staff-review",
        recommended_owner=owner,
        triage_notes=(
            deadline_note,
            "Confirm match against adopted plans, capital plan, and staff capacity.",
            "Preserve source notice, eligibility notes, and reviewer decisions in the grant file.",
        ),
    )
