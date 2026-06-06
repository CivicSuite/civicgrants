# Audit Lite - CivicGrants local-first staff UI
**Date:** 2026-06-06
**Scope:** CivicGrants default local persistence, staff UI, integration contracts, current-facing docs, and behavioral tests.
**Reviewer:** Codex (audit-lite)

## TL;DR
Ship this slice. CivicGrants now defaults to a local SQLite-backed data directory, persists application review and compliance flows without requiring `CIVICGRANTS_GRANT_DB_URL`, exposes a staff review UI, and advertises suite integration contracts. The old optional-DB behavior is covered by mutation-style test changes that now fail if default local persistence disappears.

## Severity rollup
- Blocker: 0
- Critical: 0
- Major: 0
- Minor: 0
- Nit: 0

## Findings

No findings.

## What's working
- Correctness: `civicgrants/main.py` now creates a default local database from `CIVICGRANTS_DATA_DIR`, seeds starter opportunities only for the default database, and still preserves explicit `CIVICGRANTS_GRANT_DB_URL` behavior without seeding configured city data.
- UX: `civicgrants/public_ui.py` adds `/civicgrants/staff` with readable staff-key, outline, queue-load, success, and error states, and tests assert no `innerHTML` injection sink.
- Tests: `tests/test_production_depth_grant_persistence.py` now proves default readiness, default staff queue persistence, default compliance persistence, and explicit DB no-seed behavior. `tests/test_grants_foundation.py` proves staff UI and integration contract wiring.
- Docs: `README.md`, `USER-MANUAL.md`, text mirrors, `docs/index.html`, and `CHANGELOG.md` now describe local-first persistence instead of the old env-required path.
- Runtime: `bash scripts/verify-release.sh` passed after the docs update, including 38 tests, docs gate, placeholder import check, Ruff, and package build.

## Watch items

The full suite installer still needs to set CivicGrants data/staff-key environment, verify `/api/v1/civicgrants/integration-contracts`, pin this source head, and prove the module on the clean machine.

## Escalation recommendation

No escalation needed for this slice. Run `audit-full` and `walkthrough` after the umbrella installer integration is in place for the complete CivicGrants stage gate.
