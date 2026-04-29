"""FastAPI runtime foundation for CivicGrants."""

import os

from civiccore import __version__ as CIVICCORE_VERSION
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from civicgrants import __version__
from civicgrants.application_draft import draft_application_outline
from civicgrants.audit_file import build_audit_file_export
from civicgrants.compliance_calendar import build_compliance_calendar
from civicgrants.eligibility import match_grant_eligibility
from civicgrants.opportunity_triage import triage_opportunity
from civicgrants.persistence import GrantRecordsRepository, StoredComplianceCalendar
from civicgrants.public_ui import render_public_lookup_page


app = FastAPI(
    title="CivicGrants",
    version=__version__,
    description="Grant opportunity triage, eligibility, drafting, compliance, and audit-file support for CivicSuite.",
)

_grant_repository: GrantRecordsRepository | None = None
_grant_db_url: str | None = None


class OpportunityTriageRequest(BaseModel):
    opportunity_title: str
    funding_area: str
    deadline: str = ""


class EligibilityRequest(BaseModel):
    city_profile: str
    opportunity_title: str
    funding_area: str


class ApplicationOutlineRequest(BaseModel):
    project_name: str
    opportunity_title: str
    city_need: str


class ComplianceCalendarRequest(BaseModel):
    award_name: str
    reporting_frequency: str = "quarterly"


class AuditFileRequest(BaseModel):
    grant_id: str
    title: str
    format: str = "markdown"


@app.get("/")
def root() -> dict[str, str]:
    """Return current product state without overstating unshipped behavior."""

    return {
        "name": "CivicGrants",
        "version": __version__,
        "status": "grant support foundation plus grant persistence",
        "message": (
            "CivicGrants package, API foundation, sample opportunity triage, eligibility matching, "
            "application outline helper, compliance calendar helper, optional database-backed grant "
            "opportunity and compliance records, audit-ready export checklist, and public UI foundation "
            "are online; live funder feeds, official eligibility decisions, legal advice, live LLM calls, "
            "submission portals, and grant system-of-record integrations are not implemented yet."
        ),
        "next_step": "Post-v0.1.1 roadmap: local grant catalog configuration, CivicRecords file links, and staff review queues",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Return dependency/version health for deployment smoke checks."""

    return {
        "status": "ok",
        "service": "civicgrants",
        "version": __version__,
        "civiccore_version": CIVICCORE_VERSION,
    }


@app.get("/civicgrants", response_class=HTMLResponse)
def public_civicgrants_page() -> str:
    """Return the public sample grant support UI."""

    return render_public_lookup_page()


@app.post("/api/v1/civicgrants/opportunities/triage")
def opportunity_triage(request: OpportunityTriageRequest) -> dict[str, object]:
    result = _triage_opportunity(
        opportunity_title=request.opportunity_title,
        funding_area=request.funding_area,
        deadline=request.deadline,
    )
    return result.__dict__


@app.post("/api/v1/civicgrants/eligibility/match")
def eligibility_match(request: EligibilityRequest) -> dict[str, object]:
    result = match_grant_eligibility(
        city_profile=request.city_profile,
        opportunity_title=request.opportunity_title,
        funding_area=request.funding_area,
    )
    return result.__dict__


@app.post("/api/v1/civicgrants/applications/outline")
def application_outline(request: ApplicationOutlineRequest) -> dict[str, object]:
    result = draft_application_outline(
        project_name=request.project_name,
        opportunity_title=request.opportunity_title,
        city_need=request.city_need,
    )
    return result.__dict__


@app.post("/api/v1/civicgrants/compliance/calendar")
def compliance_calendar(request: ComplianceCalendarRequest) -> dict[str, object]:
    if _grant_database_url() is not None:
        stored = _get_grant_repository().create_compliance_calendar(
            award_name=request.award_name,
            reporting_frequency=request.reporting_frequency,
        )
        return _stored_compliance_calendar_response(stored)

    result = build_compliance_calendar(
        award_name=request.award_name,
        reporting_frequency=request.reporting_frequency,
    )
    payload = result.__dict__
    payload["compliance_id"] = None
    return payload


@app.get("/api/v1/civicgrants/compliance/{compliance_id}")
def get_compliance_calendar(compliance_id: str) -> dict[str, object]:
    if _grant_database_url() is None:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "CivicGrants grant persistence is not configured.",
                "fix": "Set CIVICGRANTS_GRANT_DB_URL to retrieve persisted compliance calendar records.",
            },
        )
    stored = _get_grant_repository().get_compliance_calendar(compliance_id)
    if stored is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Compliance calendar record not found.",
                "fix": "Use a compliance_id returned by POST /api/v1/civicgrants/compliance/calendar.",
            },
        )
    return _stored_compliance_calendar_response(stored)


@app.post("/api/v1/civicgrants/export")
def audit_export(request: AuditFileRequest) -> dict[str, object]:
    result = build_audit_file_export(
        grant_id=request.grant_id,
        title=request.title,
        format=request.format,
    )
    return result.__dict__


def _grant_database_url() -> str | None:
    return os.environ.get("CIVICGRANTS_GRANT_DB_URL")


def _get_grant_repository() -> GrantRecordsRepository:
    global _grant_db_url, _grant_repository
    db_url = _grant_database_url()
    if db_url is None:
        raise RuntimeError("CIVICGRANTS_GRANT_DB_URL is not configured.")
    if _grant_repository is None or db_url != _grant_db_url:
        _dispose_grant_repository()
        _grant_db_url = db_url
        _grant_repository = GrantRecordsRepository(db_url=db_url)
    return _grant_repository


def _dispose_grant_repository() -> None:
    global _grant_repository
    if _grant_repository is not None:
        _grant_repository.engine.dispose()
        _grant_repository = None


def _triage_opportunity(*, opportunity_title: str, funding_area: str, deadline: str = ""):
    if _grant_database_url() is None:
        return triage_opportunity(
            opportunity_title=opportunity_title,
            funding_area=funding_area,
            deadline=deadline,
        )
    return _get_grant_repository().triage_opportunity(
        opportunity_title=opportunity_title,
        funding_area=funding_area,
        deadline=deadline,
    )


def _stored_compliance_calendar_response(stored: StoredComplianceCalendar) -> dict[str, object]:
    return {
        "compliance_id": stored.compliance_id,
        "award_name": stored.award_name,
        "reporting_frequency": stored.reporting_frequency,
        "calendar_items": list(stored.calendar_items),
        "staff_note": stored.staff_note,
        "created_at": stored.created_at.isoformat(),
    }
