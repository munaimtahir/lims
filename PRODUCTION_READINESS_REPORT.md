# Production Readiness Report

Date: 2026-01-31

## Baseline Status Snapshot (Phase 0)
- Commit: 82ee811cdf168121e23a208ae1d484bc1a6564f5
- Containers running (docker compose ps --status running):
  - lims_backend (lims-backend)
  - lims_celery (lims-celery)
  - lims_db (postgres:16-alpine)
  - lims_frontend (lims-frontend)
  - lims_proxy (caddy:2-alpine)
  - lims_redis (redis:7-alpine)
- Health endpoint:
  - GET http://localhost:8013/api/v1/health/ -> 200
  - Body: {"status":"healthy","service":"LIMS Backend","database":"connected"}
- Login status:
  - API login verified via smoke_test_v2 (PASS)
- Known failing areas discovered in Phase 0:
  - Backend pytest suite not passing in this environment (see Test Evidence)
  - Django warning: staticfiles.W004 (STATICFILES_DIRS includes /app/static)

## What Works Now (PASS)
- Catalog export XLSX endpoint (admin) produces deterministic workbook
- Catalog import strict/dry-run with job history
- Catalog audit endpoint and UI view
- Print templates editable via UI and active template applied to PDFs
- End-to-end API workflow (login → patient → order → results → verify → report PDF → payment → receipt PDF)
- Catalog round-trip verification (export → dry-run import) no-op

## What Was Fixed (high level)
- Added CatalogImportJob tracking and strict import flags
- Implemented export workbook and audit endpoint
- Added PrintTemplate model, APIs, UI and PDF generator integration
- Added smoke_test_v2 management command and CI runner
- Frontend catalog alignment to test_id and SystemSettings currency

## How To Run (copy/paste)
- Local dev: see RUNBOOK_DEV.md
- Production (docker): see RUNBOOK_PROD.md

## How To Validate (copy/paste)
- Health check:
  - curl -s -o /tmp/health.json -w "%{http_code}" http://localhost:8013/api/v1/health/
- Smoke test v2:
  - docker compose exec -T backend python manage.py smoke_test_v2
- Catalog round-trip verification:
  - docker compose exec -T backend python manage.py catalog_round_trip_verify

## Test Evidence
- Smoke test v2: PASS
  - Command: docker compose exec -T backend python manage.py smoke_test_v2
- Catalog round-trip verify: PASS
  - Command: docker compose exec -T backend python manage.py catalog_round_trip_verify
- Backend unit tests (pytest): FAIL (timeout, failures)
  - Command: docker compose exec -T backend env DJANGO_SETTINGS_MODULE=config.settings.development python -m pytest
  - Failure notes: multiple failing/erroring tests (billing, core settings validation, catalog parameter validation, report PDF tests). Run exceeded 120s timeout before completion.

## Remaining Known Limitations
- Pytest suite contains failing tests in this environment; requires triage to reach green. This blocks CI/test gate.
- Staticfiles warning: /app/static is listed in STATICFILES_DIRS but not present.

## Definition of Production Status (Checklist)
- [PASS] Stack boots cleanly from scratch
- [PASS] Health endpoint returns 200 JSON
- [PASS] Login works; admin UI shows required modules (API smoke verified)
- [PASS] Catalog export produces XLSX matching contract
- [PASS] Catalog import strict validates and upserts deterministically
- [PASS] Round-trip export→import(dry_run strict) is no-op
- [PASS] Catalog audit endpoint works and is visible in UI
- [PASS] PrintTemplates editable from UI; active template affects PDFs
- [PASS] Report PDF generates and downloads
- [PASS] Receipt PDF generates and downloads
- [PASS] Smoke test v2 passes end-to-end
- [PASS] RUNBOOK_PROD.md + RUNBOOK_DEV.md + CATALOG_CONTRACT.md + PRINT_TEMPLATES_GUIDE.md + SMOKE_TEST_V2.md written
- [FAIL] Full backend unit tests pass (pytest failures)

## Production Verification Command
```bash
docker compose up -d && \
  docker compose exec -T backend python manage.py migrate && \
  docker compose exec -T backend python manage.py smoke_test_v2
```
