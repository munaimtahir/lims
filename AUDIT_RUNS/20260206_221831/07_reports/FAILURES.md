# Failures & Skips

1) **Python dependencies vulnerable**
   - Excerpt: pip-audit reports Django 5.0 multiple CVEs (e.g., PYSEC-2025-13, CVE-2025-64459) and djangorestframework-simplejwt CVE-2024-22513; 43 vulns total (see pip_audit.txt).
   - Likely cause: requirements pinned to old versions.
   - Fix plan: bump Django to >=5.2.8 (latest LTS), DRF to >=3.15.2, simplejwt >=5.5.1, and refresh all pins; rerun safety/pip-audit.
   - Rerun: `source AUDIT_RUNS/20260206_221831/.venv/bin/activate && pip-audit`

2) **Backend formatting failed**
   - Excerpt: black would reformat 123 files including apps/core/models.py (see backend_format.txt).
   - Likely cause: code not formatted per black/isort.
   - Fix plan: run `black .` and `isort .` in lims-backend, commit changes.
   - Rerun: `source AUDIT_RUNS/20260206_221831/.venv/bin/activate && cd lims-backend && black --check . && isort --check-only .`

3) **Backend lint failed (flake8)**
   - Excerpt: line-length and whitespace issues e.g., apps/accounts/management/commands/create_demo_users.py:26 E501 (backend_lint.txt).
   - Likely cause: style guide not enforced recently.
   - Fix plan: wrap long lines, trim trailing whitespace, align with flake8 config; consider enabling formatter in CI.
   - Rerun: `source AUDIT_RUNS/20260206_221831/.venv/bin/activate && cd lims-backend && flake8 --exclude .venv,media,staticfiles`

4) **Frontend lint failed (eslint)**
   - Excerpt: unused vars and parsing error at src/pages/print/PrintReceiptPage.tsx:164 `Parsing error: ')' expected`; unused vars in CollectionWorklistPage.tsx (frontend_lint.txt).
   - Likely cause: stale/unfinished code.
   - Fix plan: fix syntax in PrintReceiptPage, remove unused imports/variables, address react-hooks warning in ResultsPage setState in effect, rerun lint.
   - Rerun: `cd frontend && npm run lint`

5) **Django migrations check failed**
   - Excerpt: makemigrations --check generated orders 0006 and patients 0005; also DB connection refused to localhost:5432 (backend_migrations_check.txt).
   - Likely cause: model changes not committed and DB not running for consistency check.
   - Fix plan: bring DB up (docker compose), create and commit migrations, rerun check.
   - Rerun: `source AUDIT_RUNS/20260206_221831/.venv/bin/activate && cd lims-backend && python manage.py makemigrations --check --dry-run`

6) **Backend tests failed (pytest)**
   - Excerpt: ValueError "CRITICAL: SECRET_KEY environment variable must be set in production." during pytest startup (backend_unit_pytest.txt).
   - Likely cause: SECRET_KEY not provided for test settings; settings expect env var.
   - Fix plan: set SECRET_KEY (and any other required envs) for test env, possibly adjust settings.ci to supply default for tests.
   - Rerun: `SECRET_KEY=dummy source AUDIT_RUNS/20260206_221831/.venv/bin/activate && cd lims-backend && pytest`

7) **Bandit security scan failed**
   - Excerpt: hardcoded password in apps/samples/tests/test_services.py:24 and try/except pass in config/settings/production.py:377; thousands of issues flagged (bandit.txt).
   - Likely cause: test fixtures with literal secrets and broad exception handling; bandit scanning entire tree with default profiles.
   - Fix plan: replace test passwords with fixtures/env, handle exceptions explicitly, tune bandit config to exclude generated assets; rerun.
   - Rerun: `source AUDIT_RUNS/20260206_221831/.venv/bin/activate && cd lims-backend && bandit -r . -x .venv,node_modules,staticfiles,media,logs`

8) **Safety scan reported vulnerabilities**
   - Excerpt: safety check found 30 vulnerabilities (pip_safety.txt).
   - Likely cause: same outdated Python dependencies as pip-audit.
   - Fix plan: update requirements; rerun safety.
   - Rerun: `source AUDIT_RUNS/20260206_221831/.venv/bin/activate && safety check --full-report`

9) **Semgrep skipped**
   - Reason: semgrep CLI not installed in environment; no repo config found.
   - Fix plan: install semgrep (`pip install semgrep`) and run with `semgrep --config auto` or project ruleset.
   - Rerun: `semgrep --config auto` (from repo root)
