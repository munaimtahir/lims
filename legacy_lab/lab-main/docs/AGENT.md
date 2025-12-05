# Final AI Developer Prompts (Stage-by-Stage)
The following prompts are designed for an autonomous AI dev agent. Run them one stage at a time. Each stage must keep 100% coverage and green CI.

---
## Stage 0 — Repo & CI Bootstrap (no app code)
**Mission:** Initialize a mono-repo with backend/, frontend/, infra/, docs/ and GitHub Actions CI. No business code yet.

**Requirements:**
- Add Python and Node toolchains with `uv`/`pip-tools` and `pnpm` lockfiles.
- Pre-commit hooks: black, isort, ruff, mypy (backend), eslint, prettier, typecheck (frontend).
- GitHub Actions workflows:
  - `ci.yml` running: lint, type-check, test (placeholder passes), coverage check 100% (temporary with 1 trivial test), build docker images (placeholders).
- Create placeholder packages:
  - backend: Django app skeleton with a single "health" test that passes.
  - frontend: Vite React TS skeleton with a single passing test.
- Ensure coverage gates are set to 100 (temporary single-test still passes).

**Deliverables:**
- Green CI on PR.
- README badges for CI status and coverage.

---
## Stage 1 — Backend: Patient Registration API
**Mission:** Implement `Patient` model + REST endpoints with 100% tests.

**Tech:**
- Django 5, DRF, PostgreSQL 16.
- Pytest, factory_boy, freezegun, pytest-cov.

**Scope:**
- Model fields: mrn (unique), full_name, father_name, dob, sex, phone, cnic, address, timestamps.
- Serializers with strong validation (CNIC format, phone format, DOB not in future).
- Endpoints:
  - `POST /api/patients/` (create)
  - `GET /api/patients` (search by name/phone/cnic prefix)
- Pagination, ordering, created_at desc by default.
- Error envelope: `{error:{code,message,details}}`.

**Tests (100%):**
- Model validation tests for each field edge case.
- API tests for create/search, all branches (success, invalid, duplicates).
- Performance: ensure query counts are controlled (use django-test-plus or pytest-django assertions).
- Coverage fail-under=100.

**Infra:**
- Add postgres service in docker-compose; run migrations automatically on start.
- Seed command to create 5 sample patients for local dev.

---
## Stage 2 — Frontend: Patient Registration UI
**Mission:** Build a React form for patient registration and a results table.

**Tech:**
- React 18, Vite, TS, React Query, React Hook Form, Zod.
- Vitest + Testing Library for unit tests; Playwright for e2e.

**Scope:**
- Page: `/patients` with two tabs: "Register" (form) and "Search" (table).
- Form validation mirrored with Zod (same constraints as backend).
- API client with fetch wrapper and typed responses.
- Toasts on success/error; loading states and empty results UX.

**Tests (100%):**
- Unit: form validation branches and API client error paths.
- e2e: register patient, then search and see the row.

**Accessibility:**
- Labels, keyboard navigation, role attributes verified in tests.

---
## Stage 3 — Auth & RBAC
**Mission:** Email+password auth, roles: Admin, Reception, Phlebotomy, Technologist, Pathologist.

**Backend:**
- Django auth + JWT (simplejwt).
- Endpoints: login/refresh/logout; role claims in JWT.
- Permissions on patient endpoints (Reception/Admin only).

**Frontend:**
- Auth pages, protected routes, token refresh, logout.
- Hide/show UI by role.

**Tests:**
- Backend: permissions matrix, token expiry/refresh.
- Frontend: route guards and role-based rendering.

---
## Stage 4 — Orders & Test Catalog
**Mission:** Create Orders and OrderItems from a catalog.

**Backend:**
- Models: Order, OrderItem, TestCatalog (seed dataset).
- Endpoint: POST /api/orders with items; GET /api/orders/:id.
- State: NEW → COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED.

**Frontend:**
- Order builder UI: pick patient, choose tests, submit.
- Order details page.

**Tests:** 100% across branches.

---
## Stage 5 — Sample Collection
- Sample entity with barcode; collect/receive timestamps.
- UI to mark collected/received; printable barcode.
- Tests 100%.

---
## Stage 6 — Result Entry & Verification
- Result model per OrderItem; units, ranges; flags.
- Dual verification: technologist enter, pathologist verify → publish.
- Tests: state machine branches, invalid transitions.

---
## Stage 7 — Reporting (PDF)
- PDF renderer with the standardized lab template (signatories).
- History/audit trail on publish.
- Tests: PDF generation deterministic snapshot tests.

---
## Quality Gates (All Stages)
- Coverage fail-under=100 for both backend and frontend.
- Type-check clean, linters clean.
- Docker images build and run smoke tests.
