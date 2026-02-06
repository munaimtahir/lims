# Release Gate Report (A: Backend Tests, B: Smoke)

## Detected Stack
- Backend: Django 5.0 / DRF, Python 3.12, Celery, Redis
- DB: Postgres (runtime), tests configured for SQLite (config.settings.ci)
- Frontend: React/Vite (not exercised in this gate)
- Orchestration: docker-compose (services: db, redis, backend, celery, frontend, proxy)

## Environment Summary
- OS: Linux vps.us-central1-f.c.munaimfinance.internal 6.14.0-1021-gcp x86_64
- Python: 3.12.3 (system), venv at lims-backend/.venv
- Node: v20.20.0 / npm 11.8.0
- Docker: 29.2.1, Docker Compose: v5.0.2
- Running services (docker compose ps): db (healthy), redis (healthy), backend (healthy, port 8000), celery, frontend, proxy

## Commands Executed (chronological)
1. `python3 -m venv .venv` (lims-backend)
2. `. .venv/bin/activate && pip install --upgrade pip`
3. `. .venv/bin/activate && pip install -r requirements/development.txt`
4. `. .venv/bin/activate && SECRET_KEY=testkey DB_PASSWORD=testpass ALLOWED_HOSTS=localhost,127.0.0.1 CORS_ALLOWED_ORIGINS=http://localhost CSRF_TRUSTED_ORIGINS=http://localhost DJANGO_SETTINGS_MODULE=config.settings.ci pytest -q` (full run, failed)
5. `. .venv/bin/activate && ... pytest -q --maxfail=1` (captured to artifact)
6. `ALLOWED_HOSTS=localhost SECRET_KEY=dummy DB_PASSWORD=dummy CORS_ALLOWED_ORIGINS=http://localhost CSRF_TRUSTED_ORIGINS=http://localhost docker compose ps`
7. Smoke/integration curls against http://localhost:8000 (health, login, patients) and `docker exec lims_db pg_isready` (outputs in artifacts)

## Gate A1 — Backend Unit Tests
- Status: **FAIL**
- Command: see #5 above and latest run (output in `ARTIFACTS/gate_A_unit.txt`)
- Fix attempts made:
  - Switched CI settings to allow Postgres test DB via `TEST_DB_*` env (fallback SQLite).
  - Disabled `SECURE_SSL_REDIRECT` in CI to avoid HTTP→HTTPS redirects.
  - Installed `whitenoise` (missing dependency) via requirements/development.txt.
  - Ran tests against dedicated Postgres test DB (container).
- Current failure summary:
  - 70 failures + 22 errors; core issue is schema mismatch between tests and models (e.g., tests expect `ReferenceRange` fields `min_value`/`max_value`/`min_critical`/`max_critical`, but model uses `reference_min`/`reference_max`/`critical_low`/`critical_high`), plus multiple downstream failures in reports/results/samples/orders tied to these fields and related fixtures.
  - Addressing requires aligning models/fixtures/tests; out of scope for quick infra-only adjustments.

## Gate A2 — Light API Integration
- Status: **PASS**
- Evidence: `ARTIFACTS/gate_A_integration.txt`
  - /api/v1/health returns 200 healthy (DB connected)
  - Login succeeded with admin/admin123 returning JWT
  - Authenticated GET /api/v1/patients/ returned 200 with data

## Gate B — Smoke Checks
- Status: **PASS** (note: root `/` returns 404 from backend, expected since SPA served via proxy; health/login/admin all responsive)
- Evidence: `ARTIFACTS/gate_B_smoke.txt`
  - Base `/` 404 (expected for API container)
  - /api/v1/health 200 healthy
  - /admin redirects to login (302)
  - /api/v1/auth/login 200
  - `docker exec lims_db pg_isready -U postgres` -> accepting connections

## Next-Step Fixes
1. Align tests and models for lab/results/reference ranges (rename/alias fields or update fixtures) so schema matches expectations.
2. Keep using dedicated Postgres test DB via `TEST_DB_*` env for fidelity; ensure migrations reflect current models.
3. Rerun pytest after schema/test alignment to clear remaining failures.

## Artifacts
- `ARTIFACTS/gate_A_unit.txt` — pytest output (fail at migrate foreign key mismatch)
- `ARTIFACTS/gate_A_integration.txt` — health/login/patients responses
- `ARTIFACTS/gate_B_smoke.txt` — smoke curls + pg_isready

## TODO Checklist
- [ ] Gate A1 pass
- [ ] Gate A2 pass (current: pass)
- [ ] Gate B pass (current: pass)
- [ ] Known blockers listed (foreign key mismatch on SQLite migrations)
- [ ] Ready for Gate C (Playwright)
