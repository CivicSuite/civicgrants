from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from civicgrants.opportunity_triage import DISCLAIMER
from civicgrants.persistence import GrantRecordsRepository


OPPORTUNITY_COLUMNS = {
    "opportunity_key",
    "opportunity_title",
    "funding_area",
    "deadline",
    "priority",
    "recommended_owner",
    "triage_notes",
}


@dataclass(frozen=True)
class ImportSummary:
    opportunities: int = 0


def import_local_opportunities(*, db_url: str, opportunities_csv: Path) -> ImportSummary:
    """Validate and import local grant opportunity CSV rows into CivicGrants."""

    records = [
        {
            "opportunity_key": _required(row, "opportunity_key"),
            "opportunity_title": _required(row, "opportunity_title"),
            "funding_area": _required(row, "funding_area"),
            "deadline": _required(row, "deadline"),
            "priority": _required(row, "priority"),
            "recommended_owner": _required(row, "recommended_owner"),
            "triage_notes": _triage_notes(row, opportunities_csv, index),
            "disclaimer": DISCLAIMER,
        }
        for index, row in _read_rows(opportunities_csv)
    ]

    repository = GrantRecordsRepository(db_url=db_url, seed_defaults=False)
    try:
        for record in records:
            repository.upsert_opportunity(**record)
    finally:
        repository.engine.dispose()
    return ImportSummary(opportunities=len(records))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import local municipal grant opportunity CSV rows into CivicGrants."
    )
    parser.add_argument("--db-url", required=True, help="SQLAlchemy database URL for CivicGrants records.")
    parser.add_argument(
        "--opportunities-csv",
        required=True,
        type=Path,
        help="CSV with local grant opportunity rows.",
    )
    args = parser.parse_args(argv)

    summary = import_local_opportunities(db_url=args.db_url, opportunities_csv=args.opportunities_csv)
    print(f"CivicGrants import complete: {summary.opportunities} opportunities.")
    return 0


def _read_rows(path: Path) -> list[tuple[int, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(OPPORTUNITY_COLUMNS - fieldnames)
        if missing:
            raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")
        rows = list(reader)
    for index, row in enumerate(rows, start=2):
        for column in OPPORTUNITY_COLUMNS:
            if row.get(column, "").strip() == "":
                raise ValueError(f"{path}:{index} has an empty required value for {column}")
        _triage_notes(row, path, index)
    return list(enumerate(rows, start=2))


def _required(row: dict[str, str], column: str) -> str:
    return row[column].strip()


def _triage_notes(row: dict[str, str], path: Path, index: int) -> tuple[str, ...]:
    notes = tuple(note.strip() for note in row["triage_notes"].split(";") if note.strip())
    if not notes:
        raise ValueError(f"{path}:{index} has an empty required value for triage_notes")
    return notes


if __name__ == "__main__":
    raise SystemExit(main())
