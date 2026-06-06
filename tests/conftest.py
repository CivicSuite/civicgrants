from __future__ import annotations

import pytest

import civicgrants.main as main_module


@pytest.fixture(autouse=True)
def isolated_civicgrants_runtime_data(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Keep default local-first runtime data isolated per test."""

    monkeypatch.setenv("CIVICGRANTS_DATA_DIR", str(tmp_path / "runtime-data"))
    yield
    main_module._dispose_grant_repository()
    main_module._grant_db_url = None

