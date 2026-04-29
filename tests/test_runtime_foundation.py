from fastapi.testclient import TestClient

import civicgrants
from civicgrants.main import app


client = TestClient(app)


def test_package_version_is_011() -> None:
    assert civicgrants.__version__ == "0.1.1"


def test_root_endpoint_states_runtime_boundary() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()

    assert payload["name"] == "CivicGrants"
    assert payload["version"] == "0.1.1"
    assert payload["status"] == "grant support foundation plus grant persistence"
    assert "database-backed grant opportunity and compliance records" in payload["message"]
    assert "official eligibility decisions" in payload["message"]
    assert "not implemented yet" in payload["message"]
    assert payload["next_step"].startswith("Post-v0.1.1 roadmap")


def test_health_endpoint_reports_versions() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "civicgrants"
    assert payload["version"] == "0.1.1"
    assert payload["civiccore_version"] == "0.3.0"
