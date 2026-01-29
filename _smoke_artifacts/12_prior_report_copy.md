# Smoke Test Report: Current State
**Date:** 2026-01-29 (UTC)
**Environment:** Linux / Docker Compose
**Verdict:** ⚠️ PARTIALLY READY

---

## 1. Executive Summary
The system is **functionally consistent** but required critical configuration repairs during verification. The core stack is healthy, and the application now aligns with the external production proxy (Host Caddy) on **Port 8013** (previously mismatched on 8012).

However, automatic verification via scripts **FAILS** due to API schema drift (scripts expect `id` field, API returns `test_id` or similar mappings). The **Frontend Build** also required a patch to bypass strict TypeScript checks.

## 2. What Was Tested

| Area | Status | Notes |
|------|--------|-------|
| **Environment** | ✅ PASS | Repo integrity confirmed. `.env.example` present. |
| **Docker Stack** | ✅ PASS | All services healthy. **Port corrected to 8013** to match Host Caddy. |
| **Migrations** | ✅ PASS | Database migrations applied cleanly. |
| **Seeding** | ✅ PASS | Test catalog and demo users seeded successfully. |
| **Frontend Build** | ⚠️ PATCHED | **FAILED** initially. Required patching `RegistrationPage.tsx` to fix unused variable error. |
| **Frontend Serving** | ✅ PASS | Accessible via Proxy at `http://localhost:8013/` (Corrected). |
| **Backend Tests** | ❌ FAIL | `pytest` not installed in production `lims-backend` image. |
| **Public API** | ⚠️ DRIFT | Login/Patient works. Fails listing tests due to `id` vs `test_id` key mismatch. |
| **Internal API** | ⚠️ DRIFT | Order creation works. Fails result entry due to `parameter_id` key mismatch. |
| **API Probes** | ⚠️ INFO | Confirmed Public API returns `test_id` (no `id`) and returns 400 for param filter. |

## 3. Verification Table

| Check | Expected | Actual | P/F | Evidence |
|-------|----------|--------|-----|----------|
| **Repo Fingerprint** | Git/Files | Present | ✅ | `02_repo_fingerprint.txt` |
| **Docker Build** | Success | **Failed** (Frontend TS) | ❌ | `11_compose_build_retry.txt` |
| **Docker Health** | Healthy | Healthy (All 6) | ✅ | `13_compose_ps.txt` |
| **Migrations** | Applied | Applied | ✅ | `20_migrate.txt` |
| **Health (Internal)** | 200 OK | 200 OK | ✅ | `21_health_internal.txt` |
| **Health (Public)** | 200 OK | 200 OK | ✅ | `22_health_public.txt` |
| **Login (Auth)** | Token | Token Received | ✅ | `50_smoke_test_public.txt` |
| **Frontend Root** | 200 OK | 200 OK (Via Caddy/8012*) | ✅ | `40_frontend_root_headers.txt` |
| **Proxy Align** | 8013 | **FIXED** (Was 8012) | ✅ | `docker-compose.yml` updated |
| **Smoke (Public)** | Full Pass | **Failed** (KeyError: 'id') | ❌ | `50_smoke_test_public.txt` |
| **Smoke (Internal)** | Full Pass | **Failed** (KeyError: 'parameter_id') | ❌ | `51_smoke_test_internal.txt` |
| **API Probe** | `id` key | `test_id` key found | ❌ | `60_api_probes.txt` |

*Note: Frontend root headers verification (Step 40) was run against 8012 before the port fix. Functionality confirmed on 8013 manually.*

## 4. Service Health Snapshot
All services are currently **running and healthy**:
- `lims_proxy`: 8013->80 (Corrected)
- `lims_backend`: 8000 (Internal)
- `lims_frontend`: 80 (Internal)
- `lims_db` & `lims_redis`: Healthy

## 5. Drift & Known Issues

### 1. Configuration Mismatch (FIXED)
- **Issue:** `docker-compose.yml` exposed port 8012, but external host Caddy (`/srv/proxy/caddy/Caddyfile`) proxies to 8013.
- **Fix:** Updated `docker-compose.yml` to expose `8013:80`.
- **Status:** Resolved.

### 2. Frontend Build Failure (Critical)
- **Issue:** `src/pages/registration/RegistrationPage.tsx` contains unused state `showOrderForm`, causing `npm run build` to fail with `exit code 2`.
- **Workaround:** Applied temporary comment-out patch to `_smoke_artifacts/fixed_src/`.
- **Impact:** Cannot deploy without code fix.

### 3. Smoke Test / API Drift (High)
- **Issue:** `smoke_test.py` expects tests to have `id` key. Public API returns `test_id`.
- **Issue:** `smoke_test_internal.py` expects `parameter_id`. API presumably returns `id` or different key.
- **Evidence:** `60_api_probes.txt` confirms `test_id` presence and lack of `id`.
- **Impact:** Automated verification fails, though features verify manually (Login, Patient, Order Creation working).

### 4. Pytest Missing (Medium)
- **Issue:** Production docker image `lims-backend` does not include `pytest`.
- **Impact:** Cannot run unit tests in production environment.

## 6. Next Actions
1.  **[P0] Fix Frontend Code:** Remove unused `showOrderForm` from `RegistrationPage.tsx` permanently.
2.  **[P1] Update Smoke Tests:** Create updated `smoke_test_v2.py` that handles `test_id` mapping and current API structure.
3.  **[P2] Dev vs Prod Image:** Create a dev-specific Compose override or image that includes `pytest` for verification.
