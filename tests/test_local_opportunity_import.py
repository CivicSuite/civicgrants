from pathlib import Path

import pytest

from civicgrants.data_import import import_local_opportunities, main
from civicgrants.persistence import GrantRecordsRepository


def test_import_local_opportunities_loads_valid_csv(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{(tmp_path / 'opportunities.db').as_posix()}"
    csv_path = _write_csv(
        tmp_path,
        "opportunity_key,opportunity_title,funding_area,deadline,priority,recommended_owner,triage_notes\n"
        "water-infrastructure-grant,Water infrastructure grant,stormwater,2026-06-01,high,Utilities,Confirm match;Confirm deadline\n",
    )

    summary = import_local_opportunities(db_url=db_url, opportunities_csv=csv_path)

    repository = GrantRecordsRepository(db_url=db_url, seed_defaults=False)
    try:
        result = repository.triage_opportunity(
            opportunity_title="Water infrastructure grant",
            funding_area="stormwater",
            deadline="2026-06-01",
        )
        count = repository.opportunity_record_count()
    finally:
        repository.engine.dispose()

    assert summary.opportunities == 1
    assert count == 1
    assert result.recommended_owner == "Utilities"
    assert result.triage_notes == ("Confirm match", "Confirm deadline")


def test_import_local_opportunities_validates_before_writing(tmp_path: Path) -> None:
    db_url = f"sqlite+pysqlite:///{(tmp_path / 'invalid-opportunities.db').as_posix()}"
    csv_path = _write_csv(
        tmp_path,
        "opportunity_key,opportunity_title,funding_area,deadline,priority,recommended_owner,triage_notes\n"
        "water-infrastructure-grant,Water infrastructure grant,stormwater,2026-06-01,high,Utilities,\n",
    )

    with pytest.raises(ValueError, match="triage_notes"):
        import_local_opportunities(db_url=db_url, opportunities_csv=csv_path)

    repository = GrantRecordsRepository(db_url=db_url, seed_defaults=False)
    try:
        assert repository.opportunity_record_count() == 0
    finally:
        repository.engine.dispose()


def test_import_cli_reports_loaded_opportunities(tmp_path: Path, capsys) -> None:
    db_url = f"sqlite+pysqlite:///{(tmp_path / 'cli-opportunities.db').as_posix()}"
    csv_path = _write_csv(
        tmp_path,
        "opportunity_key,opportunity_title,funding_area,deadline,priority,recommended_owner,triage_notes\n"
        "parks-access-grant,Parks access grant,parks,confirm,medium,Parks,Confirm match\n",
    )

    exit_code = main(["--db-url", db_url, "--opportunities-csv", str(csv_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "CivicGrants import complete: 1 opportunities." in captured.out


def _write_csv(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "opportunities.csv"
    path.write_text(text, encoding="utf-8")
    return path
