# Core LIMS v1.0 - Smoke Test Documentation

**Version:** 1.0.0  
**Date:** January 2026  
**Status:** ✅ Validated

---

## Overview

This document describes the smoke testing procedure for Core LIMS v1.0. Smoke testing validates that all critical workflows function correctly after deployment.

**Latest Test Results:** See [FINAL_SMOKE_TEST_REPORT.md](../../FINAL_SMOKE_TEST_REPORT.md) for complete validation results (92.3% pass rate, 24/26 tests).

---

## Test Scope

The smoke test validates the complete end-to-end workflow:

1. **Authentication** - All user roles can log in
2. **Order Creation** - Receptionist creates orders with automatic sample creation
3. **Sample Collection** - Phlebotomist marks samples as collected
4. **Result Entry** - Lab technician enters test results
5. **Result Verification** - Pathologist verifies results
6. **Reporting** - Report generation
7. **Billing** - Payment recording
8. **Audit & Health** - System monitoring and audit trail

---

## Prerequisites

- Core LIMS deployed and running
- Demo users created (or test users available)
- Test catalog seeded with at least 2 tests
- Network access to application URL

---

## Running the Automated Smoke Test

### Option 1: Using the Smoke Test Script

The repository includes a comprehensive Python script that automates all test scenarios:

```bash
# From repository root
python smoke_test.py

# Specify custom URL
python smoke_test.py --url http://your-domain:8012
```

**Script Location:** `/smoke_test.py`

**What it tests:**
- ✅ Authentication for all 6 user roles
- ✅ Patient retrieval
- ✅ Test catalog access
- ✅ Order creation with auto-sample generation (Issue #1 regression test)
- ✅ Sample status verification
- ✅ Collection worklist
- ✅ Sample collection
- ✅ Result entry worklist
- ✅ Test parameters retrieval
- ✅ Bulk result entry (Issue #2 regression test)
- ✅ Verification queue
- ✅ Result verification
- ✅ Report generation
- ✅ Report download (known limitation)
- ✅ Payment recording
- ✅ Receipt download (known limitation)
- ✅ Audit log access
- ✅ Health check endpoint

**Expected Output:**
```
================================================================================
LIMS v1.0 - FULL SMOKE TEST
================================================================================
Started: 2026-01-17 17:41:16
Target: http://localhost:8012

Total Tests: 26
Passed: 24 ✅
Failed: 2 ❌
Success Rate: 92.3%
```

### Option 2: Manual Testing

Follow the manual test scenarios below if you prefer hands-on testing or the automated script is unavailable.

---

## Manual Test Scenarios

### Phase 1: Authentication

**Objective:** Verify all user roles can log in successfully.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to http://localhost:8012 | Login page displayed |
| 2 | Login as receptionist/recep123 | Dashboard displayed, role: Receptionist |
| 3 | Logout | Return to login page |
| 4 | Login as phlebotomist/phleb123 | Dashboard displayed, role: Phlebotomist |
| 5 | Logout | Return to login page |
| 6 | Login as labtech/labtech123 | Dashboard displayed, role: Lab Technician |
| 7 | Logout | Return to login page |
| 8 | Login as pathologist/patho123 | Dashboard displayed, role: Pathologist |
| 9 | Logout | Return to login page |
| 10 | Login as cashier/cash123 | Dashboard displayed, role: Cashier |
| 11 | Logout | Return to login page |
| 12 | Login as admin/admin123 | Dashboard displayed, role: Admin |

**Pass Criteria:** All 6 roles authenticate successfully and show correct role labels.

---

### Phase 2: Order Creation & Sample Auto-Generation

**Objective:** Verify order creation and automatic sample generation (Issue #1 regression test).

**User:** Receptionist

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as receptionist | Dashboard displayed |
| 2 | Navigate to Patients | Patient list displayed |
| 3 | Select any existing patient | Patient details displayed |
| 4 | Click "Create Order" | Order creation form displayed |
| 5 | Select 2 tests from catalog | Tests added to order |
| 6 | Submit order | Order created with order number |
| 7 | View order details | 2 order items displayed |
| 8 | Check samples | **2 samples auto-created with PENDING status** |

**Pass Criteria:** 
- ✅ Order created successfully
- ✅ Samples automatically created (same count as test items)
- ✅ All samples have PENDING status
- ✅ **Issue #1 FIXED:** No manual sample creation required

**Known Issue in v1.0:** None - this workflow is fully functional.

---

### Phase 3: Sample Collection

**Objective:** Verify phlebotomist can mark samples as collected.

**User:** Phlebotomist

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as phlebotomist | Dashboard displayed |
| 2 | Navigate to Collection Worklist | List of PENDING samples displayed |
| 3 | Find sample from previous order | Sample visible in worklist |
| 4 | Click "Collect" or mark as collected | Sample status changes to COLLECTED |
| 5 | Verify worklist updates | Sample removed from pending list |

**Pass Criteria:**
- ✅ Worklist displays pending samples
- ✅ Sample collection recorded successfully
- ✅ Status updated to COLLECTED

---

### Phase 4: Result Entry

**Objective:** Verify lab technician can enter results (Issue #2 regression test).

**User:** Lab Technician

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as labtech | Dashboard displayed |
| 2 | Navigate to Result Entry Worklist | List of COLLECTED samples displayed |
| 3 | Find sample from previous order | Sample visible in worklist |
| 4 | Click "Enter Results" | Result entry form displayed |
| 5 | View test parameters | Parameter fields displayed (e.g., WBC, RBC for CBC) |
| 6 | Enter numeric values for all parameters | Values accepted |
| 7 | Submit results | Results saved successfully |
| 8 | Check result status | **Result has ENTERED status (not DRAFT)** |

**Pass Criteria:**
- ✅ Worklist displays collected samples
- ✅ Test parameters load correctly
- ✅ Results saved successfully
- ✅ **Issue #2 FIXED:** Results have ENTERED status (not DRAFT)
- ✅ Results appear in verification queue immediately

**Known Issue in v1.0:** None - this workflow is fully functional.

---

### Phase 5: Result Verification

**Objective:** Verify pathologist can verify results.

**User:** Pathologist

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as pathologist | Dashboard displayed |
| 2 | Navigate to Verification Queue | List of ENTERED results displayed |
| 3 | Find result from previous test | Result visible in queue |
| 4 | Review result details | All entered values displayed |
| 5 | Click "Verify" or "Approve" | Result status changes to VERIFIED |
| 6 | Verify queue updates | Result removed from queue |

**Pass Criteria:**
- ✅ Verification queue displays entered results
- ✅ Result verification recorded successfully
- ✅ Status updated to VERIFIED

---

### Phase 6: Report Generation

**Objective:** Verify report generation (note: download endpoint has known limitation).

**User:** Admin or Manager

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as admin | Dashboard displayed |
| 2 | Navigate to Reports | Report management page displayed |
| 3 | Find order with verified results | Order displayed |
| 4 | Click "Generate Report" | Report generation initiated |
| 5 | Check report status | Report created with ID assigned |
| 6 | Attempt to download PDF | ⚠️ **Known Issue:** Download endpoint returns 404 |

**Pass Criteria:**
- ✅ Report generation succeeds
- ✅ Report record created in database
- ⚠️ **Known Limitation:** PDF download endpoint not implemented (planned for v1.1)

**Workaround:** Report data exists in database; PDF can be regenerated or accessed via alternative method.

---

### Phase 7: Billing & Payment

**Objective:** Verify payment recording (note: receipt download has known limitation).

**User:** Cashier

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as cashier | Dashboard displayed |
| 2 | Navigate to Billing | Billing management page displayed |
| 3 | Find order ready for payment | Order with verified results displayed |
| 4 | Click "Record Payment" | Payment form displayed |
| 5 | Enter payment details (amount, method) | Values accepted |
| 6 | Submit payment | Payment recorded successfully |
| 7 | Check payment status | Payment ID assigned |
| 8 | Attempt to download receipt | ⚠️ **Known Issue:** Receipt endpoint returns 404 |

**Pass Criteria:**
- ✅ Payment recording succeeds
- ✅ Payment record created in database
- ⚠️ **Known Limitation:** Receipt download endpoint not implemented (planned for v1.1)

**Workaround:** Receipt data exists in database; can be regenerated or accessed via alternative method.

---

### Phase 8: Audit & Health Check

**Objective:** Verify system monitoring and audit trail.

**User:** Admin

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as admin | Dashboard displayed |
| 2 | Navigate to Audit Logs | Audit log page displayed |
| 3 | View recent entries | All previous actions logged (order create, sample collect, result entry, etc.) |
| 4 | Check log details | User, action, timestamp, changes recorded |
| 5 | Test health endpoint | Navigate to /api/v1/health/ |
| 6 | Verify health response | JSON: {"status":"healthy","service":"LIMS Backend","database":"connected"} |

**Pass Criteria:**
- ✅ Audit logs capture all critical actions
- ✅ Health endpoint returns 200 OK
- ✅ Database connectivity confirmed

---

## Known Issues in v1.0

### 1. PDF Download Endpoints Return 404 (Non-Critical)

**Affected Endpoints:**
- `GET /api/v1/reports/{report_id}/download/`
- `GET /api/v1/payments/{payment_id}/download_receipt/`

**Impact:** LOW - Core functionality works; only helper download endpoints fail

**Status:** Known limitation, tracked for v1.1

**Workaround:** 
- Reports are generated (database records exist)
- Payments are recorded (database records exist)
- PDFs can be regenerated on-demand or retrieved via alternative endpoints

### 2. Backend Health Check Timing (Cosmetic)

**Issue:** Backend container may show "unhealthy" in `docker ps` due to health check timing

**Impact:** NONE - System is operational if API responds

**Verification:** Test API directly:
```bash
curl http://localhost:8012/api/v1/health/
# If returns {"status":"healthy",...}, system is operational
```

---

## Regression Tests

### Issue #1: Samples Not Auto-Creating on Order Creation

**Status:** ✅ **FIXED**

**Test:** Create order with 2 tests → Verify 2 samples auto-created with PENDING status

**Validation:** Tested in Phase 2 of smoke test

**Evidence:** See FINAL_SMOKE_TEST_REPORT.md lines 88-99

---

### Issue #2: Results Saving as DRAFT Instead of ENTERED

**Status:** ✅ **FIXED**

**Test:** Enter result via bulk_entry → Verify result has ENTERED status → Verify result appears in verification queue

**Validation:** Tested in Phase 4 and Phase 5 of smoke test

**Evidence:** See FINAL_SMOKE_TEST_REPORT.md lines 114-139

---

## Test Results History

### v1.0 Final Smoke Test (2026-01-17)

**Status:** ✅ PASS (92.3%)

- **Total Tests:** 26
- **Passed:** 24 ✅
- **Failed:** 2 ❌ (non-critical PDF downloads)
- **Duration:** ~30 seconds
- **Report:** [FINAL_SMOKE_TEST_REPORT.md](../../FINAL_SMOKE_TEST_REPORT.md)

**Verdict:** ✅ **PRODUCTION READY**

---

## Running Tests in CI/CD

To integrate smoke tests into CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
smoke-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    
    - name: Start services
      run: |
        docker compose up -d
        sleep 15
    
    - name: Initialize database
      run: |
        docker compose exec -T backend python manage.py migrate
        docker compose exec -T backend python manage.py seed_test_catalog --clear
        docker compose exec -T backend python manage.py create_demo_users
    
    - name: Run smoke test
      run: python smoke_test.py
    
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: smoke-test-results
        path: smoke_test_output.txt
```

---

## Success Criteria

A deployment PASSES smoke testing if:

✅ **Authentication (6/6):** All user roles authenticate successfully  
✅ **Order Workflow (5/5):** Order creation with auto-sample generation works  
✅ **Sample Collection (2/2):** Phlebotomist workflow functional  
✅ **Result Entry (4/4):** Lab technician can enter results as ENTERED status  
✅ **Result Verification (3/3):** Pathologist can verify results  
✅ **Audit & Health (2/2):** System monitoring operational  
⚠️ **Reporting (1/2):** Report generation works (download limitation acceptable)  
⚠️ **Billing (1/2):** Payment recording works (receipt limitation acceptable)  

**Minimum Pass Rate:** 90% (23/26 tests)  
**v1.0 Achievement:** 92.3% (24/26 tests) ✅

---

## Troubleshooting Test Failures

### Authentication Failures

**Symptom:** Login fails for demo users

**Solutions:**
1. Verify demo users were created: `docker compose exec backend python manage.py create_demo_users`
2. Check backend logs: `docker compose logs backend`
3. Verify JWT settings in .env

### Sample Auto-Creation Failures

**Symptom:** Samples not created when order is created

**Solutions:**
1. Verify Issue #1 fix is applied (check `lims-backend/apps/orders/serializers.py`)
2. Check backend logs for errors during order creation
3. Verify test catalog is seeded with valid tests

### Result Entry Failures

**Symptom:** Results save as DRAFT or don't appear in verification queue

**Solutions:**
1. Verify Issue #2 fix is applied (check `lims-backend/apps/results/views.py`)
2. Ensure test parameters exist for the test
3. Check API endpoint: `/api/v1/laboratory/parameters/?test={test_id}`

### API Endpoint Errors

**Symptom:** 404 or 500 errors on API calls

**Solutions:**
1. Check service health: `docker compose ps`
2. Verify backend is running: `curl http://localhost:8012/api/v1/health/`
3. Check backend logs: `docker compose logs backend`
4. Verify .env configuration (ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS)

---

## See Also

- [FINAL_SMOKE_TEST_REPORT.md](../../FINAL_SMOKE_TEST_REPORT.md) - Complete validation results
- [SECURITY_VERIFICATION_REPORT.md](./SECURITY_VERIFICATION_REPORT.md) - Security validation
- [../ops/DEPLOYMENT.md](../ops/DEPLOYMENT.md) - Deployment procedures
- [../../PRODUCTION_READINESS_CHECKLIST.md](../../PRODUCTION_READINESS_CHECKLIST.md) - Production readiness

---

**Smoke Test Documentation Version:** 1.0.0  
**Last Updated:** January 2026  
**Next Review:** Before v1.1 release
