# Audit Dashboard (20260206_221831)

| Gate | Status | Evidence |
| --- | --- | --- |
| Node deps audit (frontend/e2e) | PASS | 02_dependencies/node_audit.txt |
| Python deps audit | FAIL | 02_dependencies/pip_audit.txt, 05_security/pip_safety.txt |
| Backend format (black/isort) | FAIL | 03_format_lint/backend_format.txt |
| Backend lint (flake8) | FAIL | 03_format_lint/backend_lint.txt |
| Backend type-check | SKIPPED | 03_format_lint/backend_typecheck.txt |
| Frontend format (prettier) | SKIPPED | 03_format_lint/frontend_format.txt |
| Frontend lint (eslint) | FAIL | 03_format_lint/frontend_lint.txt |
| Frontend type-check (tsc) | PASS | 03_format_lint/frontend_typecheck.txt |
| Django system check | PASS | 04_tests/backend_django_checks.txt |
| Django migrations check | FAIL | 04_tests/backend_migrations_check.txt |
| Backend unit tests (pytest) | FAIL | 04_tests/backend_unit_pytest.txt |
| Frontend unit tests (vitest) | PASS | 04_tests/frontend_unit.txt |
| E2E Playwright smoke | PASS | 04_tests/e2e_playwright_smoke.txt |
| Security scan (bandit) | FAIL | 05_security/bandit.txt |
| Semgrep | SKIPPED | 05_security/semgrep.txt (missing tool) |
| Runtime docker compose | PASS | 06_runtime/docker_compose_config.txt, 06_runtime/docker_compose_up.txt |
| Runtime health/API smoke | PASS | 06_runtime/healthchecks.txt, 06_runtime/api_smoke_curl.txt |
