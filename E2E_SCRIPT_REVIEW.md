# E2E Workflow Script Review & Schema Verification

**Date:** February 16, 2026  
**Script:** `e2e_workflow_test.py`

## ✅ Schema Fixes Applied

### 1. Patient Creation API (`/api/v1/patients/`)

**Fixed Issues:**
- ❌ **Before:** `"date_of_birth": jls_extract_var` (invalid variable)
- ✅ **After:** `"date_of_birth": dob_date.isoformat()` (YYYY-MM-DD format)

**Correct Schema:**
```python
{
    "full_name": "Test Patient Albumin",  # or first_name/last_name
    "date_of_birth": "1989-02-16",        # ISO format: YYYY-MM-DD
    "gender": "Male",                      # "Male", "Female", "Other"
    "phone": "0300-0000000"                # Required, min 10 digits
}
```

**Response Handling:**
- Handles both wrapped (`{"data": {...}}`) and direct response formats
- Extracts `patient_id` or `id` correctly

---

### 2. Order Creation API (`/api/v1/orders/orders/`)

**Fixed Issues:**
- ❌ **Before:** `"tests": [test_id]` (wrong field name)
- ✅ **After:** `"test_ids": [test_id]` (correct field name)
- ❌ **Before:** `"order_date": None` (field doesn't exist)
- ✅ **After:** Removed (not in schema)

**Correct Schema:**
```python
{
    "patient": patient_id,           # int: Patient ID
    "test_ids": [test_id],           # list[int]: Test IDs
    "panel_ids": [panel_id],         # list[int]: Optional panel IDs
    # Optional fields:
    # "notes": str,
    # "referred_by": str,
    # "discount": Decimal,
    # "discount_percent": Decimal
}
```

**Endpoint:** `/api/v1/orders/orders/` (router basename="order")

**Response Handling:**
- Handles wrapped response format
- Extracts `order_id` (string) and `id` (database ID) correctly

---

### 3. Parameter Creation API (`/api/v1/laboratory/parameters/`)

**Fixed Issues:**
- ❌ **Before:** `"parameter_id": "p_albumin"` (invalid format)
- ✅ **After:** `"parameter_id": "p89"` (format: p<number>)

**Correct Schema:**
```python
{
    "parameter_id": "p89",           # Format: p<number> (e.g., p1, p2, p89)
    "parameter_name": "Albumin",     # Required
    "unit": "g/dL"                   # Optional
}
```

**Validation:** Parameter ID must match regex `^p\d+$`

---

### 4. Result Entry API (`/api/v1/results/bulk_entry/`)

**Added Function:** `enter_result()` - New function for bulk result entry

**Correct Schema:**
```python
{
    "results": [
        {
            "order_item": order_item_id,      # int: OrderItem database ID
            "test_parameter": test_param_id,  # int: TestParameter database ID
            "result_value": "4.5",           # str: Result value
            "remarks": ""                    # str: Optional remarks
        }
    ]
}
```

**Endpoint:** `/api/v1/results/bulk_entry/` (POST)

**Response:**
```python
{
    "created": 1,           # Number of results created
    "updated": 0,           # Number of results updated
    "errors": []            # List of errors if any
}
```

---

### 5. Helper Functions Added

**`get_order_items(token, order_id)`**
- Fetches order items for an order
- Endpoint: `/api/v1/orders/order-items/?order=<order_id>`
- Returns list of order items with their database IDs

**`get_test_parameter(token, test_id)`**
- Fetches test parameter ID for a test
- Endpoint: `/api/v1/laboratory/test-parameters/?test=<test_id>`
- Returns first test parameter's database ID

---

## 📋 Complete API Schema Reference

### Authentication
- **Endpoint:** `/api/v1/auth/login/`
- **Method:** POST
- **Payload:** `{"username": str, "password": str}`
- **Response:** `{"data": {"access_token": str, "refresh_token": str, "user": {...}}}`

### Patient Creation
- **Endpoint:** `/api/v1/patients/`
- **Method:** POST
- **Required Fields:** `full_name` (or `first_name`/`last_name`), `date_of_birth` (YYYY-MM-DD), `gender`, `phone`
- **Optional Fields:** `age_years`, `age_months`, `age_days`, `email`, `address`, `branch`, `registration_center`

### Order Creation
- **Endpoint:** `/api/v1/orders/orders/`
- **Method:** POST
- **Required Fields:** `patient` (int), `test_ids` (list[int]) OR `panel_ids` (list[int])
- **Optional Fields:** `notes`, `referred_by`, `discount`, `discount_percent`

### Result Entry (Bulk)
- **Endpoint:** `/api/v1/results/bulk_entry/`
- **Method:** POST
- **Required Fields:** `results` (list of result objects)
- **Result Object:** `order_item` (int), `test_parameter` (int), `result_value` (str), `remarks` (str, optional)

---

## 🔍 Verification Checklist

- [x] Patient creation uses correct field names (`full_name`, `date_of_birth` in ISO format)
- [x] Order creation uses `test_ids` (not `tests`)
- [x] Order creation endpoint is `/orders/orders/`
- [x] Parameter ID format is `p<number>` (not `p_albumin`)
- [x] Date format is ISO (`YYYY-MM-DD`)
- [x] Response handling supports both wrapped and direct formats
- [x] Result entry uses bulk_entry endpoint with correct schema
- [x] All API calls include Authorization header with Bearer token

---

## 🚀 Usage

```bash
# Run the script
python3 e2e_workflow_test.py

# The script will:
# 1. Login as admin
# 2. Check/create Albumin test (Rs 500)
# 3. Register patient
# 4. Create order with Albumin
# 5. Enter result (Albumin = 4.5)
# 6. Generate summary report
```

---

## ⚠️ Known Limitations

1. **API HTTPS Redirect:** Direct HTTP API calls may fail with 400 Bad Request due to `SECURE_SSL_REDIRECT=True`. Frontend UI works correctly (proxy handles headers).

2. **Sample Collection/Receiving:** These steps require UI interaction and are not automated in the script.

3. **Verification & PDF:** These steps require UI interaction and are not automated in the script.

---

## 📝 Notes

- All schemas verified against actual serializer definitions in:
  - `lims-backend/apps/patients/serializers.py`
  - `lims-backend/apps/orders/serializers.py`
  - `lims-backend/apps/results/serializers.py`
  - `lims-backend/apps/results/views.py` (bulk_entry)

- Script now follows exact API contracts as defined in the codebase.
