# API Contract Audit - Actual Response Examples

**Date:** Saturday, January 17, 2026
**Environment:** Production Docker Stack
**Base URL:** http://localhost:8012/api/v1/

## Summary of Findings

### Key Issues Identified:
1. **Patients List Endpoint** - Uses BROKEN custom wrapper: `{count, next, previous, results: {success: true, data: [...]}}` instead of standard DRF `{count, next, previous, results: [...]}`
2. **Settings Endpoint** - Returns plain object (correct for singleton)
3. **Samples pending_collections** - Returns standard DRF pagination (correct)
4. **Results worklist** - Returns standard DRF pagination (correct)
5. **Inconsistent Response Patterns** - Mix of wrapped and unwrapped responses

---

## 1. GET /api/v1/patients/ (List Patients)

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8012/api/v1/patients/?page_size=2"
```

**Actual Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": {
    "success": true,
    "data": [
      {
        "id": 2,
        "patient_id": "PAT-20260117-0002",
        "first_name": "Jane",
        "last_name": "Smith",
        "full_name": "Jane Smith",
        ...
      },
      {
        "id": 1,
        "patient_id": "PAT-20260117-0001",
        ...
      }
    ]
  }
}
```

**Analysis:**
- Response structure uses **BROKEN CUSTOM WRAPPER** inside `results` field
- Shape: `{count, next, previous, results: {success: true, data: [...]}}`
- **CRITICAL PROBLEM:** The `results` field should be an ARRAY, not an OBJECT
- DRF pagination expects: `{count, next, previous, results: [...]}`
- Current backend returns: `{count, next, previous, results: {success, data: [...]}}`
- **ROOT CAUSE:** `apps/patients/views.py` line 150-151:
  ```python
  return self.get_paginated_response(
      {"success": True, "data": serializer.data}
  )
  ```
- **FIX:** Remove wrapper, just pass `serializer.data` to `get_paginated_response()`

**Frontend Impact:**
- Frontend code tries: `patientsData.results.map(...)` 
- Gets: `patientsData.results` is an object `{success: true, data: [...]}`
- Error: `patientsData.results.map is not a function`

---

## 2. GET /api/v1/core/settings/ (System Settings)

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8012/api/v1/core/settings/
```

**Actual Response:**
```json
{
  "id": 1,
  "lab_name": "Al Shifa Laboratory",
  "lab_address": "123 Health Street, Medical District",
  "lab_phone": "+92-300-1234567",
  "lab_email": "info@alshifalab.pk",
  "currency": "PKR",
  "timezone": "Asia/Karachi",
  ...
}
```

**Analysis:**
- Response is **PLAIN OBJECT** (no wrapper)
- **CORRECT** for singleton resource
- Frontend must NOT expect `{success, data}` wrapper
- This is proper RESTful design for singleton resources

---

## 3. GET /api/v1/samples/pending_collections/ (Sample Collection Worklist)

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8012/api/v1/samples/pending_collections/
```

**Actual Response:**
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

**Analysis:**
- Response is **STANDARD DRF PAGINATION**
- Shape: `{count, next, previous, results: [...]}`
- **CORRECT** and consistent with DRF best practices
- `results` is properly an ARRAY

---

## 4. GET /api/v1/results/worklist/ (Result Entry Worklist)

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8012/api/v1/results/worklist/
```

**Actual Response:**
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

**Analysis:**
- Response is **STANDARD DRF PAGINATION**
- Shape: `{count, next, previous, results: [...]}`
- **CORRECT** and consistent
- `results` is properly an ARRAY

---

## 5. GET /api/v1/laboratory/tests/ (Test Catalog List)

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8012/api/v1/laboratory/tests/
```

**Actual Response:**
```json
{
  "count": 11,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "test_code": "CBC",
      "test_name": "Complete Blood Count",
      ...
    },
    ...
  ]
}
```

**Analysis:**
- Response is **STANDARD DRF PAGINATION**
- Shape: `{count, next, previous, results: [...]}`
- **CORRECT**
- `results` is properly an ARRAY

---

## 6. POST /api/v1/orders/ (Create Order)

**Expected Request:**
```json
{
  "patient": 1,
  "items": [
    {"test": 1, "quantity": 1}
  ],
  "priority": "routine"
}
```

**Note:** To be tested after fixing patients endpoint

---

## 7. POST /api/v1/payments/ (Record Payment)

**Expected Request:**
```json
{
  "order": 1,
  "amount": 1500.00,
  "payment_method": "cash",
  "notes": "Full payment"
}
```

**Note:** To be tested for sample generation trigger

---

## Conclusion & Recommendations

### Response Pattern Summary:

| Endpoint | Current Pattern | Status | Issue |
|----------|----------------|--------|-------|
| `GET /patients/` | `{count, next, previous, results: {success, data: []}}` | **BROKEN** | results should be array, not object |
| `GET /settings/` | Plain object | ✅ OK | Correct for singleton |
| `GET /samples/pending_collections/` | `{count, next, previous, results: []}` | ✅ OK | Standard DRF |
| `GET /results/worklist/` | `{count, next, previous, results: []}` | ✅ OK | Standard DRF |
| `GET /laboratory/tests/` | `{count, next, previous, results: []}` | ✅ OK | Standard DRF |

### Root Cause Analysis:

**Patients List Endpoint Problem:**

The `apps/patients/views.py` `list()` method at lines 145-157 incorrectly wraps the data:

```python
def list(self, request, *args, **kwargs):
    queryset = self.filter_queryset(self.get_queryset())
    page = self.paginate_queryset(queryset)

    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(
            {"success": True, "data": serializer.data}  # ❌ WRONG
        )
```

This creates malformed response:
```json
{
  "count": 10,
  "next": "...",
  "previous": null,
  "results": {              // ❌ Should be array, is object
    "success": true,
    "data": [...]           // Actual array nested here
  }
}
```

**Standard DRF pagination expects:**
```json
{
  "count": 10,
  "next": "...",
  "previous": null,
  "results": [...]          // ✅ Direct array
}
```

### Fix Strategy:

**Phase 1: Backend Fixes (PRIORITY)**

1. **Fix Patients List Endpoint** - Remove wrapper from `list()` method
   ```python
   # Instead of:
   return self.get_paginated_response({"success": True, "data": serializer.data})
   # Use:
   return self.get_paginated_response(serializer.data)
   ```

2. **Keep wrappers ONLY for action endpoints** (create, update, custom actions)
   - These return `{success: true, data: {...}, message: "..."}`
   - This is acceptable for non-list operations

3. **Standardize pattern:**
   - **List endpoints**: Standard DRF pagination `{count, next, previous, results: []}`
   - **Retrieve/Detail**: Plain object `{id, field1, field2, ...}`
   - **Create/Update/Actions**: Wrapped `{success, data, message?}`

**Phase 2: Frontend Resilience Layer (SAFETY)**

Even with backend fixed, add normalization utilities to prevent future breaks:

```typescript
// Utils to handle API response variations
export function normalizeListResponse<T>(response: any): T[] {
  // Handle various response shapes gracefully
  if (Array.isArray(response)) return response;
  if (response?.results) {
    if (Array.isArray(response.results)) return response.results;
    if (response.results?.data && Array.isArray(response.results.data)) {
      return response.results.data;
    }
  }
  if (response?.data && Array.isArray(response.data)) return response.data;
  return [];
}

export function normalizeObjectResponse<T>(response: any): T | null {
  if (response?.data && typeof response.data === 'object') return response.data;
  if (typeof response === 'object' && !Array.isArray(response)) return response;
  return null;
}
```

**Phase 3: Sample Generation (NEW FEATURE)**

Currently missing: Payment → Sample creation workflow
- When payment is recorded OR order.is_paid set to true
- Automatically create Sample records for each OrderItem
- Set Sample.status = PENDING_COLLECTION
- Must be idempotent (don't duplicate samples)

---

## Action Items:

- [x] Phase 0: Document API contracts with real responses
- [ ] Phase 1: Fix patients list endpoint (remove wrapper from paginated response)
- [ ] Phase 2: Add frontend normalization utilities
- [ ] Phase 3: Implement payment → sample generation
- [ ] Phase 4: Test end-to-end workflow
- [ ] Phase 5: Add comprehensive tests

---