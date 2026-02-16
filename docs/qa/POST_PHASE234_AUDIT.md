# Post-Phase 2/3/4 Forensic Audit

This document summarizes the current state of the LIMS codebase after implementing Phase 2, 3, and 4 changes. It serves as a "truth map" for the system as of today.

## A) Current State Architecture Map

### 1. Data Models and Identifiers
| Model | Primary ID | Business ID | Notes |
|-------|------------|-------------|-------|
| **Patient** | `id` (int) | `registration_number` / `patient_id` | MRN (Medical Record Number). Exposted as Registration No. |
| **Order** | `id` (int) | `order_id` / `lab_number` | Represents a "Visit". One patient can have multiple orders. |
| **OrderItem** | `id` (int) | - | Link between Order and Test/Panel. |
| **TestResult** | `id` (int) | - | Holds `result_value` and linking to `TestParameter`. |
| **Payment** | `id` (int) | `REC-######` | Financial transaction linked to an Order. Enables receipt printing. |

**Exposed Identifiers:**
- **Registration No (Patient)**: Used for lookup and history.
- **Lab No (Visit)**: Used for daily tracking and worklist coordination.

### 2. Worklist & Query Logic
- **Endpoint**: `/api/v1/orders/worklist/`
- **Controller**: `WorklistOrdersView` (in `apps/orders/views.py`)
- **Behavior**:
  - Returns **Visits (Orders)**, not Patients.
  - Deduping: If a patient has multiple visits, multiple rows appear (correct).
  - Status Mapping: Maps internal DB states (NEW, COLLECTED, etc.) to human-friendly strings.
  - Filters: Date ranges, Search (Patient name, MRN, Lab No), and Status.

### 3. Receipt Creation Pipeline
- **Flow**: Patient Registration → Create Order → Print Receipt.
- **Logic**:
  - `OrderSerializer.create` accepts `paid_amount`.
  - If `paid_amount > 0`, a `Payment` object is automatically created.
  - The presence of a `Payment` object flag `can_reprint_receipt = true` in the worklist.
  - PDF is generated via `/api/v1/orders/orders/{id}/receipt.pdf`.

### 4. Result Entry & Transitions
- **Logic Location**: `apps/results/services/transitions.py`.
- **States**:
  - `DRAFT` / `ENTERED`: Editable by technicians. Shows in Result Entry Queue.
  - `VERIFIED`: Locked for editing (unless rejected/returned). Shows in Verification Queue.
  - `FINAL`: Immutable after publishing.
- **Rules**:
  - **Saving partial results**: Does not remove items from queues because `WorklistOrdersView` for results checks for pending/unverified parameters.
  - **Required Fields**: Verification is blocked by `BadPayloadError` if `is_required_for_verification` parameters are empty.
  - **Optional Blanks**: Allowed for verification if parameter is not marked required.

### 5. Report Publish Pipeline
- **Endpoint**: `/api/v1/orders/orders/{id}/publish-report/` (POST)
- **Validation**:
  - Uses `collect_report_blockers(order_id)` in `apps/reports/logic.py`.
  - Checks for: `NOT_VERIFIED`, `MISSING_REQUIRED_RESULTS`, `NO_PRINTABLE_ROWS`.
- **Error Reporting**:
  - Returns `400 Bad Request` with structured JSON:
    ```json
    {
      "code": "REPORT_BLOCKED",
      "message": "Report cannot be published.",
      "blocking_reasons": [
        {"reason_code": "MISSING_REQUIRED_RESULTS", "detail": "...", "test_name": "..."}
      ]
    }
    ```

## B) Smoke-Test Matrix (Automatic Tracing)

| Test Case | Description | Expected | Status | Reason |
|-----------|-------------|----------|--------|--------|
| TC-1 | New Patient + First Visit | Receipt created, shows in worklist. | **PASS** | `OrderSerializer` handles auto-payment and redirect. |
| TC-2 | Same Patient + Second Visit | Worklist shows TWO rows with different Lab No. | **PASS** | `WorklistOrdersView` uses `Order` model base. |
| TC-3 | Optional Blanks | Verify passes if parameter is NOT required. | **PASS** | `_has_valid_result_value` logic in `transitions.py`. |
| TC-4 | Required Blank | Verify blocked with "Result value required". | **PASS** | `transition_result_state` enforces required check. |
| TC-5 | Reprint Receipt | Visible in worklist actions. | **PASS** | `can_reprint_receipt` boolean returned by API. |

## C) Bug Ranking & Prioritization

No critical regressions found in the "Truth Map" analysis, but specific guardrails are recommended to ensure persistence.

| Ref | Symptom | Root Cause | Fix | Priority |
|-----|---------|------------|-----|----------|
| P0-1 | Silent "dropping" of items | Weak queue filter logic | Ensure `worklist` query always includes `IN_PROCESS` items if they have ANY unverified result. | P0 (Confirmed Implemented) |
| P0-2 | Generic 400 Errors | Lack of detail in response | Use `collect_report_blockers` to provide explicit reasons for blocking. | P0 (Confirmed Implemented) |

## D) Recommendations & Guardrails

1. **State Persistence**: Never use `update_fields` without including `updated_at` or ensure a full `save()` if business logic depends on timestamps.
2. **Atomic Transitions**: All status changes MUST be wrapped in `transaction.atomic()` with `select_for_update()` to prevent race conditions during multi-technician result entry. (Currently implemented in `transitions.py`).
3. **Frontend Recovery**: `ResultsPage.tsx` autosave features (`localStorage`) must be maintained to prevent data loss on browser refresh/crash.
