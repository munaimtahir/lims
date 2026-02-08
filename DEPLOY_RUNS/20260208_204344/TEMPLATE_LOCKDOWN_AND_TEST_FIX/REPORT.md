# Template Lockdown + Test Fix Report

Timestamp: 2026-02-08 20:43 (ts: 20260208_204344)

## Step 1 — Visual QA (PNG renders)
Artifacts:
- `DEPLOY_RUNS/20260208_204344/TEMPLATE_LOCKDOWN_AND_TEST_FIX/report_sample_pages/report_sample_page-1.png`
- `DEPLOY_RUNS/20260208_204344/TEMPLATE_LOCKDOWN_AND_TEST_FIX/report_sample_pages/report_sample_page-2.png`
- `DEPLOY_RUNS/20260208_204344/TEMPLATE_LOCKDOWN_AND_TEST_FIX/report_sample_pages/report_sample_page-3.png`

Checklist:
- Header: logo not distorted; lab name/address/phone aligned; no overlap — PASS (no logo set; header aligned)
- Demographics table: borders clean; no clipped text; “—” for missing — PASS
- Results table: columns align; long names wrap; no overflow — PASS
- Footer: disclaimer + both signatories visible; page numbering correct — PASS
- Multi-page: header/page number repeat; table continues cleanly — PASS

Notes: Disclaimer/signatories appear on the final page; page numbering appears on every page.

## Step 2 — `parameters_active_idx` migration fix
Root cause: migration `0006_rename_parameters_active_idx_parameters_active_6dece1_idx` attempted to rename a missing index in fresh test DBs.
Fix: made the migration idempotent with a guarded `DO $$ ... $$` block and `CREATE INDEX IF NOT EXISTS`.

Updated migration:
- `lims-backend/apps/laboratory/migrations/0006_rename_parameters_active_idx_parameters_active_6dece1_idx.py`

## Commands run + outputs
Saved logs:
- `01_git_status.txt`
- `02_git_head.txt`
- `03_compose_ps.txt`
- `04_db_index_check.txt`
- `05_showmigrations.txt`
- `06_migrate_plan.txt`
- `07_pytest_reports.txt`

Pytest (container):
- Command: `docker compose exec -T backend pytest apps/reports/tests -q`
- Result: 34 passed, 4 warnings (see `07_pytest_reports.txt`)

## Artifacts
- Sample PDF: `DEPLOY_RUNS/20260208_204344/TEMPLATE_LOCKDOWN_AND_TEST_FIX/report_sample.pdf`
- Page renders: `DEPLOY_RUNS/20260208_204344/TEMPLATE_LOCKDOWN_AND_TEST_FIX/report_sample_pages/`
