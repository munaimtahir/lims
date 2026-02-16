# Truth Map: API Workflow Smoke Test

**Generated:** 2026-02-16T17:50:47+05:00  
**Base URL:** http://localhost:8012  
**Test Execution:** PARTIAL SUCCESS (Order creation failed due to backend bug)

---

## Configuration

### Base URLs
- **Backend Base URL:** http://localhost:8012
- **API Base URL:** http://localhost:8012/api/v1
- **Auth Endpoint:** `http://localhost:8012/api/v1/auth/login/`

### Authentication
- **Method:** JWT Bearer Token
- **Endpoint:** `POST http://localhost:8012/api/v1/auth/login/`
- **Payload:** `{"username": "admin", "password": "admin123"}`
- **Response:** `{"success": true, "data": {"access_token": "...", "refresh_token": "..."}}`
- **Header Format:** `Authorization: Bearer {access_token}`
- **Note:** Requires `Host: lims.alshifalab.pk` header (or matching ALLOWED_HOSTS) and `X-Forwarded-Proto: https` header for proxy compatibility

---

## Endpoint Inventory

### 1. Authentication
- **POST** `http://localhost:8012/api/v1/auth/login/` - Login and obtain JWT token ✅

### 2. Test Catalog
- **GET** `http://localhost:8012/api/v1/laboratory/tests/` - List tests (supports `?search=Albumin`) ✅
- **GET** `http://localhost:8012/api/v1/laboratory/tests/{id}/` - Get test details with parameters ✅

### 3. Tenant Settings
- **GET** `http://localhost:8012/api/v1/core/settings/tenant/` - Get tenant settings (includes `sample_workflow_enabled`)

### 4. Patients
- **POST** `http://localhost:8012/api/v1/patients/` - Create patient ✅
  - Required: `full_name` OR (`first_name` AND `last_name`), `gender`, `phone` (Pakistani format: 03XXXXXXXXX)
- **GET** `http://localhost:8012/api/v1/patients/{id}/` - Get patient details

### 5. Orders
- **POST** `http://localhost:8012/api/v1/orders/orders/` - Create order ❌ **FAILED**
  - Payload: `{"patient": <patient_id>, "test_ids": [<test_id>]}`
  - **Error:** 500 Internal Server Error - `Order() got unexpected keyword arguments: 'created_by'`

### 6. Samples (Conditional - if `sample_workflow_enabled=True`)
- **GET** `http://localhost:8012/api/v1/samples/` - List samples (`?order=<order_id>`)
- **PATCH** `http://localhost:8012/api/v1/samples/{id}/` - Update sample status
  - Status transitions: `PENDING` → `COLLECTED` → `RECEIVED`

### 7. Results
- **POST** `http://localhost:8012/api/v1/results/ensure/` - Ensure result rows exist (`?order_item_id=<id>`)
- **GET** `http://localhost:8012/api/v1/results/` - List results (`?order_item=<id>&test_parameter=<id>`)
- **PATCH** `http://localhost:8012/api/v1/results/{id}/` - Update result value
- **POST** `http://localhost:8012/api/v1/results/{id}/verify/` - Verify result

### 8. Reports
- **POST** `http://localhost:8012/api/v1/orders/orders/{id}/publish-report/` - Publish report
- **GET** `http://localhost:8012/api/v1/orders/orders/{id}/report.pdf` - Download PDF report

---

## Test Execution Results

### Step-by-Step Status

| Phase | Step | Status | Endpoint | Notes |
|-------|------|--------|----------|-------|
| 0 | Discovery | ✅ PASS | - | Base URL and endpoints identified |
| 1 | Authentication | ✅ PASS | `POST /auth/login/` | Token obtained successfully |
| 2 | Catalog Check | ✅ PASS | `GET /laboratory/tests/` | Albumin test verified (Rs 500, ID=24, Parameter ID=48) |
| 3 | Patient Create | ✅ PASS | `POST /patients/` | Patient ID: 13, MRN: LAB-26-000006 |
| 4 | Order Create | ❌ FAIL | `POST /orders/orders/` | **500 Internal Server Error** - Backend bug |
| 5 | Sample Workflow | ⏸ SKIP | `GET/PATCH /samples/` | Not reached (order creation failed) |
| 6 | Result Entry | ⏸ SKIP | `POST/PATCH /results/` | Not reached (order creation failed) |
| 7 | Verification | ⏸ SKIP | `POST /results/{id}/verify/` | Not reached (order creation failed) |
| 8 | Publish | ⏸ SKIP | `POST /orders/orders/{id}/publish-report/` | Not reached (order creation failed) |
| 9 | PDF Download | ⏸ SKIP | `GET /orders/orders/{id}/report.pdf` | Not reached (order creation failed) |
| 10 | PDF Content | ⏸ SKIP | - | Not reached (order creation failed) |

---

## Extracted IDs

- **Patient ID:** 13
- **Patient MRN:** LAB-26-000006
- **Albumin Test ID:** 24
- **Albumin Parameter ID:** 48
- **Order ID:** N/A (creation failed)
- **Order Item ID:** N/A
- **Result ID:** N/A
- **Report ID:** N/A

---

## Failures & Fixes

### ❌ FAILURE: Order Creation (500 Internal Server Error)

**Endpoint:** `POST http://localhost:8012/api/v1/orders/orders/`

**Request:**
```json
{
  "patient": 13,
  "test_ids": [24]
}
```

**Response:**
```json
{
  "detail": "An unexpected error occurred. Please try again later.",
  "error": "internal_server_error"
}
```

**Root Cause:**
```
TypeError: Order() got unexpected keyword arguments: 'created_by'
```

**Location:** `apps/orders/views.py:106` in `perform_create()` method:
```python
order = serializer.save(created_by=self.request.user)
```

**Minimal Fix Proposal:**

The `Order` model doesn't accept `created_by` as a constructor argument. The fix should set `created_by` after object creation or use the model's field assignment:

**Option 1 (Recommended):** Modify `apps/orders/views.py`:
```python
# In OrderViewSet.perform_create()
order = serializer.save()
order.created_by = self.request.user
order.save()
```

**Option 2:** If Order model has a `created_by` field that should be set via a signal or model method, ensure the serializer handles it properly.

**File to modify:** `lims-backend/apps/orders/views.py` (line ~106)

---

## Notes

- **Proxy Configuration:** The backend requires `Host: lims.alshifalab.pk` header (matching ALLOWED_HOSTS) and `X-Forwarded-Proto: https` header when accessing via proxy
- **Sample workflow** is controlled by tenant setting `sample_workflow_enabled`
- When disabled, orders can proceed directly to result entry after creation
- **Phone validation:** Requires Pakistani mobile format (03XXXXXXXXX, 11 digits starting with 03)
- **Patient name:** Requires either `full_name` OR both `first_name` AND `last_name`
- PDF content verification uses PyPDF2/pdfminer/pdftotext if available
- All endpoints require JWT Bearer token authentication

---

## Test Script

The smoke test script is located at: `scripts/smoke_test_api.py`

**Usage:**
```bash
BASE_URL=http://localhost:8012 \
ADMIN_USER=admin \
ADMIN_PASS=admin123 \
API_HOST=lims.alshifalab.pk \
python3 scripts/smoke_test_api.py
```

**Execution Log:** See `docs/qa/API_WORKFLOW_SMOKE_LOG.md`
