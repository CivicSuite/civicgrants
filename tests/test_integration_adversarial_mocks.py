from fastapi.testclient import TestClient

from civicgrants.integration_mocks import validate_grant_context_mocks
from civicgrants.main import app


client = TestClient(app)


def test_adversarial_mock_rejects_spoofed_submission_and_missing_context() -> None:
    result = validate_grant_context_mocks(
        {
            "scenario": "spoofed-grant-submission",
            "role": "resident",
            "official_eligibility": True,
            "application_submitted": True,
            "award_accepted": True,
            "legal_advice": True,
            "funder_feed_source": "live",
            "source_date_status": "stale",
        }
    )

    assert result.status == "blocked-for-staff-review"
    assert result.review_required is True
    assert "Rejected grant context without trusted staff or service role." in result.findings
    assert "Rejected attempted official eligibility determination in integration context." in result.findings
    assert "Rejected attempted grant application submission in integration context." in result.findings
    assert "does not call live CivicRecords" in result.boundary


def test_integration_mock_api_accepts_complete_staff_context_for_review() -> None:
    response = client.post(
        "/api/v1/civicgrants/integrations/mock/grant-context",
        json={
            "scenario": "complete-local-context",
            "role": "staff",
            "records_context_id": "records-context-123",
            "grant_file_context_id": "grant-file-456",
            "source_date_status": "current",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready-for-staff-review"
    assert payload["findings"] == []
    assert payload["review_required"] is True


def test_integration_mock_api_blocks_stale_or_partial_context() -> None:
    response = client.post(
        "/api/v1/civicgrants/integrations/mock/grant-context",
        json={
            "scenario": "stale-records-context",
            "role": "service",
            "records_context_id": "records-context-123",
            "source_date_status": "stale",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked-for-staff-review"
    assert "Missing grant file context ID" in " ".join(payload["findings"])
    assert "Stale records/grant context" in " ".join(payload["findings"])


def test_grant_review_context_carries_records_and_grant_file_references() -> None:
    response = client.post(
        "/api/v1/civicgrants/context/grant-review",
        json={
            "grant_id": "grant-2026-001",
            "opportunity_title": "Water infrastructure grant",
            "records_context_id": "records-context-123",
            "grant_file_context_id": "grant-file-456",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["grant_id"] == "grant-2026-001"
    assert payload["review_required"] is True
    assert "CivicRecords context: records-context-123" in payload["citations"]
    assert "Grant file context: grant-file-456" in payload["citations"]
    assert "not an official eligibility decision" in payload["boundary"]
