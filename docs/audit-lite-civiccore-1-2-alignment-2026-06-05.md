# Audit Lite - CivicCore 1.2.0 Alignment

**Date:** 2026-06-05
**Scope:** CivicGrants CivicCore dependency alignment slice.

## Verdict

Pass. The slice updates CivicGrants' current runtime dependency to the published CivicCore 1.2.0 wheel and makes the dependency contract mutation-visible in tests.

## Findings

None.

## Behavioral Coverage

- `tests/test_runtime_foundation.py` asserts `/health` reports `civiccore_version` as `1.2.0`.
- `tests/test_runtime_foundation.py` asserts `pyproject.toml` uses the exact CivicCore 1.2.0 release wheel URL and SHA256.
- Current-facing docs describe CivicCore 1.2.0 instead of earlier release-wheel pins.

## Verification

- `python -m pytest tests/test_runtime_foundation.py -q` - 5 passed.
- `python -m pytest -q` - 24 passed.
