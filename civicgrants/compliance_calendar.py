"""Compliance calendar helpers for CivicGrants v0.1.0."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComplianceCalendar:
    award_name: str
    reporting_frequency: str
    calendar_items: tuple[str, ...]
    staff_note: str


def build_compliance_calendar(*, award_name: str, reporting_frequency: str = "quarterly") -> ComplianceCalendar:
    """Build deterministic sample compliance milestones for staff review."""

    frequency = reporting_frequency.strip().casefold() or "quarterly"
    if frequency not in {"monthly", "quarterly", "annual"}:
        frequency = "quarterly"
    return ComplianceCalendar(
        award_name=award_name.strip() or "Untitled award",
        reporting_frequency=frequency,
        calendar_items=(
            "Record award agreement execution date.",
            f"Create {frequency} programmatic reporting reminders.",
            f"Create {frequency} financial reporting reminders.",
            "Schedule closeout package review before final reimbursement request.",
        ),
        staff_note="Staff must verify actual deadlines against the executed award agreement.",
    )
