# Failing Tests Documentation

**Date:** 2025-01-27  
**Status:** Tests documented for later review

## Summary

This document lists all currently failing tests that need to be addressed. These tests were added as part of the coverage closure effort but have issues that need investigation and fixing.

---

## Failing Tests by Category

### 1. Filter Tests (Patient Filters)

**File:** `apps/patients/tests/test_filters.py`

#### `test_filter_by_created_from`
- **Status:** FAILING
- **Issue:** Date filtering logic may have timezone or date comparison issues
- **Details:** Test creates patients with specific `created_at` dates but filter may not be working as expected with date comparisons

#### `test_filter_by_created_to`
- **Status:** FAILING
- **Issue:** Similar to `test_filter_by_created_from`, date comparison logic needs review
- **Details:** Filter may not be correctly handling date boundaries

#### `test_filter_by_age_max`
- **Status:** FAILING (may be fixed)
- **Issue:** Age calculation logic in filter may need adjustment
- **Details:** The `filter_age_max` method uses `date.today().replace(year=date.today().year - value - 1)` which may have edge case issues

#### `test_filter_by_age_range`
- **Status:** FAILING (may be fixed)
- **Issue:** Combination of age_min and age_max filters may have logic issues
- **Details:** When both filters are applied, the intersection logic may not work correctly

---

### 2. Results Filter Tests

**File:** `apps/results/tests/test_filters.py`

#### `test_filter_by_value_min`
- **Status:** FAILING
- **Issue:** The `filter_value_min` method iterates over queryset in Python, which may cause issues with test assertions
- **Details:** Filter implementation uses Python iteration rather than database filtering

#### `test_filter_by_value_max`
- **Status:** FAILING
- **Issue:** Similar to `test_filter_by_value_min`
- **Details:** Filter implementation needs review

#### `test_filter_by_value_range`
- **Status:** FAILING
- **Issue:** Combination of value_min and value_max filters
- **Details:** Both filters iterate in Python, which may cause unexpected behavior

#### `test_filter_handles_non_numeric_values`
- **Status:** FAILING
- **Issue:** Filter may not handle non-numeric values gracefully
- **Details:** Need to ensure filter handles ValueError exceptions properly

---

### 3. Worklist Tests

**File:** `apps/results/tests/test_results.py`

#### `test_worklist`
- **Status:** FAILING
- **Issue:** Worklist action logic or test setup may be incorrect
- **Details:** Test may need adjustment based on actual worklist implementation

#### `test_worklist_endpoint`
- **Status:** FAILING
- **Issue:** Similar to `test_worklist`
- **Details:** Endpoint may have different behavior than expected

---

### 4. Integration Tests

**File:** `apps/integrations/tests/test_integrations.py`

#### `test_import_hl7_create_results_on_match`
- **Status:** FAILING
- **Issue:** HL7 import result creation logic may have issues
- **Details:** Test expects results to be created when order is matched, but may not be working

#### `test_import_hl7_result_creation_exception`
- **Status:** FAILING
- **Issue:** Exception handling in result creation may not be working as expected
- **Details:** Mock may not be set up correctly or exception handling needs review

#### `test_match_order_result_creation_exception`
- **Status:** FAILING
- **Issue:** Similar to `test_import_hl7_result_creation_exception`
- **Details:** Exception handling in match_order action needs review

---

### 5. Serializer Tests (Fixed but may still fail)

**File:** `apps/orders/tests/test_serializers.py`

#### All OrderSerializer tests
- **Status:** FIXED (data format corrected)
- **Issue:** Tests were using IDs instead of objects in `validated_data`
- **Fix Applied:** Changed to use objects (patient, order_item, etc.) instead of IDs
- **Note:** May still need verification

**File:** `apps/results/tests/test_serializers.py`

#### All TestResultSerializer tests
- **Status:** FIXED (data format corrected)
- **Issue:** Tests were using IDs instead of objects in `validated_data`
- **Fix Applied:** Changed to use objects instead of IDs
- **Note:** May still need verification

---

## Test Count Summary

- **Total Failing Tests:** ~29 (varies based on recent fixes)
- **Filter Tests:** ~7-10
- **Worklist Tests:** ~2
- **Integration Tests:** ~3
- **Serializer Tests:** ~9 (may be fixed)

---

## Recommended Fix Order

1. **Filter Tests** - Review filter implementation logic, especially date and age filtering
2. **Worklist Tests** - Review worklist action implementation and test expectations
3. **Integration Tests** - Review exception handling and mocking setup
4. **Serializer Tests** - Verify fixes are working correctly

---

## Notes

- All failing tests are documented here for later review
- Tests were added to increase coverage but need debugging
- Some tests may fail due to implementation details that need adjustment
- Focus should be on fixing the root cause rather than adjusting tests to match incorrect behavior

---

## Next Steps

1. Review each failing test individually
2. Understand the expected vs actual behavior
3. Fix either the test or the implementation (whichever is incorrect)
4. Re-run tests to verify fixes
5. Update this document as tests are fixed
