# Engineering Deep Dive

## Scope

Reviewed `civicgrants/main.py`, persistence behavior, staff auth boundaries, integration contracts, tests, and release verification.

## Severity Rollup

- Blocker: 0
- Critical: 0
- Major: 0
- Minor: 0
- Nit: 0

## Findings

No findings.

## What's Working

- Default persistence uses `CIVICGRANTS_DATA_DIR` and falls back to a local SQLite file, while explicit `CIVICGRANTS_GRANT_DB_URL` remains supported.
- Seeded starter opportunities apply only to the default local database; configured city databases still require imported city records.
- Application outlines and compliance calendars now persist IDs in the normal no-env path.
- Integration contracts are machine-readable and stable for suite verification.

## Residual Risk

The suite installer must set an isolated data directory and staff key before clean-machine proof. This is an umbrella integration task, not a module defect.
