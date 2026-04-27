# Changelog

All notable changes to CivicGrants will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
