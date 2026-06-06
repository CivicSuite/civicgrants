# CivicGrants

CivicGrants is the CivicSuite module for grant opportunity triage, eligibility-factor matching, application outline support, compliance-calendar scaffolding, staff review queues, review-required CivicRecords grant context packets, adversarial local integration mocks, and audit-ready grant files.

Current state: **v0.2.0 local-first grant support and staff review queue runtime**. This repo ships a FastAPI package aligned to the published CivicCore v1.2.0 release wheel, health/root endpoints, documentation gates, default local SQLite-backed grant opportunity triage, compliance-calendar records, staff-only review queue workflows, review-required CivicRecords/grant-file context packets, adversarial local integration mocks, application outline helper, audit-ready export checklist, an accessible public sample UI at `/civicgrants`, and a staff review UI at `/civicgrants/staff`. It does **not** ship live funder feeds, official eligibility decisions, legal advice, live LLM calls, submission portals, award acceptance, or grant system-of-record integrations.

## What CivicGrants Does

- Triage sample grant opportunities and recommend a staff owner.
- Match sample eligibility factors that staff must verify.
- Draft application outlines for staff review.
- Build compliance-calendar scaffolds for awarded grants.
- Persist grant opportunity, application review, and compliance-calendar records in the default local CivicGrants database.
- Route grant review work through staff-only queue endpoints protected by `CIVICGRANTS_STAFF_API_KEY`.
- Carry CivicRecords and grant-file context IDs into review-required packets without calling those systems live.
- Validate adversarial local integration mocks for spoofed roles, official eligibility attempts, submission attempts, award-acceptance attempts, legal-advice claims, stale context, and live funder-feed claims.
- Produce audit-ready export checklists for grant files.
- Demonstrate API-backed public and staff grant-support UIs at `/civicgrants` and `/civicgrants/staff`.

## What CivicGrants Does Not Do

- It does not decide official eligibility.
- It does not submit grant applications.
- It does not accept grant awards.
- It does not provide legal advice.
- It does not call live LLMs or live funder feeds in this recovery release.
- It does not replace a grant management system of record.

## CivicCore Dependency

CivicGrants installs against the published CivicCore v1.2.0 release wheel:

```bash
python -m pip install https://github.com/CivicSuite/civiccore/releases/download/v1.2.0/civiccore-1.2.0-py3-none-any.whl
```

## API Surface

- `GET /` returns the shipped/planned boundary.
- `GET /health` returns package and CivicCore versions.
- `GET /ready` returns local-data readiness for installer and operator checks.
- `GET /api/v1/civicgrants/readiness` returns detailed schema and opportunity readiness.
- `GET /civicgrants` returns the accessible public sample UI.
- `GET /civicgrants/staff` returns the accessible staff review queue UI.
- `GET /api/v1/civicgrants/integration-contracts` returns suite-visible contract metadata.
- `POST /api/v1/civicgrants/opportunities/triage` returns sample opportunity triage.
- `POST /api/v1/civicgrants/eligibility/match` returns staff-review eligibility factors.
- `POST /api/v1/civicgrants/applications/outline` returns an application outline and a persisted `staff_review_id`.
- `POST /api/v1/civicgrants/compliance/calendar` returns compliance reminders and a persisted `compliance_id`.
- `GET /api/v1/civicgrants/compliance/{compliance_id}` retrieves a persisted compliance calendar.
- `POST /api/v1/civicgrants/context/grant-review` returns review-required CivicRecords/grant-file context.
- `POST /api/v1/civicgrants/integrations/mock/grant-context` validates local adversarial integration payloads.
- `POST /api/v1/civicgrants/staff/reviews` creates a staff-only review queue item.
- `GET /api/v1/civicgrants/staff/reviews` lists staff-only review queue items.
- `PATCH /api/v1/civicgrants/staff/reviews/{review_id}` updates staff-only queue status, assignment, and resolution.
- `GET /api/v1/civicgrants/staff/reviews/summary` returns staff queue counts.
- `POST /api/v1/civicgrants/export` returns an audit-file export checklist.

## Local Persistence And Staff Queue

CivicGrants creates a default local SQLAlchemy-backed SQLite database at startup. Set `CIVICGRANTS_DATA_DIR` to choose the local data directory, or set `CIVICGRANTS_GRANT_DB_URL` when a city needs an explicit SQLAlchemy database URL. The default local database seeds starter opportunity records so `/ready` is usable for clerk-first installation checks.

Example local data directory:

```bash
export CIVICGRANTS_DATA_DIR="./data/civicgrants"
```

Set `CIVICGRANTS_STAFF_API_KEY` before using staff-only review routes:

```bash
export CIVICGRANTS_STAFF_API_KEY="replace-with-city-secret"
```

Staff routes require `X-CivicGrants-Role: staff` and `X-CivicGrants-Staff-Key` matching the configured key. CivicGrants uses CivicCore `staff_key_gate` for timing-safe key comparison. Use `civicgrants-db-status` to initialize/check an explicit database URL and `civicgrants-import-opportunities` to load city opportunity CSV rows when replacing the seeded starter records.

## Local Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
bash scripts/verify-release.sh
```

## License

Code is Apache License 2.0. Documentation is CC BY 4.0.
