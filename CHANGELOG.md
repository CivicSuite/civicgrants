# Changelog

## Unreleased

- Aligned the current CivicGrants runtime dependency and current-facing docs to the published CivicCore v1.2.0 release wheel.
- Wired the public `/civicgrants` draft workflow to the local application-outline API and safe DOM rendering.
- Added schema status, local opportunity import, and readiness gates that do not treat sample fallback as customer data.
- Added bounded API request validation with actionable 422 responses.

## [0.2.0] - 2026-05-11

### Changed

- feat(deps): bump civiccore pin to v1.1.0 and use shared `staff_key_gate` for timing-safe staff review queue auth.

## [0.2.0] - 2026-05-10

- Demoted the false v1.0.0 release label after the external CivicSuite audit found this module is a recovery/foundation module, not a canonical spec-complete v1 product.
- Preserved the useful recovery work while resetting the public package version to 0.2.0.
- Kept the CivicCore v1.0.0 wheel dependency and pinned it with SHA256 for release integrity.
- Supersedes the prior public v1.0.0 posture; do not treat v1.0.0 as production-ready or spec-complete.

All notable changes to CivicGrants will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-05-09

### Added

- CivicCore v1.0.0 release-wheel alignment.
- Staff-only grant review queue workflows protected by `CIVICGRANTS_STAFF_API_KEY`.
- Review-required CivicRecords/grant-file context packet endpoint.
- Adversarial local integration mocks for spoofed roles, official eligibility attempts, submission attempts, award acceptance, legal-advice claims, stale context, and live funder-feed claims.
- v1.0.0 docs, tests, browser QA evidence, release verification, and installer-integration requirement tracking.

### Changed

- Public UI and runtime health/version surfaces now report the CivicGrants v0.2.0 productization lane.

## [0.1.1] - 2026-04-28

### Added

- Optional SQLAlchemy-backed grant opportunity and compliance-calendar records via `CIVICGRANTS_GRANT_DB_URL`.
- Compliance-calendar retrieval endpoint for persisted grant records.

### Changed

- Aligned CivicGrants to `civiccore==0.3.0` while preserving the v0.1 grant support foundation behavior.
- Updated release gates, CI wheel install, docs, tests, and browser-visible version copy for the v0.1.1 compatibility release.

## [0.1.0] - 2026-04-27

### Added

- FastAPI package/runtime foundation pinned to `civiccore==0.2.0`.
- Opportunity triage helper using deterministic sample data.
- Eligibility-factor matching helper with staff-verification boundary.
- Application outline helper with review-required boundary.
- Compliance calendar helper.
- Audit-ready grant file export checklist.
- Accessible public sample UI at `/civicgrants` with browser QA coverage.
- Release gate: tests, docs, placeholder import guard, Ruff, and build artifact checks.

### Not Shipped

- Live funder feeds, official eligibility decisions, legal advice, live LLM calls, submission portals, and grant system-of-record integrations.
