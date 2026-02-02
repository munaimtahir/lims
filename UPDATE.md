# Update Summary

Date: 2026-01-31
Repository: /home/munaim/srv/apps/lims

## What was done
- Booted the Docker stack and applied migrations.
- Ensured a superuser exists (`admin/admin123`).
- Seeded minimal catalog data if empty.
- Implemented catalog import/export/audit (strict, deterministic, job history, round-trip safe).
- Added `CatalogImportJob` model + endpoints.
- Added catalog export endpoint (XLSX) and audit endpoint + UI summary view.
- Implemented PrintTemplate model, defaults, API, and admin UI; PDF generators now use active templates.
- Added PDF generation tests (report + receipt) and catalog IO tests.
- Implemented `smoke_test_v2` management command and documented usage.
- Fixed frontend catalog field mismatches (test_id), added import/export UX, audit view, and currency display from SystemSettings.
- Added/updated runbooks, catalog contract, print templates guide, smoke test guide, and production readiness report.

## Commands executed and results
- `docker compose up -d` -> stack booted.
- `docker compose exec -T backend python manage.py migrate` -> migrations applied.
- `docker compose exec -T backend python manage.py seed_minimal_catalog` -> catalog seeded.
- `curl -s http://lims.alshifalab.pk:8012/api/v1/health/` -> 200 JSON.
- `docker compose exec -T backend python manage.py catalog_round_trip_verify` -> PASS.
- `docker compose exec -T backend python manage.py smoke_test_v2` -> PASS.
- `docker compose exec -T backend env DJANGO_SETTINGS_MODULE=config.settings.development python -m pytest` -> FAIL (timeout/known failures).

## Current status (high level)
- Stack boots and health endpoint returns 200 JSON.
- Login works; admin UI loads.
- Catalog import/export/audit endpoints are live and deterministic.
- Print templates are editable from UI and affect PDFs.
- End-to-end smoke test v2 passes.
- Full pytest suite is still failing (reported as FAIL in production readiness report).

## Files created/updated (key)
- `RUNBOOK_PROD.md`, `RUNBOOK_DEV.md`
- `CATALOG_CONTRACT.md`, `PRINT_TEMPLATES_GUIDE.md`
- `SMOKE_TEST_V2.md`, `PRODUCTION_READINESS_REPORT.md`
- `lims-backend/apps/laboratory/catalog_io.py`
- `lims-backend/apps/laboratory/models.py` (CatalogImportJob)
- `lims-backend/apps/core/models.py` (PrintTemplate)
- `lims-backend/apps/core/management/commands/smoke_test_v2.py`
- Frontend catalog and settings updates (import/export/audit/print templates)
- Tests for catalog IO and PDF generation

## Notable changes to tooling/scripts
- `scripts/run_ci.sh` now installs dev requirements and runs pytest with dev settings.
- `lims-backend/requirements/base.txt` includes `requests==2.31.0` for smoke test client.

## Open issues
- Full pytest suite still failing; see `PRODUCTION_READINESS_REPORT.md` for details.
