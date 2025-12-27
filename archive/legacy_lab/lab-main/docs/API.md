# API Contracts

All endpoints return JSON. Consistent error envelope: `{error: {code, message, details}}`.

## Authentication

### JWT Authentication
- `POST /api/auth/login/` - Login (returns access + refresh tokens with role)
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout (blacklists refresh token)

## Patients

### Patient Management
- `GET /api/patients/` - List/search patients (supports `?query=` for name/phone/CNIC search)
- `POST /api/patients/` - Create patient (Admin/Reception only)
- `GET /api/patients/:id/` - Get patient details

**Validation:**
- CNIC format: `#####-#######-#`
- Phone: Pakistani mobile format (`+92` or `0` prefix)
- DOB: Must not be in future

## Test Catalog

### Test Management
- `GET /api/catalog/` - List active tests
- `GET /api/catalog/:id/` - Get test details

## Orders

### Order Management
- `GET /api/orders/` - List orders (supports `?patient=id` filter)
- `POST /api/orders/` - Create order with `test_ids` array
- `GET /api/orders/:id/` - Get order with items
- `POST /api/orders/:id/cancel/` - Cancel order (Admin/Reception only)
- `PATCH /api/orders/:id/edit-tests/` - Edit order tests (Admin/Reception only)

**Order States:** NEW → COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED | CANCELLED

**Order Cancellation:**
- Can only cancel orders in NEW status
- Cannot cancel if any samples have been collected or received
- Cancellation also updates all related order items to CANCELLED status
- Shows confirmation dialog before cancellation

**Order Test Editing:**
- Can edit tests (add/remove) before any samples or results exist
- Request body: `{"tests_to_add": [4,5], "tests_to_remove": [3]}`
- Cannot edit cancelled orders
- Cannot edit if samples exist
- Cannot edit if results exist
- Cannot remove all tests without adding new ones
- Requires Admin or Reception role
- Returns updated order with modified items

## Samples

### Sample Collection & Tracking
- `GET /api/samples/` - List samples
- `POST /api/samples/` - Create sample (auto-generates barcode)
- `GET /api/samples/:id/` - Get sample details
- `POST /api/samples/:id/collect/` - Mark collected (Phlebotomy/Admin only)
- `POST /api/samples/:id/receive/` - Mark received (Tech/Pathologist/Admin only)
- `POST /api/samples/:id/reject/` - Reject sample with reason (Tech/Pathologist/Admin only)

**Sample States:** PENDING → COLLECTED → RECEIVED | REJECTED
**Barcode Format:** SAM-YYYYMMDD-NNNN

**Sample Rejection:**
- Requires `rejection_reason` field in request body
- Can only reject samples in PENDING, COLLECTED, or RECEIVED status
- Rejected samples cannot be processed further
- Rejection reason is displayed in UI with red badge

## Results

### Result Entry & Verification
- `GET /api/results/` - List results
- `POST /api/results/` - Create result
- `GET /api/results/:id/` - Get result details
- `POST /api/results/:id/enter/` - Enter result (Technologist/Admin only)
- `POST /api/results/:id/verify/` - Verify result (Pathologist/Admin only)
- `POST /api/results/:id/publish/` - Publish result (Pathologist/Admin only)

**Result States:** DRAFT → ENTERED → VERIFIED → PUBLISHED
**State Machine Enforcement:** Each transition requires previous state completion

## Reports

### PDF Report Generation
- `GET /api/reports/` - List reports
- `GET /api/reports/:id/` - Get report details
- `POST /api/reports/generate/:order_id/` - Generate PDF report (Pathologist/Admin only)
- `GET /api/reports/:id/download/` - Download PDF

**Requirements for Report Generation:**
- All order item results must be in PUBLISHED state
- Uses Al Shifa Laboratory template with official signatories

## Role-Based Access Control (RBAC)

### Roles
1. **ADMIN** - Full access to all endpoints
2. **RECEPTION** - Patient registration, order creation
3. **PHLEBOTOMY** - Sample collection
4. **TECHNOLOGIST** - Sample receiving, result entry
5. **PATHOLOGIST** - Result verification, publishing, report generation

### Permission Matrix

| Endpoint | Admin | Reception | Phlebotomy | Technologist | Pathologist |
|----------|-------|-----------|------------|--------------|-------------|
| Patient CRUD | ✓ | ✓ | ✗ | ✗ | ✗ |
| Order CRUD | ✓ | ✓ | ✗ | ✗ | ✗ |
| Order Cancel | ✓ | ✓ | ✗ | ✗ | ✗ |
| Sample Collect | ✓ | ✗ | ✓ | ✗ | ✗ |
| Sample Receive | ✓ | ✗ | ✗ | ✓ | ✓ |
| Sample Reject | ✓ | ✗ | ✗ | ✓ | ✓ |
| Result Enter | ✓ | ✗ | ✗ | ✓ | ✗ |
| Result Verify | ✓ | ✗ | ✗ | ✗ | ✓ |
| Result Publish | ✓ | ✗ | ✗ | ✗ | ✓ |
| Report Generate | ✓ | ✗ | ✗ | ✗ | ✓ |

## Error Handling

All errors follow consistent envelope:
```json
{
  "error": {
    "code": 400,
    "message": "Validation error",
    "details": {
      "field_name": ["Error message"]
    }
  }
}
```

## Pagination

List endpoints support pagination:
```json
{
  "count": 100,
  "next": "http://api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

Default page size: 20 items

