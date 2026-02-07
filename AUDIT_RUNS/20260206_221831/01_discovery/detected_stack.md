# Stack Detection

## Backend
- Framework: Django 5.0.0 with DRF (manage.py, config/settings, requirements/base.txt)
- Tests: pytest with pytest-django (lims-backend/pytest.ini, DJANGO_SETTINGS_MODULE=config.settings.ci)
- Format/Lint: black, flake8, isort listed in requirements/development.txt; no ruff/mypy configs found.
- Type checking: none configured (no mypy/pyproject.toml).

## Frontend
- Framework: Vite 7 + React 19 + TypeScript (~5.9) (frontend/package.json, vite.config.ts).
- Lint: eslint scripts (`npm run lint`).
- Format: no prettier dependency detected.
- Type-check: `npm run type-check` (tsc --noEmit).
- Unit tests: Vitest (`npm run test`, `vitest.config.ts`).

## E2E
- Playwright (@playwright/test ^1.48.2) located in `e2e/` with `playwright.config.ts`.
- Base URL default: http://localhost:8012 (BASE_URL env override).
- Storage state: `e2e/.auth/storageState.json` via globalSetup `fixtures/auth.setup.ts`.
- Reports: HTML to `e2e/artifacts/playwright-report`, traces/screenshots enabled on failure.

## Docker
- Compose files: docker-compose.yml, docker-compose.override.yml (root).
- Services: db (Postgres 16), redis, backend (Django), celery, frontend (Vite build served), proxy (Caddy) with network `lims_network` and volumes (lims_pgdata, redis_data, static_files, caddy_data, caddy_config).
- Requires env vars: SECRET_KEY, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, DB_PASSWORD, etc. .env.production.example referenced (not present).

## Package Managers
- Frontend: package-lock.json present (also pnpm-lock.yaml) -> defaulting to npm.
- E2E: package-lock.json -> npm.
- Backend: requirements/*.txt -> pip/venv (no poetry).
