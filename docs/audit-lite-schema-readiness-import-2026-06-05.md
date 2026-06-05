# Audit Lite - Schema Readiness And Import

**Date:** 2026-06-05
**Scope:** CivicGrants local opportunity import, schema status, and readiness gate.

## Verdict

Pass. CivicGrants now has operator-visible schema status, a validated local opportunity CSV importer, and readiness endpoints that do not treat sample fallback as customer-ready data.

## Findings

None.

## Behavioral Coverage

- Configured runtime repositories are created with `seed_defaults=False`.
- `/ready` and `/api/v1/civicgrants/readiness` block when `CIVICGRANTS_GRANT_DB_URL` is unset.
- Readiness blocks when schema exists but no local opportunity records have been imported.
- Readiness passes after a local opportunity record is loaded.
- CSV import validates required columns and row values before writing.
- `civicgrants-db-status` reports schema status and opportunity count.

## Verification

- `python -m pytest tests/test_production_depth_grant_persistence.py tests/test_local_opportunity_import.py tests/test_runtime_foundation.py -q` - 23 passed.
- `python -m ruff check civicgrants tests` - passed.
