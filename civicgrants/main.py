"""FastAPI runtime foundation for CivicGrants."""

import os

from civiccore import __version__ as CIVICCORE_VERSION
from civiccore.auth import staff_key_gate
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

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
_require_staff_key = staff_key_gate("CIVICGRANTS_STAFF_API_KEY", "X-CivicGrants-Staff-Key")


class OpportunityTriageRequest(BaseModel):
    opportunity_title: str = Field(..., min_length=1, max_length=500)
    funding_area: str = Field(..., min_length=1, max_length=255)
    deadline: str = Field(default="", max_length=120)


class EligibilityRequest(BaseModel):
    city_profile: str = Field(..., min_length=1, max_length=8000)
    opportunity_title: str = Field(..., min_length=1, max_length=500)
    funding_area: str = Field(..., min_length=1, max_length=255)


class ApplicationOutlineRequest(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=500)
    opportunity_title: str = Field(..., min_length=1, max_length=500)
    city_need: str = Field(..., min_length=1, max_length=8000)
    grant_id: str | None = Field(default=None, max_length=255)


class ComplianceCalendarRequest(BaseModel):
    award_name: str = Field(..., min_length=1, max_length=500)
    reporting_frequency: str = Field(default="quarterly", max_length=120)


class AuditFileRequest(BaseModel):
    grant_id: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    format: str = Field(default="markdown", max_length=40)


class GrantContextRequest(BaseModel):
    grant_id: str = Field(..., min_length=1, max_length=255)
    opportunity_title: str = Field(..., min_length=1, max_length=500)
    records_context_id: str = Field(default="", max_length=255)
    grant_file_context_id: str = Field(default="", max_length=255)
    source_date_status: str = Field(default="current", max_length=80)


class IntegrationMockRequest(BaseModel):
    scenario: str = Field(default="grant-context", max_length=160)
    role: str = Field(default="staff", max_length=80)
    records_context_id: str = Field(default="", max_length=255)
    grant_file_context_id: str = Field(default="", max_length=255)
    official_eligibility: bool = False
    application_submitted: bool = False
    award_accepted: bool = False
    legal_advice: bool = False
    funder_feed_source: str = Field(default="local", max_length=160)
    source_date_status: str = Field(default="current", max_length=80)


class StaffReviewCreateRequest(BaseModel):
    opportunity_title: str = Field(..., min_length=1, max_length=500)
    reason: str = Field(..., min_length=1, max_length=1000)
    grant_id: str | None = Field(default=None, max_length=255)


class StaffReviewUpdateRequest(BaseModel):
    status: str = Field(..., min_length=1, max_length=120)
    assigned_to: str | None = Field(default=None, max_length=255)
    resolution: str | None = Field(default=None, max_length=2000)


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
            "UI foundation are online with readiness checks; live funder feeds, official eligibility "
            "decisions, legal advice, live LLM calls, submission portals, award acceptance, and grant "
            "system-of-record integrations are not implemented."
        ),
        "next_step": (
            "Configure CIVICGRANTS_GRANT_DB_URL, import local grant opportunities, and verify "
            "/ready before public use."
        ),
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


@app.get("/ready")
def ready() -> dict[str, object]:
    """Return public-use readiness without treating sample fallback as customer data."""

    return _readiness_payload()


@app.get("/api/v1/civicgrants/readiness")
def readiness() -> dict[str, object]:
    """Return detailed CivicGrants local-data readiness for installers and operators."""

    return _readiness_payload()


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
    _staff_principal: object = Depends(_require_staff_key),
) -> dict[str, object]:
    _require_persistence_configured()
    item = _get_grant_repository().create_staff_review_queue_item(
        opportunity_title=request.opportunity_title,
        grant_id=request.grant_id,
        reason=request.reason,
        created_by="staff",
    )
    return _staff_review_payload(item)


@app.get("/api/v1/civicgrants/staff/reviews")
def list_staff_reviews(
    status: str | None = None,
    _staff_principal: object = Depends(_require_staff_key),
) -> dict[str, object]:
    _require_persistence_configured()
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
    _staff_principal: object = Depends(_require_staff_key),
) -> dict[str, object]:
    _require_persistence_configured()
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
    _staff_principal: object = Depends(_require_staff_key),
) -> dict[str, object]:
    _require_persistence_configured()
    return _staff_review_summary_payload(_get_grant_repository().staff_review_summary())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: object, exc: RequestValidationError) -> JSONResponse:
    fields = sorted(
        {
            str(error["loc"][-1])
            for error in exc.errors()
            if error.get("loc") and error["loc"][0] in {"body", "query", "path"}
        }
    )
    field_text = ", ".join(fields) if fields else "request"
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "message": f"CivicGrants could not validate: {field_text}.",
                "fix": (
                    "Send a JSON body with the required field names listed in the fields array. "
                    "Keep text fields within documented bounds and use booleans for yes/no inputs."
                ),
                "fields": fields,
            }
        },
    )


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
        _grant_repository = GrantRecordsRepository(db_url=db_url, seed_defaults=False)
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


def _readiness_payload() -> dict[str, object]:
    db_url = _grant_database_url()
    if db_url is None:
        return {
            "status": "not-ready",
            "ready": False,
            "grant_database_configured": False,
            "schema_ready": False,
            "schema_version": None,
            "expected_schema_version": None,
            "opportunity_count": 0,
            "blockers": ["Set CIVICGRANTS_GRANT_DB_URL to a local grant database."],
        }

    repository = _get_grant_repository()
    schema_status = repository.schema_status()
    opportunity_count = repository.opportunity_record_count()
    blockers: list[str] = []
    if not schema_status.ready:
        blockers.append("Initialize the CivicGrants database schema with civicgrants-db-status.")
    if opportunity_count == 0:
        blockers.append("Import local grant opportunity records with civicgrants-import-opportunities.")
    ready_for_public_use = not blockers
    return {
        "status": "ready" if ready_for_public_use else "not-ready",
        "ready": ready_for_public_use,
        "grant_database_configured": True,
        "schema_ready": schema_status.ready,
        "schema_version": schema_status.schema_version,
        "expected_schema_version": schema_status.expected_schema_version,
        "opportunity_count": opportunity_count,
        "blockers": blockers,
    }
