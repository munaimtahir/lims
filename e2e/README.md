# E2E Playwright Suite (Gate S6)

## Quickstart (local)
1) `cd e2e`
2) `npm ci`
3) `cp .env.example .env` and set `BASE_URL`, `E2E_USER_EMAIL`, `E2E_USER_PASSWORD`
4) Seed test users (one-time, dev only): `docker compose exec backend python manage.py seed_smoke_users`
5) `npx playwright install --with-deps chromium`
6) Smoke: `npm run test:smoke`
7) Regression (optional): `npm run test:regression`

## Auth strategy (storageState)
- Global setup logs in once with creds from `.env` and writes `.auth/storageState.json`.
- All tests reuse that authenticated state; no creds are hard-coded in specs.
- To refresh state: delete `e2e/.auth` and re-run tests (global setup recreates it).

## Selector & POM policy
- No inline selectors in specs; use `utils/selectors.ts`.
- Prefer `data-testid`; fallback to role/text only if no stable hook exists.
- Page Objects live in `pages/`; waits go through `utils/waiters.ts` (no sleeps).

## Structure
- `playwright.config.ts` Root config (dotenv, retries, artifacts)
- `tests/smoke` Smoke suite (3 flows + detail open)
- `tests/regression` Light regression tags
- `pages/` POMs (`BasePage`, `LoginPage`, `DashboardPage`, `ResultsPage`)
- `fixtures/auth.setup.ts` storageState generation
- `utils/` selectors, waiters, asserts, testdata
- `artifacts/` test-results, traces, screenshots, videos, html report

## Env & test data
- `.env.example` documents required vars:
  - `BASE_URL` (default http://localhost:8012)
  - `E2E_USER_EMAIL`, `E2E_USER_PASSWORD`
  - `E2E_ALLOW_WRITES` (default false; gate risky writes)
- Test user provisioning: run `docker compose exec backend python manage.py seed_smoke_users`

## CI notes
- Headless chromium only; retries=2 on CI, 0 locally.
- Artifacts: `e2e/artifacts/test-results`, `e2e/artifacts/playwright-report`.
- Commands:
  - `npm run test:smoke`
  - `npm run test:regression`
  - `npx playwright show-report e2e/artifacts/playwright-report`
