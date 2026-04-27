# CivicGrants Agent Contract

## Source of Truth

- Upstream suite spec: `CivicSuite/civicsuite/docs/CivicSuiteUnifiedSpec.md`, especially the CivicGrants catalog entry and suite-wide non-negotiables.
- CivicGrants supports opportunity triage, eligibility-factor matching, application outline support, compliance-calendar scaffolding, and audit-ready grant files.
- Staff own every decision.

## Hard Boundaries

- CivicGrants never determines official eligibility, submits applications, provides legal advice, or updates a grant system of record.
- CivicGrants v0.1.0 must not call live LLMs or live funder feeds.
- Application outlines and eligibility matches must be marked review-required.
- CivicGrants depends on CivicCore; CivicCore must never depend on CivicGrants.
- CivicGrants may reference CivicRecords concepts only through released contracts or deterministic sample data in v0.1.0.

## Verification

Run `bash scripts/verify-release.sh` before every push or release.
