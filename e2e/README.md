# E2E Playwright Suite

## Quickstart (local)
1) `cd e2e`
2) `npm install` (or `npm ci`)
3) `cp config/env.example .env` and set `BASE_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`
4) `npx playwright install --with-deps chromium`
5) `npx playwright test tests/smoke.spec.ts`

## Conventions (AI + human friendly)
- One test = one intent; keep specs short.
- Use Page Objects (extend `BasePage`); no inline selectors in specs.
- Selectors live in `utils/selectors.ts` (use data-testid/stable hooks).
- No `waitForTimeout`; all waits go through `utils/waiters.ts`.
- One assertion per logical step with clear message.
- Env-driven base URL via `BASE_URL`; secrets stay in `.env`.
- Artifacts on failure: screenshots, videos, traces, HTML report under `artifacts/`.

## Structure
- `config/` Playwright config and env template
- `tests/` Spec files
- `pages/` Page Objects (`BasePage`, feature pages)
- `fixtures/` Reusable fixtures (e.g., `authenticatedPage`)
- `data/` Static test data (non-secret)
- `utils/` Selectors, waiters, assertions helpers
- `artifacts/` Test outputs (screens, videos, traces, html report)

## CI notes
- Install deps: `npm ci`
- Install browsers: `npx playwright install --with-deps chromium`
- Run headless: `npx playwright test`
- Export env: `BASE_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`
- Upload `artifacts/` as workflow artifact
