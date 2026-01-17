# API Contract Audit - Actual Response Examples

**Date:** Saturday, January 17, 2026
**Environment:** Production Docker Stack
**Base URL:** http://localhost:8013/api/v1/

## Summary of Critical Findings

### Issue #1: Patients List Endpoint (BROKEN)
- **Current:** `{count, next, previous, results: {success: true, data: [...]}}`
- **Expected:** `{count, next, previous, results: [...]}`
- **Impact:** Frontend error "map is not a function"
- **Root cause:** Line 150 in `apps/patients/views.py` wraps array in object

### Issue #2: Settings loads correctly (no issue)
- Returns plain object as expected for singleton

### Issue #3: Payment does NOT create samples
- Missing workflow bridge: payment → sample generation
- Samples table empty after payment recorded

---

## Detailed Endpoint Analysis

### 1. GET /api/v1/patients/

**Actual Response Structure:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": {
    "success": true,
    "data": [...]
  }
}
```

**Problem:** `results` should be array, not object with nested array.

**Fix:** Change line 150 in `apps/patients/views.py` from:
```python
return self.get_paginated_response({"success": True, "data": serializer.data})
```
To:
```python
return self.get_paginated_response(serializer.data)
```

---

### 2. GET /api/v1/core/settings/

**Actual Response:** Plain object ✓ Correct

---

### 3. GET /api/v1/samples/pending_collections/

**Actual Response:** Standard DRF pagination ✓ Correct

---

### 4. GET /api/v1/results/worklist/

**Actual Response:** Standard DRF pagination ✓ Correct

---

### 5. GET /api/v1/laboratory/tests/

**Actual Response:** Standard DRF pagination ✓ Correct

---

## Recommended Fixes

### Priority 1: Fix Patients List (Immediate)
File: `lims-backend/apps/patients/views.py`
Line: 150-151

### Priority 2: Implement Payment → Sample Generation
File: `lims-backend/apps/billing/views.py`
Add post-save logic to create samples

### Priority 3: Frontend Normalization Layer
File: `frontend/src/utils/apiHelpers.ts`
Add response normalization functions
