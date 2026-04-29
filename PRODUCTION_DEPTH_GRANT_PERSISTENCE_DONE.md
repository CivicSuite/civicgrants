# Production Depth: Grant Persistence

## Summary

CivicGrants now supports optional SQLAlchemy-backed grant opportunity and compliance-calendar records through `CIVICGRANTS_GRANT_DB_URL`.

## Shipped

- `GrantRecordsRepository` with schema-aware SQLAlchemy tables.
- Seeded sample grant opportunity records.
- Persisted compliance-calendar records with `compliance_id`.
- Retrieval endpoint: `GET /api/v1/civicgrants/compliance/{compliance_id}`.
- Actionable `503` guidance when persistence is not configured.
- Regression tests for repository reload, API round trip, missing-record `404`, no-config `503`, and stateless fallback behavior.

## Still Not Shipped

- Live funder feeds.
- Official eligibility decisions.
- Legal advice.
- Live LLM calls.
- Submission portals.
- Grant system-of-record integrations.

## Verification

Run before merge:

```bash
python -m pytest --collect-only -q
python -m pytest -q
bash scripts/verify-docs.sh
python scripts/check-civiccore-placeholder-imports.py
python -m ruff check .
bash scripts/verify-release.sh
git diff --check
```
