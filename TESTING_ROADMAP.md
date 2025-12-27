# Testing Roadmap - Quick Reference

## Current Status

✅ **All Phase 1 & 2 Features Implemented**
- Reference Range Management
- Multi-Terminal Support  
- System Configuration
- Patient History & Comparison
- Enhanced Reporting
- Advanced Search & Filters
- Dashboard Analytics
- Email Notifications
- Analyzer Integration

⏳ **Remaining Work**
- Test coverage for new features
- Integration tests
- Frontend API integration testing

---

## Test Files to Create

### New Test Files Needed

1. **`apps/laboratory/tests/test_reference_ranges.py`**
   - Test ReferenceRange model
   - Test ReferenceRangeSerializer
   - Test ReferenceRangeViewSet
   - Test age/gender filtering
   - Test versioning

2. **`apps/core/tests/test_terminals.py`**
   - Test LabTerminal model
   - Test LabTerminalSerializer
   - Test LabTerminalViewSet
   - Test MRN allocation
   - Test range validation

3. **`apps/core/tests/test_settings.py`**
   - Test SystemSettings model
   - Test SystemSettingsSerializer
   - Test SystemSettingsViewSet
   - Test singleton pattern

4. **`apps/core/tests/test_export_utils.py`**
   - Test export_to_csv
   - Test export_to_excel
   - Test various data formats

5. **`apps/patients/tests/test_patient_history.py`**
   - Test history endpoint
   - Test test_comparison endpoint
   - Test delta checks
   - Test trend data

6. **`apps/reports/tests/test_enhanced_reporting.py`**
   - Test report amendments
   - Test reprints
   - Test delivery tracking
   - Test report history

7. **`apps/dashboard/tests/test_analytics.py`**
   - Test revenue_report
   - Test test_statistics
   - Test turnaround_time
   - Test workload_distribution
   - Test payment_methods
   - Test export_analytics

8. **`apps/notifications/tests/test_models.py`**
   - Test Notification model

9. **`apps/notifications/tests/test_views.py`**
   - Test NotificationViewSet

10. **`apps/notifications/tests/test_utils.py`**
    - Test all notification sending functions
    - Test email sending
    - Test error handling

11. **`apps/integrations/tests/test_models.py`**
    - Test Analyzer model
    - Test AnalyzerResultImport model

12. **`apps/integrations/tests/test_views.py`**
    - Test AnalyzerViewSet
    - Test AnalyzerResultImportViewSet
    - Test import_hl7 action
    - Test match_order action

13. **`apps/integrations/tests/test_hl7_parser.py`**
    - Test HL7Parser class
    - Test message parsing
    - Test segment extraction
    - Test error handling

---

## Test Execution Order

### Week 1: Core Infrastructure
1. Reference Range tests (A1)
2. Multi-Terminal tests (A2)
3. System Settings tests (A3)

### Week 2: Feature Tests
4. Patient History tests (A4)
5. Enhanced Reporting tests (A5)
6. Advanced Search tests (A6)

### Week 3: Advanced Features
7. Dashboard Analytics tests (A7)
8. Email Notifications tests (A8)
9. Analyzer Integration tests (A9)

### Week 4: Integration & Polish
10. Integration tests (B1-B2)
11. Test suite enhancement (C1-C3)
12. Frontend integration (D1-D3)

---

## Quick Commands

### Run Tests
```bash
# All tests
pytest apps/ -v

# Specific app
pytest apps/laboratory/ -v

# Specific test file
pytest apps/laboratory/tests/test_reference_ranges.py -v

# With coverage
coverage run -m pytest apps/ -v
coverage report
coverage html
```

### Check Coverage
```bash
# Generate coverage report
coverage run -m pytest apps/ -v
coverage report --show-missing

# HTML report
coverage html
# Open htmlcov/index.html in browser
```

### Run CI Locally
```bash
# Linting
flake8 apps/ --max-line-length=120 --exclude=migrations

# Tests with coverage (100% threshold)
coverage run -m pytest apps/ -v
coverage report --fail-under=100
```

---

## Success Metrics

- ✅ 100% code coverage for all new code
- ✅ All tests passing
- ✅ No linting errors
- ✅ CI pipeline green
- ✅ All API endpoints tested
- ✅ Integration tests passing

---

*See COMPLETION_PLAN.md for detailed implementation guide*

