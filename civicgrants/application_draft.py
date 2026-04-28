"""Grant application outline helpers for CivicGrants v0.1.1."""

from __future__ import annotations

from dataclasses import dataclass

from civicgrants.opportunity_triage import DISCLAIMER


@dataclass(frozen=True)
class ApplicationOutline:
    project_name: str
    heading: str
    narrative_sections: tuple[str, ...]
    staff_review_required: bool
    disclaimer: str = DISCLAIMER


def draft_application_outline(
    *,
    project_name: str,
    opportunity_title: str,
    city_need: str,
) -> ApplicationOutline:
    """Create a deterministic application outline without drafting final submission text."""

    clean_project = project_name.strip() or "Untitled grant project"
    clean_opportunity = opportunity_title.strip() or "Untitled opportunity"
    need = city_need.strip() or "Need statement must be supplied by staff."
    return ApplicationOutline(
        project_name=clean_project,
        heading=f"Draft application outline for {clean_project}",
        narrative_sections=(
            f"Opportunity fit: {clean_opportunity}.",
            f"Need statement source: {need}",
            "Project scope and work plan.",
            "Budget, match, and sustainability plan.",
            "Performance measures and reporting approach.",
        ),
        staff_review_required=True,
    )
