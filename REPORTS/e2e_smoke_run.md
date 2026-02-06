# E2E Smoke Run Report (Playwright)

## Date/Time
- Sat Feb 07 02:16:10 PKT 2026 (PKT)

## Environment
- OS/kernel: Linux vps.us-central1-f.c.munaimfinance.internal 6.14.0-1021-gcp #22~24.04.1-Ubuntu SMP Sat Nov 22 06:23:18 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
- Node version: v20.20.0
- npm version: 11.8.0
- Playwright version: 1.58.1
- Docker version: Docker version 29.2.1, build a5c7197
- Docker Compose version: v5.0.2

## App Target
- Base URL: http://localhost:8012
- Reachability: HTTP 200 OK via `curl -I`

## Commands Executed
- cd e2e && node -v; npm -v; npm ls @playwright/test; npx playwright --version (logged to ARTIFACTS/e2e_discovery_diagnosis.txt)
- cd e2e && npx playwright test tests/_sanity.spec.ts --reporter=list
- cd e2e && npx playwright test tests/smoke --reporter=list | tee ../ARTIFACTS/e2e_stabilized.txt
- date

## Test Scope
- Suites: e2e/tests/_sanity.spec.ts, e2e/tests/smoke
- Auth strategy: storageState-based session (globalSetup logs in to seed storageState)

## Results Summary
- Total tests: 5
- Passed: 5
- Failed: 0
- Skipped: 0
- Runtime duration: ~10s total
- Conclusion: PASS — smoke and sanity suites executed cleanly

## Failures
- None

## Artifacts
- ARTIFACTS/e2e_discovery_diagnosis.txt
- ARTIFACTS/e2e_stabilized.txt
- e2e/artifacts/test-results/
- e2e/artifacts/playwright-report/

## Notes
- Added minimal harness test `tests/_sanity.spec.ts` to validate runner execution independent of app state.
