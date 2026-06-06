CivicGrants
===========

CivicGrants is the CivicSuite module for grant opportunity triage, eligibility-factor matching, application outline support, compliance-calendar scaffolding, staff review queues, review-required CivicRecords grant context packets, adversarial local integration mocks, and audit-ready grant files.

Current state: v0.2.0 local-first grant support and staff review queue runtime. It ships a FastAPI package aligned to the published CivicCore v1.2.0 release wheel, default local database-backed grant opportunity triage, compliance-calendar records, staff-only review queue workflows, review-required CivicRecords/grant-file context packets, adversarial local integration mocks, application outline helper, audit-ready export checklist, an API-backed accessible public sample UI at /civicgrants, and a staff UI at /civicgrants/staff.

It does not decide official eligibility, submit grant applications, accept awards, provide legal advice, call live LLMs, call live funder feeds, or replace a grant system of record.

Staff routes require CIVICGRANTS_STAFF_API_KEY and trusted headers:

- X-CivicGrants-Role: staff or service
- X-CivicGrants-Staff-Key: configured staff key

CivicGrants creates a default local SQLite database. Set CIVICGRANTS_DATA_DIR to choose its location, or set CIVICGRANTS_GRANT_DB_URL for an explicit SQLAlchemy database URL. Use civicgrants-db-status to initialize/check explicit schema, then load local opportunity CSV rows with civicgrants-import-opportunities when replacing seeded starter records.

Local development:

python -m pip install https://github.com/CivicSuite/civiccore/releases/download/v1.2.0/civiccore-1.2.0-py3-none-any.whl
python -m pip install -e ".[dev]"
python -m pytest -q
bash scripts/verify-release.sh
