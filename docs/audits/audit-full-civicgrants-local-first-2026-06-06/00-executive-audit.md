# CivicGrants Local-First Stage Audit

**Date:** 2026-06-06  
**Branch:** `stage-civicgrants-release-readiness-2026-06-05`  
**Scope:** Full five-role audit of CivicGrants local-first persistence, public/staff UIs, docs, tests, release verification, and walkthrough evidence.  
**Posture:** Release gate.

## Executive Summary

CivicGrants passes this stage audit. The module now ships as a clerk-usable local-first grant support product slice: default local SQLite persistence, seeded readiness, staff review queues, public and staff UIs, suite integration contract metadata, honest docs, behavioral tests, release verification, and Playwright walkthrough evidence all align. The remaining work is outside this module repo: pin this source head in the umbrella installer, verify suite contracts there, and prove the clean-machine gate.

## Severity Rollup

- Blocker: 0
- Critical: 0
- Major: 0
- Minor: 0
- Nit: 0

## Findings

No findings.

## What's Working Well

- Local-first runtime: default local DB creation, seeded opportunity records, persisted application review IDs, persisted compliance IDs, and explicit-database no-seed behavior are covered by tests.
- Integration readiness: `/api/v1/civicgrants/integration-contracts` names the downstream contracts that the suite installer can verify.
- UI wiring: public and staff routes render, the public draft action calls the backend, and the staff route exposes both queue loading and actionable unauthenticated feedback.
- Documentation: README, user manual, generated text mirrors, docs index, changelog, and release gate all describe the current local-first behavior.
- Verification: `bash scripts/verify-release.sh` passed with tests, docs gate, placeholder import check, Ruff, and package build. Playwright evidence is recorded under `docs/qa/civicgrants-local-first-2026-06-06`.

## This-Sprint Punch List

- Pin CivicGrants source commit in the umbrella installer.
- Add umbrella installer environment setup for `CIVICGRANTS_DATA_DIR` and the local staff key.
- Add umbrella verifier checks for CivicGrants readiness and integration contracts.
- Send the clean-machine tester a repo-channel directive for CivicGrants standalone and suite integration.

## Next-Sprint Watchlist

- Add city-import UX for replacing seeded starter opportunities after the full suite installer is proven.
- Consider staff assignment/search filters once real clerk feedback arrives.
- Keep the explicit-database no-seed behavior protected when supporting non-SQLite city deployments.

## Blast-Radius Notes

- Installer blast radius: CivicGrants is now ready by default, so the suite installer must provide an isolated module data directory to avoid writing runtime files into the package checkout.
- Downstream blast radius: CivicRecords and CivicProcure should consume the named contract metadata rather than inferring endpoints from docs.
