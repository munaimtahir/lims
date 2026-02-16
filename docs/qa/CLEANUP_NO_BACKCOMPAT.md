# Cleanup Pass: No Backward Compatibility

This pass removed all legacy contracts and enforced canonical data/API shapes for a fresh project start.

## 1. Removed Legacy Contracts

The following backward-compatibility fields and response shapes were removed from the API:

### Backend (apps/orders/views.py)
- **Removed Fields from Worklist Response:**
  - `latest_order_id` (Redundant, use `id`)
  - `latest_order_number` (Use `lab_number`)
  - `latest_order_created_at` (Use `created_at`)
  - `receipt_url` (Redundant, use `receipt_pdf_url`)
  - `report_url` (Redundant, use `report_pdf_url`)
  - `order_pk` (Redundant, use `id`)
  - `patient_id` (Moved to nested `patient.id`)
  - `patient_mrn` (Moved to nested `patient.registration_number`)
  - `patient_name` (Moved to nested `patient.full_name`)
  - `mobile` (Moved to nested `patient.phone`)
  - `gender` (Moved to nested `patient.gender`)
  - `age_years` (Moved to nested `patient.age_years`)
  - `age_months` (Moved to nested `patient.age_months`)
  - `age_days` (Moved to nested `patient.age_days`)

- **Standardization:**
  - The worklist endpoint now returns a list of **Orders (Visits)** only.
  - Every row in the worklist represents a unique Order.

### Frontend
- **Removed Types:**
  - `WorklistPatient` (Replaced by `WorklistOrder`)
- **Refactored Pages:**
  - `PatientsWorklistPage.tsx` refactored to use `WorklistOrder` and canonical nested patient shape.
  - Navigation now uses `order.id` and `lab_number` consistently.

## 2. Canonical API Shape: Worklist

Endpoint: `GET /api/v1/worklist/patients/` (Legacy name kept for URL stability, but returns Orders)

### Response Shape (Item in results)
```json
{
  "id": 123,
  "lab_number": "2602-HQ-0001",
  "order_id": "ORD-12345",
  "status": "COLLECTED",
  "current_status": "Sample Collected",
  "created_at": "2026-02-16T13:50:00Z",
  "is_paid": true,
  "can_reprint_receipt": true,
  "can_reprint_report": false,
  "receipt_pdf_url": "/api/v1/orders/orders/123/receipt.pdf",
  "report_pdf_url": null,
  "patient": {
    "id": 45,
    "registration_number": "MRN-1001",
    "full_name": "John Doe",
    "age": 35,
    "gender": "Male",
    "phone": "03001234567",
    "age_years": 35,
    "age_months": 0,
    "age_days": 10
  }
}
```

## 3. Database & Migrations Hygiene

- **Linear Migrations:** Verified that all apps have linear migration histories.
- **Empty DB Support:** Confirmed that `python manage.py migrate` succeeds on a fresh SQLite/PostgreSQL database without `NodeNotFound` errors.
- **Dependencies:** Orphan dependencies in `apps/orders` and `apps/patients` have been resolved.

## 4. Maintenance Notes
- All future worklist items should be added to the nested `patient` object if they are patient-specific, or to the root object if they are order-specific.
- Avoid flat fields at the root level for patient-related data.
