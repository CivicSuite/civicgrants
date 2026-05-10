from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from civicgrants.main import app, _dispose_grant_repository
from civicgrants.persistence import GrantRecordsRepository


client = TestClient(app)


def test_repository_persists_seeded_triage_and_compliance_calendar(tmp_path: Path) -> None:
    db_path = tmp_path / "civicgrants.db"
    db_url = f"sqlite+pysqlite:///{db_path.as_posix()}"

    repository = GrantRecordsRepository(db_url=db_url)
    triage = repository.triage_opportunity(
        opportunity_title="Water infrastructure grant",
        funding_area="stormwater",
        deadline="2026-06-01",
    )
    compliance = repository.create_compliance_calendar(
        award_name="Water infrastructure grant",
        reporting_frequency="monthly",
    )
    repository.engine.dispose()

    reloaded = GrantRecordsRepository(db_url=db_url)
    stored = reloaded.get_compliance_calendar(compliance.compliance_id)
    reloaded.engine.dispose()

    assert triage.recommended_owner == "Public Works"
    assert stored is not None
    assert stored.award_name == "Water infrastructure grant"
    assert stored.reporting_frequency == "monthly"
    assert any("monthly financial" in item for item in stored.calendar_items)
    db_path.unlink()


def test_grant_persistence_api_round_trip(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "civicgrants-api.db"
    monkeypatch.setenv("CIVICGRANTS_GRANT_DB_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
    _dispose_grant_repository()

    triage = client.post(
        "/api/v1/civicgrants/opportunities/triage",
        json={
            "opportunity_title": "Water infrastructure grant",
            "funding_area": "stormwater",
            "deadline": "2026-06-01",
        },
    )
    created = client.post(
        "/api/v1/civicgrants/compliance/calendar",
        json={"award_name": "Water infrastructure grant", "reporting_frequency": "monthly"},
    )
    compliance_id = created.json()["compliance_id"]
    fetched = client.get(f"/api/v1/civicgrants/compliance/{compliance_id}")

    _dispose_grant_repository()
    monkeypatch.delenv("CIVICGRANTS_GRANT_DB_URL")

    assert triage.status_code == 200
    assert triage.json()["recommended_owner"] == "Public Works"
    assert created.status_code == 200
    assert compliance_id
    assert fetched.status_code == 200
    assert fetched.json()["award_name"] == "Water infrastructure grant"
    assert fetched.json()["reporting_frequency"] == "monthly"
    db_path.unlink()


def test_application_outline_with_persistence_creates_staff_review_queue(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "api-staff-review-records.db"
    monkeypatch.setenv("CIVICGRANTS_GRANT_DB_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("CIVICGRANTS_STAFF_API_KEY", "test-staff-key")
    _dispose_grant_repository()

    headers = {"X-CivicGrants-Role": "staff", "X-CivicGrants-Staff-Key": "test-staff-key"}
    created = client.post(
        "/api/v1/civicgrants/applications/outline",
        json={
            "grant_id": "grant-2026-001",
            "project_name": "North basin stormwater retrofit",
            "opportunity_title": "Water infrastructure grant",
            "city_need": "Flooding affects three blocks.",
        },
    )
    queue_response = client.get("/api/v1/civicgrants/staff/reviews", headers=headers)
    summary_response = client.get("/api/v1/civicgrants/staff/reviews/summary", headers=headers)

    _dispose_grant_repository()
    monkeypatch.delenv("CIVICGRANTS_GRANT_DB_URL")
    monkeypatch.delenv("CIVICGRANTS_STAFF_API_KEY")

    assert created.status_code == 200
    payload = created.json()
    assert payload["staff_review_id"]
    assert payload["staff_review_required"] is True
    assert queue_response.status_code == 200
    items = queue_response.json()["items"]
    assert len(items) == 1
    assert items[0]["review_id"] == payload["staff_review_id"]
    assert items[0]["grant_id"] == "grant-2026-001"
    assert items[0]["opportunity_title"] == "Water infrastructure grant"
    assert summary_response.status_code == 200
    assert summary_response.json()["open_items"] == 1
    db_path.unlink()


def test_staff_review_queue_lifecycle_is_staff_gated_and_persistent(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "api-staff-review-lifecycle.db"
    monkeypatch.setenv("CIVICGRANTS_GRANT_DB_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("CIVICGRANTS_STAFF_API_KEY", "test-staff-key")
    _dispose_grant_repository()

    headers = {"X-CivicGrants-Role": "staff", "X-CivicGrants-Staff-Key": "test-staff-key"}
    blocked = client.post(
        "/api/v1/civicgrants/staff/reviews",
        json={"grant_id": "grant-2026-002", "opportunity_title": "Parks grant", "reason": "Needs budget review."},
    )
    created = client.post(
        "/api/v1/civicgrants/staff/reviews",
        headers=headers,
        json={"grant_id": "grant-2026-002", "opportunity_title": "Parks grant", "reason": "Needs budget review."},
    )
    review_id = created.json()["review_id"]
    invalid_update = client.patch(
        f"/api/v1/civicgrants/staff/reviews/{review_id}",
        headers=headers,
        json={"status": "resolved"},
    )
    resolved = client.patch(
        f"/api/v1/civicgrants/staff/reviews/{review_id}",
        headers=headers,
        json={"status": "resolved", "assigned_to": "finance", "resolution": "Budget source confirmed."},
    )

    _dispose_grant_repository()
    reloaded = client.get("/api/v1/civicgrants/staff/reviews?status=resolved", headers=headers)

    _dispose_grant_repository()
    monkeypatch.delenv("CIVICGRANTS_GRANT_DB_URL")
    monkeypatch.delenv("CIVICGRANTS_STAFF_API_KEY")

    assert blocked.status_code == 403
    assert "X-CivicGrants-Role" in blocked.json()["detail"]["fix"]
    assert created.status_code == 200
    assert created.json()["status"] == "open"
    assert invalid_update.status_code == 422
    assert "resolution is required" in invalid_update.json()["detail"]["fix"]
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert reloaded.status_code == 200
    assert reloaded.json()["items"][0]["review_id"] == review_id
    db_path.unlink()


def test_staff_review_queue_requires_persistence_configuration(monkeypatch) -> None:
    monkeypatch.delenv("CIVICGRANTS_GRANT_DB_URL", raising=False)
    monkeypatch.setenv("CIVICGRANTS_STAFF_API_KEY", "test-staff-key")
    _dispose_grant_repository()

    response = client.get(
        "/api/v1/civicgrants/staff/reviews",
        headers={"X-CivicGrants-Role": "staff", "X-CivicGrants-Staff-Key": "test-staff-key"},
    )

    monkeypatch.delenv("CIVICGRANTS_STAFF_API_KEY")

    assert response.status_code == 503
    assert "Set CIVICGRANTS_GRANT_DB_URL" in response.json()["detail"]["fix"]


def test_get_compliance_calendar_without_persistence_returns_actionable_503(monkeypatch) -> None:
    monkeypatch.delenv("CIVICGRANTS_GRANT_DB_URL", raising=False)
    _dispose_grant_repository()

    response = client.get("/api/v1/civicgrants/compliance/example")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["message"] == "CivicGrants grant persistence is not configured."
    assert "Set CIVICGRANTS_GRANT_DB_URL" in detail["fix"]


def test_get_compliance_calendar_missing_id_returns_actionable_404(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "civicgrants-missing.db"
    monkeypatch.setenv("CIVICGRANTS_GRANT_DB_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
    _dispose_grant_repository()

    response = client.get("/api/v1/civicgrants/compliance/missing")

    _dispose_grant_repository()
    monkeypatch.delenv("CIVICGRANTS_GRANT_DB_URL")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["message"] == "Compliance calendar record not found."
    assert "POST /api/v1/civicgrants/compliance/calendar" in detail["fix"]
    db_path.unlink()


def test_plain_calendar_response_includes_null_compliance_id(monkeypatch) -> None:
    monkeypatch.delenv("CIVICGRANTS_GRANT_DB_URL", raising=False)
    _dispose_grant_repository()

    response = client.post(
        "/api/v1/civicgrants/compliance/calendar",
        json={"award_name": "Water grant", "reporting_frequency": "quarterly"},
    )

    assert response.status_code == 200
    assert response.json()["compliance_id"] is None
    assert os.environ.get("CIVICGRANTS_GRANT_DB_URL") is None
