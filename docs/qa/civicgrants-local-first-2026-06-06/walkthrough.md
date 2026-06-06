# CivicGrants Local-First Walkthrough

**Date:** 2026-06-06  
**Scope:** CivicGrants public UI, staff UI, default local persistence, readiness, integration contracts, application outline, compliance calendar, and audit export.  
**Runtime:** `http://127.0.0.1:18162` with isolated `CIVICGRANTS_DATA_DIR`.

## Verdict

Pass. CivicGrants runs locally with the default SQLite data directory, `/ready` is green, the public UI drafts through the local API, the staff UI is reachable with an actionable unauthenticated error state, and the module exposes suite integration contracts for the umbrella installer to verify.

## Evidence

- Desktop public UI: `public-desktop.png`
- Public draft result: `public-draft-result.png`
- Desktop staff UI: `staff-desktop.png`
- Staff keyless error state: `staff-keyless-error.png`
- Mobile staff UI: `staff-mobile.png`
- API evidence bundle: `walkthrough-evidence.json`

## Runtime Checks

- `GET /` returned `local-first grant support plus staff review queues`.
- `GET /ready` returned `ready=true`, `schema_ready=true`, `using_default_local_database=true`, and `opportunity_count=2`.
- `GET /api/v1/civicgrants/integration-contracts` returned all required suite contracts:
  - `civicgrants.opportunity_triage.v1`
  - `civicgrants.application_outline.v1`
  - `civicgrants.staff_review_queue.v1`
  - `civicgrants.audit_file_export.v1`
- Public UI `#draft-button` posted to `/api/v1/civicgrants/applications/outline` and rendered draft sections through safe text nodes.
- `POST /api/v1/civicgrants/applications/outline` returned a persisted `staff_review_id`.
- `POST /api/v1/civicgrants/compliance/calendar` returned a persisted `compliance_id`.
- `GET /api/v1/civicgrants/compliance/{compliance_id}` retrieved the created calendar.
- `POST /api/v1/civicgrants/export` returned the audit-file checklist and retention note.

## UI Wiring

- `/civicgrants` is wired to the local application-outline API and no longer behaves as a static-only sample.
- `/civicgrants/staff` exposes the staff queue workflow, loads the staff queue API, and shows an actionable key configuration message when no staff key is configured in the local runtime.
- Desktop and mobile staff layouts remain readable with no text overlap observed in the captured screenshots.

## Known Boundary

This local walkthrough intentionally did not inject `CIVICGRANTS_STAFF_API_KEY` into the shell command because the local hook blocks secret-looking environment variables. Keyed staff queue behavior is covered by `tests/test_production_depth_grant_persistence.py` and must be proven again by the clean-machine tester through the suite installer, where the installer sets the local staff key environment.
