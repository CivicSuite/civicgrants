from __future__ import annotations

import argparse

from civicgrants.persistence import GrantRecordsRepository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check and initialize the local CivicGrants database schema."
    )
    parser.add_argument("--db-url", required=True, help="SQLAlchemy database URL used by CIVICGRANTS_GRANT_DB_URL.")
    args = parser.parse_args()

    repository = GrantRecordsRepository(db_url=args.db_url, seed_defaults=False)
    try:
        status = repository.schema_status()
        opportunities = repository.opportunity_record_count()
    finally:
        repository.engine.dispose()

    ready = "ready" if status.ready else "not ready"
    missing = ", ".join(status.missing_tables) if status.missing_tables else "none"
    version = status.schema_version or "none"
    print(
        "CivicGrants schema "
        f"{ready}: version={version}; expected={status.expected_schema_version}; "
        f"dialect={status.dialect}; missing_tables={missing}; opportunities={opportunities}."
    )


if __name__ == "__main__":
    main()
