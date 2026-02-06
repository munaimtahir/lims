# E2E Playwright Runbook

## Prerequisites
- Node 20+, npm
- Docker & docker compose (stack at http://localhost:8012)
- Playwright browsers: `npx playwright install --with-deps chromium`

## Environment
- Copy `e2e/.env.example` to `e2e/.env` and set:
  - `BASE_URL` (default `http://localhost:8012`)
  - `E2E_USER_EMAIL` / `E2E_USER_PASSWORD`
  - `E2E_ALLOW_WRITES` (defaults to false; guards risky ops)

## Auth strategy
- Storage state (Option B). `fixtures/auth.setup.ts` logs in once using env creds and writes `e2e/.auth/storageState.json`.
- Tests reuse the state; delete `e2e/.auth` to force regeneration.

## Test user provisioning
- Use built-in seed command (dev only):
  - `docker compose exec backend python manage.py seed_smoke_users`
- Default smoke user used here: `admin@example.com` / `admin123` (set in `.env`).

## How to run
- Smoke: `cd e2e && npm run test:smoke`
- Regression: `cd e2e && npm run test:regression`
- All: `cd e2e && npm test`

## Artifacts
- Test results: `e2e/artifacts/test-results/`
- HTML report: `e2e/artifacts/playwright-report/`
- Traces/screens/videos: under `e2e/artifacts/` (on failure or first retry traces).
- CI should archive `e2e/artifacts/**`.

## Debugging failures
- Open HTML report: `npx playwright show-report e2e/artifacts/playwright-report`
- Open trace: `npx playwright show-trace e2e/artifacts/test-results/<trace>.zip`
- Re-run a single test: `npx playwright test tests/smoke/smoke.results.spec.ts -g "open first result detail"`

## CI notes
- Headless chromium only; retries=2 in CI (configured via `process.env.CI`).
- `forbidOnly` enabled in CI.
- Output dir: `e2e/artifacts/test-results`.

## Tags
- Smoke tests tagged `@smoke`
- Regression tests tagged `@regression`
