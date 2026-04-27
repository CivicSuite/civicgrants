CivicGrants
============

CivicGrants is the CivicSuite module for grant opportunity triage, eligibility-factor matching, application outline support, compliance-calendar scaffolding, and audit-ready grant files.

Current state: v0.1.0 grant support foundation release. It ships deterministic sample helpers and an accessible public sample UI at /civicgrants.

Not shipped: live funder feeds, official eligibility decisions, legal advice, live LLM calls, submission portals, or grant system-of-record integrations.

API surface:
- GET /
- GET /health
- GET /civicgrants
- POST /api/v1/civicgrants/opportunities/triage
- POST /api/v1/civicgrants/eligibility/match
- POST /api/v1/civicgrants/applications/outline
- POST /api/v1/civicgrants/compliance/calendar
- POST /api/v1/civicgrants/export

License: code Apache License 2.0; documentation CC BY 4.0.
