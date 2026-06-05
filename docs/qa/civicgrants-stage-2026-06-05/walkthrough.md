# CivicGrants Stage Walkthrough

## Executive Summary

The `/civicgrants` interface is wired to the application-outline API and works in desktop and mobile Chromium checks. The page renders a real draft form, submits to `/api/v1/civicgrants/applications/outline`, displays returned narrative sections, and keeps the no-official-action boundary visible. No interface wiring findings remain.

## Methodology

- Reviewed README, user manual, route definitions, public UI source, persistence code, importer code, readiness code, and tests.
- Launched `civicgrants.main:app` locally on `127.0.0.1:18170`.
- Used Playwright Chromium at 1440x1000 and 390x844.
- Captured screenshots and network/console evidence.
- Exercised `/`, `/health`, `/ready`, `/api/v1/civicgrants/readiness`, valid application outline, and invalid application outline.

## Findings By Severity

None.

## Broken Or Suspicious Wiring Map

| UI element or workflow | Expected system connection | Actual connection | Status | Evidence |
| --- | --- | --- | --- | --- |
| Draft form | POST application outline API | `fetch("/api/v1/civicgrants/applications/outline")` | Pass | Outline sections rendered |
| Invalid outline API | 422 actionable validation | Missing `city_need` returned 422 with `fields: ["city_need"]` | Pass | `walkthrough-evidence.json` |
| Mobile layout | No horizontal overflow | `document.documentElement.scrollWidth <= window.innerWidth` | Pass | desktop/mobile evidence |

## Confidence And Gaps

High confidence for the local CivicGrants module gate. This walkthrough does not claim suite-level bare-metal installer readiness or cross-module end-to-end packaging readiness.

## Appendix

- Screenshot: `docs/qa/civicgrants-stage-2026-06-05/public-desktop.png`
- Screenshot: `docs/qa/civicgrants-stage-2026-06-05/public-mobile.png`
- Evidence JSON: `docs/qa/civicgrants-stage-2026-06-05/walkthrough-evidence.json`
- `python -m pytest -q` - 36 passed.
- `bash scripts/verify-release.sh` - PASSED.
