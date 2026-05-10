# CivicGrants

CivicGrants is the CivicSuite module for grant opportunity triage, eligibility-factor matching, application outline support, compliance-calendar scaffolding, staff review queues, review-required CivicRecords grant context packets, adversarial local integration mocks, and audit-ready grant files.

Current state: **v0.2.0 grant support and staff review queue runtime**. This repo ships a FastAPI package aligned to the published CivicCore v1.0.0 release wheel, health/root endpoints, documentation gates, deterministic and database-backed grant opportunity triage, compliance-calendar records, staff-only review queue workflows, review-required CivicRecords/grant-file context packets, adversarial local integration mocks, application outline helper, audit-ready export checklist, and accessible public sample UI at `/civicgrants`. It does **not** ship live funder feeds, official eligibility decisions, legal advice, live LLM calls, submission portals, award acceptance, or grant system-of-record integrations.

## What CivicGrants Does

- Triage sample grant opportunities and recommend a staff owner.
- Match sample eligibility factors that staff must verify.
- Draft application outlines for staff review.
- Build compliance-calendar scaffolds for awarded grants.
- Persist grant opportunity and compliance-calendar records when `CIVICGRANTS_GRANT_DB_URL` is configured.
- Route grant review work through staff-only queue endpoints protected by `CIVICGRANTS_STAFF_API_KEY`.
- Carry CivicRecords and grant-file context IDs into review-required packets without calling those systems live.
- Validate adversarial local integration mocks for spoofed roles, official eligibility attempts, submission attempts, award-acceptance attempts, legal-advice claims, stale context, and live funder-feed claims.
- Produce audit-ready export checklists for grant files.
- Demonstrate a public grant-support UI at `/civicgrants`.

## What CivicGrants Does Not Do

- It does not decide official eligibility.
- It does not submit grant applications.
- It does not accept grant awards.
- It does not provide legal advice.
- It does not call live LLMs or live funder feeds in this recovery release.
- It does not replace a grant management system of record.

## CivicCore Dependency

CivicGrants installs against the published CivicCore v1.0.0 release wheel:

```bash
python -m pip install https://github.com/CivicSuite/civiccore/releases/download/v1.0.1/civiccore-1.0.1-py3-none-any.whl
```

## API Surface

- `GET /` returns the shipped/planned boundary.
- `GET /health` returns package and CivicCore versions.
- `GET /civicgrants` returns the accessible public sample UI.
- `POST /api/v1/civicgrants/opportunities/triage` returns sample opportunity triage.
- `POST /api/v1/civicgrants/eligibility/match` returns staff-review eligibility factors.
- `POST /api/v1/civicgrants/applications/outline` returns an application outline and a `staff_review_id` when persistence is configured.
- `POST /api/v1/civicgrants/compliance/calendar` returns compliance reminders and a `compliance_id` when persistence is configured.
- `GET /api/v1/civicgrants/compliance/{compliance_id}` retrieves a persisted compliance calendar when `CIVICGRANTS_GRANT_DB_URL` is configured.
- `POST /api/v1/civicgrants/context/grant-review` returns review-required CivicRecords/grant-file context.
- `POST /api/v1/civicgrants/integrations/mock/grant-context` validates local adversarial integration payloads.
- `POST /api/v1/civicgrants/staff/reviews` creates a staff-only review queue item.
- `GET /api/v1/civicgrants/staff/reviews` lists staff-only review queue items.
- `PATCH /api/v1/civicgrants/staff/reviews/{review_id}` updates staff-only queue status, assignment, and resolution.
- `GET /api/v1/civicgrants/staff/reviews/summary` returns staff queue counts.
- `POST /api/v1/civicgrants/export` returns an audit-file export checklist.

## Optional Persistence And Staff Queue

Set `CIVICGRANTS_GRANT_DB_URL` to enable local SQLAlchemy-backed grant records:

```bash
export CIVICGRANTS_GRANT_DB_URL="sqlite+pysqlite:///./civicgrants.db"
```

Set `CIVICGRANTS_STAFF_API_KEY` before using staff-only review routes:

```bash
export CIVICGRANTS_STAFF_API_KEY="replace-with-city-secret"
```

Staff routes require `X-CivicGrants-Role: staff` or `service` and `X-CivicGrants-Staff-Key` matching the configured key. Without persistence, CivicGrants remains deterministic and stateless. Retrieval and staff-only endpoints return actionable `503` responses that name the required configuration.

## Local Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
bash scripts/verify-release.sh
```

## License

Code is Apache License 2.0. Documentation is CC BY 4.0.
