# Workflow Call Graph: LIMS End-to-End

This document maps the workflow from UI routes to backend mutations.

## 1. Patient Registration
- **UI Route**: `/dashboard/registration`
- **Component**: `RegistrationPage`
- **Action**: Click "Create Registration"
- **Handler**: `handleSubmit()`
- **API Client**: `patientApi.create(payload)`
- **HTTP Endpoint**: `POST /api/patients/`
- **Backend View**: `PatientViewSet.create` (apps/patients/views.py)
- **Serializer**: `PatientCreateSerializer`
- **DB Mutations**:
  - `Patient`: Insert new record.
- **Status Transitions**: N/A (Initial creation)
- **Side Effects**:
  - Audit Log: `Patient registered`

## 2. Order Creation
- **UI Route**: `/dashboard/orders/create?patient_id={id}`
- **Component**: `CreateOrderPage`
- **Action**: Click "Create Order"
- **Handler**: `handleCreateOrder()`
- **API Client**: `orderApi.create(payload)`
- **HTTP Endpoint**: `POST /api/orders/`
- **Backend View**: `OrderViewSet.create` (apps/orders/views.py)
- **Serializer**: `OrderSerializer` (apps/orders/serializers.py)
- **DB Mutations**:
  - `Order`: Insert new record (status: `NEW`).
  - `OrderItem`: Insert records for each test/panel.
  - `Sample`: Insert records for each `OrderItem` (status: `PENDING`).
  - `Payment`: Insert record if `paid_amount > 0`.
- **Status Transitions**:
  - `Order.status`: `NEW`
- **Side Effects**:
  - Audit Log: `Visit/Order created`
  - Automatic Sample Generation

## 3. Sample Collection & Receipt
- **UI Route**: `/dashboard/collection`
- **Component**: `CollectionWorklistPage`
- **Action**: Mark Collected (in modal)
- **Handler**: `handleConfirmCollection()`
- **API Client**: `sampleApi.updateStatus(id, 'RECEIVED', ...)`
- **HTTP Endpoint**: `PATCH /api/samples/{id}/` (via `SampleViewSet.perform_update`)
- **Backend View**: `SampleViewSet.perform_update` (apps/samples/views.py)
- **Service**: `transition_sample_state` (apps/samples/services.py)
- **DB Mutations**:
  - `Sample`: Update `status` to `RECEIVED`, `collected_at`, `received_at`.
- **Status Transitions**:
  - `Sample.status`: `PENDING` -> `COLLECTED` -> `RECEIVED` (Note: UI skips COLLECTED and goes straight to RECEIVED in some paths)
  - `Order.status`: `NEW` -> `IN_PROCESS` (via `OrderWorkflowService._recalculate_order_status`)
- **Side Effects**:
  - Audit Log: `SAMPLE_STATE_CHANGED`
  - `ensure_test_results(order_item)`: Creates `TestResult` records for all parameters.

## 4. Result Entry
- **UI Route**: `/dashboard/results?orderId={id}&orderItemId={id}`
- **Component**: `ResultsPage`
- **Action**: Click "Save Draft"
- **Handler**: `saveMutation.mutate()`
- **API Client**: `resultApi.bulkEntry(payload)`
- **HTTP Endpoint**: `POST /api/results/bulk_entry/`
- **Backend View**: `TestResultViewSet.bulk_entry` (apps/results/views.py)
- **Service**: `recompute_formulas_for_order_item`, `update_order_item_status`
- **DB Mutations**:
  - `TestResult`: Update `result_value`, `status` to `ENTERED`.
- **Status Transitions**:
  - `OrderItem.status`: `NEW` -> `IN_PROCESS`
  - `Order.status`: `IN_PROCESS` (redundant if already transitioned)
- **Side Effects**:
  - Audit Log: `RESULT_VALUE_UPDATED`
  - Formula recalculation

## 5. Result Verification
- **UI Route**: `/dashboard/results` (Result Entry) or `/dashboard/verification` (Verification Queue)
- **Component**: `ResultsPage` or `VerificationQueuePage`
- **Action**: Click "Verify" or "Verify All"
- **Handler**: `handleSaveAndVerify()` or `handleVerifyAll()`
- **API Client**: `resultApi.bulkVerify(ids)`
- **HTTP Endpoint**: `POST /api/results/bulk_verify/`
- **Backend View**: `TestResultViewSet.bulk_verify` (apps/results/views.py)
- **Service**: `transition_result_state` (apps/results/services/transitions.py)
- **DB Mutations**:
  - `TestResult`: Update `status` to `VERIFIED`.
- **Status Transitions**:
  - `OrderItem.status`: `IN_PROCESS` -> `VERIFIED` (if all results verified)
  - `Order.status`: `IN_PROCESS` -> `VERIFIED` (if all required results verified)
- **Side Effects**:
  - Audit Log: `RESULT_VERIFIED`

## 6. Report Publishing
- **UI Route**: `/dashboard/verification`
- **Component**: `VerificationQueuePage`
- **Action**: Click "Publish Report"
- **Handler**: `handlePublishReport()`
- **API Client**: `orderApi.publishReport(orderId)`
- **HTTP Endpoint**: `POST /api/orders/{id}/publish_report/`
- **Backend View**: `OrderViewSet.publish_report` (apps/orders/views.py)
- **Logic**: `generate_v2_report` (apps/reports/logic.py)
- **DB Mutations**:
  - `Report`: Insert new record with PDF file.
  - `Order`: Update `status` to `PUBLISHED`.
  - `TestResult`: Update `status` to `FINAL`.
- **Status Transitions**:
  - `Order.status`: `VERIFIED` -> `PUBLISHED`
- **Side Effects**:
  - PDF Generation
  - Audit Log: `PUBLISHED` transition via `transition_visit_state`
