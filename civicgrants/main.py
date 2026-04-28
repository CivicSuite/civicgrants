"""FastAPI runtime foundation for CivicGrants."""

from civiccore import __version__ as CIVICCORE_VERSION
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from civicgrants import __version__
from civicgrants.application_draft import draft_application_outline
from civicgrants.audit_file import build_audit_file_export
from civicgrants.compliance_calendar import build_compliance_calendar
from civicgrants.eligibility import match_grant_eligibility
from civicgrants.opportunity_triage import triage_opportunity
from civicgrants.public_ui import render_public_lookup_page


app = FastAPI(
    title="CivicGrants",
    version=__version__,
    description="Grant opportunity triage, eligibility, drafting, compliance, and audit-file support for CivicSuite.",
)


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
        "status": "grant support foundation",
        "message": (
            "CivicGrants package, API foundation, sample opportunity triage, eligibility matching, "
            "application outline helper, compliance calendar helper, audit-ready export checklist, "
            "and public UI foundation are online; live funder feeds, official eligibility decisions, "
            "legal advice, live LLM calls, submission portals, and grant system-of-record integrations "
            "are not implemented yet."
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
    result = triage_opportunity(
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
    result = build_compliance_calendar(
        award_name=request.award_name,
        reporting_frequency=request.reporting_frequency,
    )
    return result.__dict__


@app.post("/api/v1/civicgrants/export")
def audit_export(request: AuditFileRequest) -> dict[str, object]:
    result = build_audit_file_export(
        grant_id=request.grant_id,
        title=request.title,
        format=request.format,
    )
    return result.__dict__
