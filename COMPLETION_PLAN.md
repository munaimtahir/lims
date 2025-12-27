# Phase 1 & 2 Completion Plan - 100% Coverage & Testing

## Overview

This document outlines the comprehensive plan to complete all remaining tasks for Phase 1 and Phase 2 features, ensuring 100% code coverage and a fully functional test suite.

**Status**: All Phase 1 & 2 development features are complete. Remaining work focuses on testing and coverage.

---

## Remaining Tasks

### 1. ✅ Coverage 100% (Pending)
**Goal**: Achieve 100% code coverage for all new and existing code

**Current State**: 
- CI threshold set to 100% (updated in `.github/workflows/backend-ci.yml`)
- Coverage configuration exists (`.coveragerc`)
- Existing tests cover core functionality

**New Code Requiring Tests**:
- Reference Range Management (models, views, serializers)
- Multi-Terminal Support (models, views, serializers)
- System Settings (models, views, serializers)
- Patient History & Comparison (views, endpoints)
- Enhanced Reporting (models, views, serializers)
- Advanced Search & Filters (filters, export utils)
- Dashboard Analytics (views, endpoints)
- Email Notifications (models, views, utils)
- Analyzer Integration (models, views, HL7 parser)

### 2. ✅ Test Suite Complete (Pending)
**Goal**: Enhance test suite, fix all failing tests, add integration and E2E tests

**Current State**:
- Test files exist for all core apps
- Basic test structure in place
- Need comprehensive coverage for new features

### 3. ⚠️ Frontend Integration (Pending)
**Goal**: Test and fix frontend-backend API integration issues

**Current State**:
- Backend APIs implemented
- Frontend exists but needs integration testing
- API endpoints need validation

---

## Detailed Implementation Plan

### Phase A: Test Coverage for New Features (Priority: High)

#### A1. Reference Range Management Tests
**Files to Test**:
- `apps/laboratory/models.py` (ReferenceRange model)
- `apps/laboratory/serializers.py` (ReferenceRangeSerializer)
- `apps/laboratory/views.py` (ReferenceRangeViewSet)
- `apps/laboratory/urls.py` (URL routing)

**Test Cases**:
1. **Model Tests**:
   - ReferenceRange creation with age/gender ranges
   - Versioning logic (auto-increment version)
   - Age range validation (min < max)
   - Reference value validation (min < max)
   - String representation
   - Unique constraint validation

2. **Serializer Tests**:
   - Valid data serialization
   - Invalid data validation (age ranges, reference values)
   - Read-only fields enforcement
   - Nested field serialization (parameter_name, test_name)

3. **ViewSet Tests**:
   - CRUD operations (Create, Read, Update, Delete)
   - Filtering by parameter, gender, age
   - `for_parameter` action with age/gender filtering
   - `deactivate` action
   - Permission checks

4. **Integration Tests**:
   - Create reference range → Query by parameter
   - Age-specific range selection
   - Version history tracking

**Estimated Tests**: 25-30 tests

---

#### A2. Multi-Terminal Support Tests
**Files to Test**:
- `apps/core/models.py` (LabTerminal model)
- `apps/core/serializers.py` (LabTerminalSerializer)
- `apps/core/views.py` (LabTerminalViewSet)

**Test Cases**:
1. **Model Tests**:
   - Terminal creation with offline ranges
   - Range validation (start < end)
   - `get_next_offline_mrn()` atomic allocation
   - Range exhaustion handling
   - String representation

2. **Serializer Tests**:
   - Valid terminal creation
   - Range validation
   - Read-only fields

3. **ViewSet Tests**:
   - CRUD operations
   - `get_next_mrn` action (success and failure cases)
   - `reset_range` action (admin only)
   - `active` action (list active terminals)
   - Permission checks

**Estimated Tests**: 20-25 tests

---

#### A3. System Settings Tests
**Files to Test**:
- `apps/core/models.py` (SystemSettings model)
- `apps/core/serializers.py` (SystemSettingsSerializer)
- `apps/core/views.py` (SystemSettingsViewSet)

**Test Cases**:
1. **Model Tests**:
   - Singleton pattern enforcement
   - Settings update (updates existing instead of creating new)
   - Email configuration fields
   - Report customization fields
   - Financial settings validation

2. **Serializer Tests**:
   - Valid settings update
   - Email port validation (1-65535)
   - Tax rate validation (non-negative)
   - Read-only fields

3. **ViewSet Tests**:
   - GET settings (returns singleton)
   - PUT/PATCH settings update
   - `current` action (alias for list)
   - Permission checks

**Estimated Tests**: 15-20 tests

---

#### A4. Patient History & Comparison Tests
**Files to Test**:
- `apps/patients/views.py` (PatientViewSet - history, test_comparison actions)

**Test Cases**:
1. **History Endpoint Tests**:
   - Get patient history with orders
   - Test history grouping by parameter
   - Comparison data (last N results)
   - Delta check detection (>20% change)
   - Critical value change detection
   - Trend data generation
   - Filtering by parameter_id
   - Limit parameter

2. **Test Comparison Endpoint Tests**:
   - Get comparison for specific parameter
   - Reference range inclusion
   - Multiple result comparison
   - Missing parameter handling
   - Invalid parameter_id handling

**Estimated Tests**: 20-25 tests

---

#### A5. Enhanced Reporting Tests
**Files to Test**:
- `apps/reports/models.py` (Report model enhancements)
- `apps/reports/serializers.py` (ReportSerializer updates)
- `apps/reports/views.py` (ReportViewSet - new actions)

**Test Cases**:
1. **Model Tests**:
   - Report number generation
   - Status transitions
   - Amendment creation (`create_amendment`)
   - Delivery tracking (`mark_delivered`)
   - Reprint tracking (`increment_reprint`)
   - `is_final` sync with status

2. **Serializer Tests**:
   - New field serialization (report_number, status, etc.)
   - Nested field serialization (amended_from_number, patient_name)

3. **ViewSet Tests**:
   - `mark_delivered` action
   - `reprint` action
   - `amend` action (with permission checks)
   - `patient_history` action
   - `amendments` action
   - Report generation with new fields

**Estimated Tests**: 25-30 tests

---

#### A6. Advanced Search & Filters Tests
**Files to Test**:
- `apps/patients/filters.py` (PatientFilter)
- `apps/orders/filters.py` (OrderFilter)
- `apps/results/filters.py` (TestResultFilter)
- `apps/core/export_utils.py` (export_to_csv, export_to_excel)
- `apps/patients/views.py` (export action)
- `apps/orders/views.py` (export action)
- `apps/results/views.py` (export action)

**Test Cases**:
1. **Filter Tests**:
   - PatientFilter: name search, age range, date range, gender
   - OrderFilter: date range, status, priority, amount range
   - TestResultFilter: value range, date range, flag, status

2. **Export Utils Tests**:
   - CSV export (list of dicts, list of lists)
   - Excel export (with headers, without headers)
   - Column width auto-adjustment
   - Empty data handling

3. **Export Action Tests**:
   - Patient export (CSV/Excel)
   - Order export (CSV/Excel)
   - Result export (CSV/Excel)
   - Format parameter validation

**Estimated Tests**: 30-35 tests

---

#### A7. Dashboard Analytics Tests
**Files to Test**:
- `apps/dashboard/views.py` (DashboardStatisticsViewSet - new actions)

**Test Cases**:
1. **Revenue Report Tests**:
   - Date range filtering
   - Grouping by day/week/month
   - Summary calculations
   - Invalid date format handling

2. **Test Statistics Tests**:
   - Most ordered tests
   - Most ordered panels
   - Date range filtering
   - Limit parameter

3. **Turnaround Time Tests**:
   - TAT calculation (creation to verification)
   - Average/min/max TAT
   - Date range filtering
   - Orders without results handling

4. **Workload Distribution Tests**:
   - By role (receptionists, phlebotomists, technicians, pathologists)
   - Date range filtering
   - Count aggregation

5. **Payment Methods Tests**:
   - Payment method breakdown
   - Total amount calculation
   - Date range filtering

6. **Export Analytics Tests**:
   - Revenue export
   - Test statistics export
   - Format validation

**Estimated Tests**: 25-30 tests

---

#### A8. Email Notifications Tests
**Files to Test**:
- `apps/notifications/models.py` (Notification model)
- `apps/notifications/serializers.py` (NotificationSerializer)
- `apps/notifications/views.py` (NotificationViewSet)
- `apps/notifications/utils.py` (all notification functions)

**Test Cases**:
1. **Model Tests**:
   - Notification creation
   - Status transitions
   - Related object linking
   - String representation

2. **Serializer Tests**:
   - Field serialization
   - Read-only fields

3. **ViewSet Tests**:
   - List notifications
   - Filtering by type, status, recipient
   - Search functionality

4. **Utils Tests**:
   - `send_notification` (success and failure)
   - `send_order_complete_notification`
   - `send_critical_value_alert`
   - `send_payment_receipt_notification`
   - `send_report_ready_notification`
   - `send_system_alert`
   - Email sending with system settings
   - Error handling

**Estimated Tests**: 25-30 tests

---

#### A9. Analyzer Integration Tests
**Files to Test**:
- `apps/integrations/models.py` (Analyzer, AnalyzerResultImport)
- `apps/integrations/serializers.py` (both serializers)
- `apps/integrations/views.py` (both ViewSets)
- `apps/integrations/hl7_parser.py` (HL7Parser class)

**Test Cases**:
1. **Model Tests**:
   - Analyzer creation
   - Connection config storage
   - AnalyzerResultImport creation
   - Status transitions

2. **HL7 Parser Tests**:
   - Message parsing (MSH, PID, OBR, OBX segments)
   - Patient info extraction
   - Order info extraction
   - Result extraction
   - Invalid message handling
   - Missing segment handling

3. **ViewSet Tests**:
   - Analyzer CRUD
   - `import_hl7` action (success, failure, matching, manual review)
   - `match_order` action
   - Result creation from import
   - Error handling

**Estimated Tests**: 30-35 tests

---

### Phase B: Integration & Trigger Tests (Priority: High)

#### B1. Notification Trigger Tests
**Test Integration Points**:
- Order status change → Order complete notification
- Payment creation → Payment receipt notification
- Report generation → Report ready notification
- Critical result → Critical value alert

**Test Cases**:
1. Order status to PUBLISHED triggers notification
2. Payment creation triggers receipt email
3. Report generation triggers ready email
4. Critical result flagging triggers alert
5. Missing email handling (no notification sent)
6. Email sending failure handling

**Estimated Tests**: 10-15 tests

---

#### B2. Result Validation Integration Tests
**Test Integration Points**:
- Result save → Auto-flagging
- Critical flag → Notification trigger
- Reference range lookup

**Test Cases**:
1. Result save triggers validation
2. Flag assignment based on reference ranges
3. Critical flag triggers notification
4. Missing reference range handling
5. Invalid value handling

**Estimated Tests**: 10-15 tests

---

### Phase C: Test Suite Enhancement (Priority: Medium)

#### C1. Test Infrastructure
**Tasks**:
1. Create test fixtures for common data:
   - Users (all roles)
   - Patients
   - Tests and parameters
   - Orders
   - Reference ranges
   - Terminals
   - System settings

2. Create test utilities:
   - API client helpers
   - Data factories
   - Assertion helpers

3. Update test configuration:
   - Ensure pytest.ini is correct
   - Verify coverage settings
   - Check test database setup

---

#### C2. Integration Test Suite
**Test Scenarios**:
1. Complete order workflow:
   - Patient registration → Order creation → Sample collection → Result entry → Verification → Report generation

2. Multi-terminal workflow:
   - Terminal creation → Offline MRN allocation → Patient registration

3. Reference range workflow:
   - Range creation → Result entry → Auto-flagging

4. Report workflow:
   - Report generation → Amendment → Reprint → Delivery

**Estimated Tests**: 10-15 integration tests

---

#### C3. E2E Test Scenarios
**Test Scenarios**:
1. Patient registration to report delivery
2. Critical value detection and alerting
3. Report amendment workflow
4. Multi-user role workflows

**Note**: E2E tests may require frontend integration or API-level testing

**Estimated Tests**: 5-10 E2E tests

---

### Phase D: Frontend Integration Testing (Priority: Medium)

#### D1. API Endpoint Validation
**Tasks**:
1. Test all new API endpoints:
   - Reference ranges: `/api/v1/laboratory/reference-ranges/`
   - Terminals: `/api/v1/core/terminals/`
   - System settings: `/api/v1/core/settings/`
   - Patient history: `/api/v1/patients/{id}/history/`
   - Test comparison: `/api/v1/patients/{id}/test_comparison/`
   - Report actions: `/api/v1/reports/{id}/reprint/`, `/api/v1/reports/{id}/amend/`
   - Dashboard analytics: `/api/v1/dashboard/revenue_report/`, etc.
   - Notifications: `/api/v1/notifications/`
   - Analyzer imports: `/api/v1/integrations/imports/import_hl7/`

2. Validate request/response formats
3. Test error handling
4. Verify authentication/authorization

---

#### D2. API Documentation
**Tasks**:
1. Ensure all endpoints are documented in Swagger/OpenAPI
2. Verify request/response schemas
3. Add example requests/responses
4. Document error codes

---

#### D3. Frontend-Backend Compatibility
**Tasks**:
1. Test API responses match frontend expectations
2. Verify CORS configuration
3. Test pagination
4. Test filtering and search
5. Test export functionality

---

## Execution Strategy

### Step 1: Create Test Files Structure
```
lims-backend/apps/
├── laboratory/tests/
│   └── test_reference_ranges.py (NEW)
├── core/tests/
│   ├── test_terminals.py (NEW)
│   ├── test_settings.py (NEW)
│   └── test_export_utils.py (NEW)
├── patients/tests/
│   └── test_patient_history.py (NEW)
├── reports/tests/
│   └── test_enhanced_reporting.py (NEW)
├── dashboard/tests/
│   └── test_analytics.py (NEW)
├── notifications/tests/
│   ├── test_models.py (NEW)
│   ├── test_views.py (NEW)
│   └── test_utils.py (NEW)
└── integrations/tests/
    ├── test_models.py (NEW)
    ├── test_views.py (NEW)
    └── test_hl7_parser.py (NEW)
```

### Step 2: Write Tests in Priority Order
1. **Week 1**: Core models and serializers (ReferenceRange, LabTerminal, SystemSettings)
2. **Week 2**: ViewSets and API endpoints (all new endpoints)
3. **Week 3**: Integration tests and triggers
4. **Week 4**: Advanced features (filters, exports, analytics)

### Step 3: Run Coverage Analysis
```bash
# Run tests with coverage
coverage run -m pytest apps/ -v

# Generate coverage report
coverage report

# Generate HTML report for detailed analysis
coverage html

# Identify uncovered lines
coverage report --show-missing
```

### Step 4: Fix Coverage Gaps
- Add tests for uncovered lines
- Add edge case tests
- Add error handling tests

### Step 5: Run Full Test Suite
```bash
# Run all tests
pytest apps/ -v

# Run with coverage
coverage run -m pytest apps/ -v
coverage report --fail-under=100
```

### Step 6: Integration Testing
- Test complete workflows
- Test API integration
- Test notification triggers

### Step 7: Frontend Integration
- Test API endpoints from frontend
- Fix any compatibility issues
- Verify all features work end-to-end

---

## Success Criteria

### Coverage Goals
- ✅ **100% code coverage** for all new code
- ✅ **95%+ coverage** for existing code (if not already 100%)
- ✅ **Zero uncovered critical paths**

### Test Quality Goals
- ✅ **All tests passing** (100% pass rate)
- ✅ **No flaky tests**
- ✅ **Fast execution** (<5 minutes for full suite)
- ✅ **Clear test names** and documentation

### Integration Goals
- ✅ **All API endpoints tested**
- ✅ **All workflows tested end-to-end**
- ✅ **Frontend-backend integration verified**

---

## Estimated Timeline

| Phase | Tasks | Estimated Time | Priority |
|-------|-------|----------------|----------|
| A1-A3 | Core models tests | 2-3 days | High |
| A4-A6 | Feature tests | 3-4 days | High |
| A7-A9 | Advanced feature tests | 3-4 days | High |
| B1-B2 | Integration tests | 2-3 days | High |
| C1-C3 | Test suite enhancement | 2-3 days | Medium |
| D1-D3 | Frontend integration | 2-3 days | Medium |
| **Total** | **All tasks** | **14-20 days** | - |

---

## Risk Mitigation

### Risks
1. **Complex test scenarios**: Some features have complex workflows
   - **Mitigation**: Break down into smaller test cases, use fixtures

2. **Integration dependencies**: Tests may depend on external services
   - **Mitigation**: Mock external services, use test database

3. **Coverage gaps**: Some code paths may be hard to test
   - **Mitigation**: Use coverage tools to identify gaps, add targeted tests

4. **Test maintenance**: Tests may break with code changes
   - **Mitigation**: Write maintainable tests, use fixtures, keep tests simple

---

## Next Steps

1. **Immediate**: Start with Phase A1 (Reference Range tests) - highest priority
2. **This Week**: Complete Phase A1-A3 (core models)
3. **Next Week**: Complete Phase A4-A6 (feature tests)
4. **Following Week**: Complete Phase A7-A9, B1-B2 (advanced features and integration)
5. **Final Week**: Complete Phase C and D (test suite enhancement and frontend integration)

---

## Notes

- All new code should have tests written before merging
- Use TDD approach where possible (write tests first)
- Keep tests isolated and independent
- Use fixtures for common test data
- Mock external dependencies (email, file system, etc.)
- Run tests frequently during development
- Update this plan as progress is made

---

*Last Updated: 2024-12-28*
*Status: Ready for Execution*

