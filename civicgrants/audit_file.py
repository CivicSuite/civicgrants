"""Audit-ready export helpers for CivicGrants v0.1.1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditFileExport:
    grant_id: str
    title: str
    format: str
    checklist: tuple[str, ...]
    retention_note: str


def build_audit_file_export(*, grant_id: str, title: str, format: str = "markdown") -> AuditFileExport:
    """Build a deterministic audit-file checklist for grant records."""

    return AuditFileExport(
        grant_id=grant_id.strip() or "unassigned-grant",
        title=title.strip() or "Untitled grant file",
        format=format,
        checklist=(
            "Preserve source opportunity notice and eligibility review notes.",
            "Preserve governing-body authorization and signer records.",
            "Preserve application drafts, final submission, award agreement, and budget.",
            "Preserve reporting calendar, submitted reports, reimbursements, and closeout documents.",
        ),
        retention_note="Keep grant records according to municipal retention schedule and award terms.",
    )
