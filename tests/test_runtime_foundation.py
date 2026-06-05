import tomllib
from pathlib import Path

from fastapi.testclient import TestClient

import civicgrants
from civicgrants.main import app


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_package_version_is_100() -> None:
    assert civicgrants.__version__ == "0.2.0"


def test_pyproject_uses_published_civiccore_release_wheel() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]

    assert data["tool"]["hatch"]["metadata"]["allow-direct-references"] is True
    assert (
        "civiccore @ https://github.com/CivicSuite/civiccore/releases/download/"
        "v1.2.0/civiccore-1.2.0-py3-none-any.whl#sha256=a94ce958e36fb03c8d961e4db4672ce5bcfa25765c57d75886e999cf15703ec7"
    ) in dependencies
    assert "civiccore==1.0.0" not in dependencies


def test_pyproject_exposes_operator_database_scripts() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    scripts = data["project"]["scripts"]
    assert scripts["civicgrants-db-status"] == "civicgrants.db_admin:main"
    assert scripts["civicgrants-import-opportunities"] == "civicgrants.data_import:main"


def test_root_endpoint_states_runtime_boundary() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()

    assert payload["name"] == "CivicGrants"
    assert payload["version"] == "0.2.0"
    assert payload["status"] == "grant support foundation plus grant persistence"
    assert "staff review queues" in payload["message"]
    assert "CivicRecords grant context packets" in payload["message"]
    assert "official eligibility decisions" in payload["message"]
    assert "not implemented" in payload["message"]
    assert payload["next_step"].startswith("Configure CIVICGRANTS_GRANT_DB_URL")
    assert "/ready" in payload["next_step"]


def test_health_endpoint_reports_versions() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "civicgrants"
    assert payload["version"] == "0.2.0"
    assert payload["civiccore_version"] == "1.2.0"


def test_release_gate_prefers_native_unix_python_before_windows_launcher() -> None:
    script = (ROOT / "scripts" / "verify-release.sh").read_text(encoding="utf-8")

    python3_probe = "command -v python3"
    python_probe = "command -v python)"
    assert python3_probe in script
    assert python_probe in script
    assert script.index(python3_probe) < script.index(python_probe)
