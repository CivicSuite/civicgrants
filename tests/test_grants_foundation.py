from fastapi.testclient import TestClient

from civicgrants.application_draft import draft_application_outline
from civicgrants.audit_file import build_audit_file_export
from civicgrants.compliance_calendar import build_compliance_calendar
from civicgrants.eligibility import match_grant_eligibility
from civicgrants.main import app
from civicgrants.opportunity_triage import triage_opportunity


client = TestClient(app)


def test_opportunity_triage_recommends_owner_and_boundary() -> None:
    result = triage_opportunity(
        opportunity_title="Water infrastructure grant",
        funding_area="stormwater",
        deadline="2026-06-01",
    )
    assert result.recommended_owner == "Public Works"
    assert "Confirm deadline" in result.triage_notes[0]
    assert "does not determine eligibility" in result.disclaimer


def test_eligibility_match_requires_staff_verification() -> None:
    result = match_grant_eligibility(
        city_profile="Population 8,500; local match available; capital plan adopted.",
        opportunity_title="Water infrastructure grant",
        funding_area="stormwater",
    )
    assert result.status == "needs-staff-verification"
    assert "Population profile supplied." in result.matched_factors
    assert any("official applicant eligibility" in q for q in result.unresolved_questions)


def test_application_outline_requires_staff_review() -> None:
    result = draft_application_outline(
        project_name="North basin stormwater retrofit",
        opportunity_title="Water infrastructure grant",
        city_need="Flooding affects three blocks near the north basin.",
    )
    assert result.heading == "Draft application outline for North basin stormwater retrofit"
    assert result.staff_review_required is True
    assert any("Budget" in section for section in result.narrative_sections)


def test_compliance_calendar_defaults_to_quarterly() -> None:
    result = build_compliance_calendar(award_name="Water grant", reporting_frequency="weird")
    assert result.reporting_frequency == "quarterly"
    assert any("quarterly financial" in item for item in result.calendar_items)


def test_audit_file_export_preserves_records_context() -> None:
    result = build_audit_file_export(title="Water grant file", grant_id="grant-2026-001")
    assert result.grant_id == "grant-2026-001"
    assert "Preserve source opportunity notice and eligibility review notes." in result.checklist
    assert "retention schedule" in result.retention_note


def test_grant_support_apis_success_shape() -> None:
    triage = client.post(
        "/api/v1/civicgrants/opportunities/triage",
        json={
            "opportunity_title": "Water infrastructure grant",
            "funding_area": "stormwater",
            "deadline": "2026-06-01",
        },
    )
    eligibility = client.post(
        "/api/v1/civicgrants/eligibility/match",
        json={
            "city_profile": "Population 8,500; local match available.",
            "opportunity_title": "Water infrastructure grant",
            "funding_area": "stormwater",
        },
    )
    outline = client.post(
        "/api/v1/civicgrants/applications/outline",
        json={
            "project_name": "North basin stormwater retrofit",
            "opportunity_title": "Water infrastructure grant",
            "city_need": "Flooding affects three blocks.",
        },
    )
    calendar = client.post(
        "/api/v1/civicgrants/compliance/calendar",
        json={"award_name": "Water grant", "reporting_frequency": "monthly"},
    )
    export = client.post(
        "/api/v1/civicgrants/export",
        json={"title": "Water grant file", "grant_id": "grant-2026-001"},
    )
    assert triage.status_code == 200
    assert triage.json()["recommended_owner"] == "Public Works"
    assert eligibility.status_code == 200
    assert eligibility.json()["unresolved_questions"]
    assert outline.status_code == 200
    assert outline.json()["staff_review_required"] is True
    assert calendar.status_code == 200
    assert calendar.json()["reporting_frequency"] == "monthly"
    assert export.status_code == 200
    assert export.json()["grant_id"] == "grant-2026-001"


def test_public_ui_route_is_accessible_and_honest() -> None:
    response = client.get("/civicgrants")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    text = response.text
    assert '<a class="skip-link" href="#main">Skip to main content</a>' in text
    assert '<main id="main" tabindex="-1">' in text
    assert "v0.1.1 grant support foundation" in text
    assert "does not determine eligibility" in text
    assert "grant system of record" in text
