# LIMS Registration Flow Audit

## Current Flow

1.  **Registration Page (`/registration`)**:
    -   Handles both Patient Registration and Order Creation in a single page.
    -   Patient Search:
        -   Start typing in "Mobile Number" to search locally (debounced lookup).
        -   Global search bar in header.
    -   Patient Form:
        -   Fields: Mobile, Name, DOB/Age, Gender, etc.
        -   Age/DOB sync logic exists but is basic.
    -   Test Selection:
        -   Search and add tests to a list.
    -   Payment:
        -   Discount and Paid Amount fields.
    -   Actions:
        -   "Save Patient" button writes to `api/v1/patients/`.
        -   "Create Order" button writes to `api/v1/orders/`.
    -   Receipt:
        -   Modal shows after order creation.

2.  **Order Page (`/orders`)**:
    -   List of orders.
    -   "Create Order" button opens a modal (`CreateOrderModal`).
    -   This modal duplicates some logic from the Registration Page (patient search, test selection).

## Problems Identified

1.  **Duplicated Logic**: Order creation logic exists in both `RegistrationPage.tsx` and `OrdersPage.tsx` (inside `CreateOrderModal`).
2.  **Workflow Separation**: The requirement is to have a distinct "Registration -> Order Creation" flow. Currently, it's mixed in `RegistrationPage`.
3.  **Validation**:
    -   `RegistrationPage` uses `alert()` for validation errors which is poor UX.
    -   Backend errors are shown as alerts with potential JSON dumps.
4.  **Age/DOB Usability**:
    -   Prompts for "Age field too narrow" and "Poor visibility".
    -   Sync logic handles basics but might need refinement for "25y", "2m" formats.
5.  **Keyboard Accessibility**:
    -   `alert()` breaks keyboard flow.
    -   Enter key navigation is not explicitly managed for all fields.
6.  **Layout**:
    -   Current layout might not match the "LIMS-Optimized Registration Layout" specified (Identity -> Contact -> Admin).

## Backend API Endpoints

-   **Patients**: `POST /api/v1/patients/` (Create), `PUT /api/v1/patients/{id}/` (Update), `GET /api/v1/patients/?search={q}` (Search)
-   **Orders**: `POST /api/v1/orders/` (Create order with patient ID, tests, discount, etc.)

## Proposed Changes

1.  **New Route**: Create `/orders/new` (or `/orders/create`) handled by a new `CreateOrderPage` (or utilizing the existing logic refactored).
    -   This page will accept `patient_id` query param or path param.
    -   It will prefill the patient details and focus on Test Selection.

2.  **Refactor `RegistrationPage`**:
    -   **Remove Order Creation Logic**: Strip out test selection, payment, and order submission.
    -   **Redirect**: On successful patient save/update, redirect to `/orders/new?patient_id={id}`.
    -   **Layout**: Reorganize fields into Sections 1, 2, 3 as requested.
    -   **Validation**: Replace `alert()` with inline errors.
    -   **Keyboard**: Implement `onKeyDown` handlers to move focus on Enter.

3.  **Refactor Age/DOB**:
    -   Widen fields.
    -   Implement "smart" age input (parsing "25y", "2m").

4.  **Order Creation Page**:
    -   Extract `CreateOrderModal` logic into a full page `CreateOrderPage`.
    -   Ensure it handles the `patient_id` param to load the patient immediately.

5.  **API Integration**:
    -   Ensure error handling maps 400 errors to fields.
    -   Handle 500 errors gracefully.
