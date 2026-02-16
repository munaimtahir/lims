# Phase 1: LIMS Workflow Audit & Truth Map

**Date:** 2026-02-16  
**Version:** 1.0  
**Scope:** Backend & Frontend Audit (Read-Only)

---

## 1. Entity & Relationship Map (Current State)

The current system uses the following core entities to model the laboratory workflow.

### **Core Entities**
*   **Patient (`apps/patients/models.py`)**
    *   **Identity:** `patient_id` (P-YYYY-NNNNN), `mrn`.
    *   **Key Fields:** `registration_number` (YYMM-CC-SSSS), `full_name`, `phone`, `gender`.
    *   **Role:** Represents the human subject. One-to-Many relationship with Orders.
*   **Order (Visit) (`apps/orders/models.py`)**
    *   **Identity:** `order_id` (ORD-YYYYMMDD-NNNN), `lab_number` (MDD-XXX + `daily_serial`).
    *   **Role:** Acts as the **Visit**. The user requirement "One Visit = One Order" is technically true in current data structure, though strict "Visit" entity is implicit.
    *   **State Machine:** `NEW` -> `COLLECTED` -> `IN_PROCESS` -> `VERIFIED` -> `PUBLISHED` -> `FINAL`.
    *   **Relationships:** Belongs to `Patient`. Contains many `OrderItem`s.
*   **OrderItem (`apps/orders/models.py`)**
    *   **Role:** Link between Order and Test/Panel.
    *   **Status:** Matches Order status workflow.
*   **TestResult (`apps/results/models.py`)**
    *   **Identity:** `order_item` + `test_parameter`.
    *   **Role:** Holds the actual value (`result_value`), status (`DRAFT`, `ENTERED`, `VERIFIED`), and flags.
*   **Payment (Receipt) (`apps/billing/models.py`)**
    *   **Role:** Represents a financial transaction.
    *   **Relationship:** Linked to `Order`.
    *   **Receipts:** Generated only if a `Payment` record exists. Order `is_paid` flag is derived from `sum(payments) >= net_amount`.

### **ERD Narrative**
> `Patient` (1) <---> (N) `Order` (Implicit Visit)  
> `Order` (1) <---> (N) `OrderItem`  
> `OrderItem` (1) <---> (N) `TestResult`  
> `Order` (1) <---> (N) `Payment`

---

## 2. Worklist & ID Behavior Analysis

### **A. ID Generation**
| ID Type | Generator Location | Logic | Uniqueness |
| :--- | :--- | :--- | :--- |
| **Registration No** (`patient_id`) | `Patient.save` (apps/patients/models.py:222) | `P-YYYY-NNNNN` (via `generate_mrn`) | Global per Tenant |
| **Lab No** (`lab_number`) | `Order.save` (apps/orders/models.py:242) | `MDD-XXX` (via `generate_lab_number`) + `daily_serial` | Per Collection Center + Date |
| **Order ID** | `Order.save` (apps/orders/models.py:197) | `ORD-YYYYMMDD-NNNN` | Global per Tenant |

### **B. Worklist Behavior (Root Cause of "Latest Only")**
The "Patients Worklist" UI displays **only the single latest order per patient**, effectively hiding concurrent or historical active visits.

*   **Backend Source:** `apps/orders/views.py` -> `WorklistPatientsView`
*   **Root Cause Code:**
    ```python
    # filters previous orders for same patient
    latest_order_subquery = orders.filter(patient=OuterRef("pk")).order_by("-created_at")
    
    # Selecting from Patient, not Order
    patients = Patient.objects.annotate(
        latest_order_id=Subquery(latest_order_subquery.values("id")[:1]),
        ...
    ).filter(latest_order_id__isnull=False)
    ```
*   **Impact:** If a patient has an active order from today and an unfinished one from yesterday, the list **only shows today's order**. The older one becomes inaccessible from this view.
*   **Frontend Contract:** Expects `WorklistPatient` list, grouped by patient ID.

### **C. Receipt Pipeline**
*   **Creation Path:** `Order` creation does not automatically create a receipt.
*   **Failure Point:** A `Payment` record must be explicitly created via `PaymentViewSet` or during the registration transaction. If the frontend creates an Order but fails/skips the Payment API call, the Order exists as `is_paid=False` and **no receipt is generated/printable**.
*   **Printing:** Depends on `patient.latest_order_id in payments` (Lines 314-318 in `apps/orders/views.py`).

---

## 3. Workflow Diagnostics

### **A. Result Entry Disappearance**
We observed that partially saved results disappear from the "Pending Entry" worklist.

*   **Component:** `ResultEntryWorklistPage` -> `TestResultViewSet.worklist`
*   **Root Cause:** The query logic excludes items as soon as *any* result is entered, if placeholders (DRAFT) are missing.
    ```python
    # apps/results/views.py:166
    .filter(Q(rc=0) | Q(results__status="DRAFT"))
    ```
*   **Scenario:**
    1.  User enters value for Parameter A. Status becomes `ENTERED`.
    2.  Parameter B is empty (no row exists yet) or also `ENTERED`.
    3.  `rc` (result count) is now > 0.
    4.  `results__status` is `ENTERED`, not `DRAFT`.
    5.  **Result:** The condition `Q(rc=0) | Q(results__status="DRAFT")` evaluates to `False`. The item vanishes.

### **B. Report Publishing**
*   **Status:** `Order` status must transition `VERIFIED` -> `PUBLISHED`.
*   **Validation:** `transition_visit_state` checks permissions (`can_verify_results`).
*   **PDF Generation:** `report_pdf` endpoint strictly requires `status="PUBLISHED"`.
*   **Potential 400:** If `Payment` logic or `TestResult` finalization isn't complete (though `validate_status_transition` only checks state graph). The most common user-facing 400 is likely attempting to print/publish a report that hasn't been generated or is in the wrong status.

---

## 4. Fix Plan (Phase 2-4)

### **Phase 2: Critical Workflow Fixes (Next Step)**
1.  [ ] **Fix Worklist Query:** Change `WorklistPatientsView` to select from `Order` (grouped by Visit/Lab No) instead of `Patient`.
    *   *Target:* `apps/orders/views.py`
2.  [ ] **Fix Result Disappearance:** Update `TestResultViewSet.worklist` to include items with `status__in=["DRAFT", "ENTERED"]` explicitly, regardless of count.
    *   *Target:* `apps/results/views.py`
3.  [ ] **Unified Identifier:** Expose `Lab Number` as the primary identifier in Worklist.

### **Phase 3: Result Entry & Printing**
1.  [ ] **Result Placeholder Logic:** Ensure `ensure_test_results` is called reliably or query handles missing rows.
2.  [ ] **Printing Rules:** Implement `omit_blank_parameters` logic in report generation.

### **Phase 4: Guardrails**
1.  [ ] **Receipt Enforce:** Transactional creation of Order + Payment.

---

## 5. Files for Phase 2 Modification
*   `lims-backend/apps/orders/views.py` (Worklist logic)
*   `lims-backend/apps/results/views.py` (Result worklist logic)
*   `lims-backend/apps/orders/serializers.py` (Data contract updates)
*   `frontend/src/pages/patient-worklist/PatientsWorklistPage.tsx` (UI to handle Visit-based rows)
