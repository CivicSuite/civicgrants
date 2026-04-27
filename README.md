# CivicGrants

CivicGrants is the CivicSuite module for grant opportunity triage, eligibility-factor matching, application outline support, compliance-calendar scaffolding, and audit-ready grant files.

Current state: **v0.1.0 grant support foundation release**. This repo ships a FastAPI package, health/root endpoints, documentation gates, deterministic sample opportunity triage, eligibility matching, application outline helper, compliance calendar helper, audit-ready export checklist, and accessible public sample UI at `/civicgrants`. It does **not** ship live funder feeds, official eligibility decisions, legal advice, live LLM calls, submission portals, or grant system-of-record integrations.

## What CivicGrants Does

- Triage sample grant opportunities and recommend a staff owner.
- Match sample eligibility factors that staff must verify.
- Draft application outlines for staff review.
- Build compliance-calendar scaffolds for awarded grants.
- Produce audit-ready export checklists for grant files.
- Demonstrate a public grant-support UI at `/civicgrants`.

## What CivicGrants Does Not Do

- It does not decide official eligibility.
- It does not submit grant applications.
- It does not provide legal advice.
- It does not call live LLMs in v0.1.0.
- It does not replace a grant management system of record.

## API Surface

- `GET /` returns the shipped/planned boundary.
- `GET /health` returns package and CivicCore versions.
- `GET /civicgrants` returns the accessible public sample UI.
- `POST /api/v1/civicgrants/opportunities/triage` returns sample opportunity triage.
- `POST /api/v1/civicgrants/eligibility/match` returns staff-review eligibility factors.
- `POST /api/v1/civicgrants/applications/outline` returns an application outline.
- `POST /api/v1/civicgrants/compliance/calendar` returns compliance reminders.
- `POST /api/v1/civicgrants/export` returns an audit-file export checklist.

## Local Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
bash scripts/verify-release.sh
```

## License

Code is Apache License 2.0. Documentation is CC BY 4.0.
