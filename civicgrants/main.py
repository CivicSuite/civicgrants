"""FastAPI runtime foundation for CivicGrants."""

import os
from typing import Annotated

from civiccore import __version__ as CIVICCORE_VERSION
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from civicgrants import __version__
from civicgrants.application_draft import draft_application_outline
from civicgrants.audit_file import build_audit_file_export
from civicgrants.compliance_calendar import build_compliance_calendar
from civicgrants.eligibility import match_grant_eligibility
from civicgrants.integration_mocks import validate_grant_context_mocks
from civicgrants.opportunity_triage import triage_opportunity
from civicgrants.persistence import (
    GrantRecordsRepository,
    StaffReviewQueueItem,
    StaffReviewSummary,
    StoredComplianceCalendar,
)
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
    grant_id: str | None = None


class ComplianceCalendarRequest(BaseModel):
    award_name: str
    reporting_frequency: str = "quarterly"


class AuditFileRequest(BaseModel):
    grant_id: str
    title: str
    format: str = "markdown"


class GrantContextRequest(BaseModel):
    grant_id: str
    opportunity_title: str
    records_context_id: str = ""
    grant_file_context_id: str = ""
    source_date_status: str = "current"


class IntegrationMockRequest(BaseModel):
    scenario: str = "grant-context"
    role: str = "staff"
    records_context_id: str = ""
    grant_file_context_id: str = ""
    official_eligibility: bool = False
    application_submitted: bool = False
    award_accepted: bool = False
    legal_advice: bool = False
    funder_feed_source: str = "local"
    source_date_status: str = "current"


class StaffReviewCreateRequest(BaseModel):
    opportunity_title: str
    reason: str
    grant_id: str | None = None


class StaffReviewUpdateRequest(BaseModel):
    status: str
    assigned_to: str | None = None
    resolution: str | None = None


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
            "opportunity and compliance records, staff review queues, review-required CivicRecords grant "
            "context packets, adversarial local integration mocks, audit-ready export checklist, and public "
            "UI foundation are online; live funder feeds, official eligibility decisions, legal advice, "
            "live LLM calls, submission portals, award acceptance, and grant system-of-record integrations "
            "are not implemented."
        ),
        "next_step": "Configure CIVICGRANTS_GRANT_DB_URL and CIVICGRANTS_STAFF_API_KEY before using staff queues.",
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
    if _grant_database_url() is not None:
        result = draft_application_outline(
            project_name=request.project_name,
            opportunity_title=request.opportunity_title,
            city_need=request.city_need,
        )
        staff_review = _get_grant_repository().create_staff_review_queue_item(
            opportunity_title=request.opportunity_title,
            grant_id=request.grant_id,
            reason="Grant application outline requires staff review before submission or award action.",
            created_by="staff",
        )
        payload = result.__dict__
        payload["staff_review_id"] = staff_review.review_id
        return payload

    result = draft_application_outline(
        project_name=request.project_name,
        opportunity_title=request.opportunity_title,
        city_need=request.city_need,
    )
    payload = result.__dict__
    payload["staff_review_id"] = None
    return payload


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


@app.post("/api/v1/civicgrants/context/grant-review")
def grant_review_context(request: GrantContextRequest) -> dict[str, object]:
    triage = _triage_opportunity(
        opportunity_title=request.opportunity_title,
        funding_area="general",
    )
    citations = [f"Grant triage context: {triage.recommended_owner}"]
    if request.records_context_id:
        citations.append(f"CivicRecords context: {request.records_context_id}")
    if request.grant_file_context_id:
        citations.append(f"Grant file context: {request.grant_file_context_id}")
    return {
        "grant_id": request.grant_id.strip() or "unassigned-grant",
        "opportunity_title": request.opportunity_title.strip() or "Untitled opportunity",
        "records_context_id": request.records_context_id,
        "grant_file_context_id": request.grant_file_context_id,
        "source_date_status": request.source_date_status,
        "citations": citations,
        "recommended_owner": triage.recommended_owner,
        "review_required": True,
        "boundary": (
            "CivicGrants provides grant review context only; it is not an official eligibility "
            "decision, legal opinion, application submission, award acceptance, live funder-feed "
            "result, or grant system-of-record action."
        ),
    }


@app.post("/api/v1/civicgrants/integrations/mock/grant-context")
def integration_mock_grant_context(request: IntegrationMockRequest) -> dict[str, object]:
    result = validate_grant_context_mocks(request.model_dump())
    return {
        "scenario": result.scenario,
        "status": result.status,
        "review_required": result.review_required,
        "findings": list(result.findings),
        "boundary": result.boundary,
    }


@app.post("/api/v1/civicgrants/export")
def audit_export(request: AuditFileRequest) -> dict[str, object]:
    result = build_audit_file_export(
        grant_id=request.grant_id,
        title=request.title,
        format=request.format,
    )
    return result.__dict__


@app.post("/api/v1/civicgrants/staff/reviews")
def create_staff_review(
    request: StaffReviewCreateRequest,
    x_civicgrants_role: Annotated[str | None, Header()] = None,
    x_civicgrants_staff_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    _require_persistence_configured()
    _require_staff_role(x_civicgrants_role, x_civicgrants_staff_key)
    item = _get_grant_repository().create_staff_review_queue_item(
        opportunity_title=request.opportunity_title,
        grant_id=request.grant_id,
        reason=request.reason,
        created_by=x_civicgrants_role or "staff",
    )
    return _staff_review_payload(item)


@app.get("/api/v1/civicgrants/staff/reviews")
def list_staff_reviews(
    status: str | None = None,
    x_civicgrants_role: Annotated[str | None, Header()] = None,
    x_civicgrants_staff_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    _require_persistence_configured()
    _require_staff_role(x_civicgrants_role, x_civicgrants_staff_key)
    return {
        "visibility": "staff_only",
        "items": [
            _staff_review_payload(item)
            for item in _get_grant_repository().list_staff_review_queue_items(status=status)
        ],
    }


@app.patch("/api/v1/civicgrants/staff/reviews/{review_id}")
def update_staff_review(
    review_id: str,
    request: StaffReviewUpdateRequest,
    x_civicgrants_role: Annotated[str | None, Header()] = None,
    x_civicgrants_staff_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    _require_persistence_configured()
    _require_staff_role(x_civicgrants_role, x_civicgrants_staff_key)
    try:
        item = _get_grant_repository().update_staff_review_queue_item(
            review_id=review_id,
            status=request.status,
            assigned_to=request.assigned_to,
            resolution=request.resolution,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "Staff review update is invalid.", "fix": str(exc)},
        ) from exc
    if item is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "CivicGrants staff review item was not found.",
                "fix": "List staff reviews and retry with an existing review_id.",
            },
        )
    return _staff_review_payload(item)


@app.get("/api/v1/civicgrants/staff/reviews/summary")
def staff_review_summary(
    x_civicgrants_role: Annotated[str | None, Header()] = None,
    x_civicgrants_staff_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    _require_persistence_configured()
    _require_staff_role(x_civicgrants_role, x_civicgrants_staff_key)
    return _staff_review_summary_payload(_get_grant_repository().staff_review_summary())


def _grant_database_url() -> str | None:
    return os.environ.get("CIVICGRANTS_GRANT_DB_URL")


def _staff_api_key() -> str | None:
    return os.environ.get("CIVICGRANTS_STAFF_API_KEY")


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


def _require_persistence_configured() -> None:
    if _grant_database_url() is None:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "CivicGrants staff review persistence is not configured.",
                "fix": "Set CIVICGRANTS_GRANT_DB_URL before using staff review queue routes.",
            },
        )


def _require_staff_role(role: str | None, staff_key: str | None) -> None:
    expected_key = _staff_api_key()
    if expected_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "CivicGrants staff API key is not configured.",
                "fix": "Set CIVICGRANTS_STAFF_API_KEY before using staff-only routes.",
            },
        )
    if role not in {"staff", "service"}:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Staff role required for this CivicGrants endpoint.",
                "fix": "Send X-CivicGrants-Role: staff or service from a trusted workflow.",
            },
        )
    if staff_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Valid CivicGrants staff key required.",
                "fix": "Send X-CivicGrants-Staff-Key with the configured staff API key.",
            },
        )


def _staff_review_payload(item: StaffReviewQueueItem) -> dict[str, object]:
    return {
        "review_id": item.review_id,
        "grant_id": item.grant_id,
        "opportunity_title": item.opportunity_title,
        "status": item.status,
        "reason": item.reason,
        "assigned_to": item.assigned_to,
        "resolution": item.resolution,
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "visibility": item.visibility,
        "boundary": (
            "Staff review queues support grant triage only; they do not determine eligibility, "
            "submit applications, accept awards, provide legal advice, or update a grant system of record."
        ),
    }


def _staff_review_summary_payload(summary: StaffReviewSummary) -> dict[str, object]:
    return {
        "total_items": summary.total_items,
        "by_status": summary.by_status,
        "open_items": summary.open_items,
        "generated_at": summary.generated_at.isoformat(),
        "visibility": summary.visibility,
    }
