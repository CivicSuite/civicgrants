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
