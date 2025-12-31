# Migration Report & Plan

## 1. Feature Inventory & Decision Table

| ID | Feature | Status (Backend) | Status (Frontend) | Action Required |
|:---:|:---|:---:|:---:|:---|
| **A1** | Patient registration (quick entry) | ✅ Implemented | ⚠️ Partial | Implement simplified registration form |
| **A2** | Patient history / timeline | ✅ Implemented | ❌ Missing | Build Patient Detail/History View |
| **B1** | Test catalog CRUD | ✅ Implemented | ❌ Missing | Build Test Catalog Management UI |
| **B2** | Reference ranges (age/gender) | ✅ Implemented | ❌ Missing | Build Reference Range Management UI |
| **B3** | Excel / bulk import | ❌ Missing | ❌ Missing | Implement Excel Import Logic & UI |
| **C1** | Order creation (multi-test) | ✅ Implemented | ⚠️ Partial | Refine Order Entry Form |
| **C2** | Sample collection | ✅ Implemented | ❌ Missing | Build Phlebotomy/Collection Screen |
| **C3** | Sample rejection workflow | ✅ Implemented | ❌ Missing | Add Rejection Dialog/Action |
| **C4** | Order cancellation rules | ✅ Implemented | ❌ Missing | Add Cancellation Action with logic |
| **C5** | Partial order handling | ✅ Implemented | ❌ Missing | Ensure UI handles partial states |
| **D1** | Result entry per test | ✅ Implemented | ❌ Missing | Build Result Entry Grid |
| **D2** | Result lifecycle (verify/approve) | ✅ Implemented | ❌ Missing | Add Verification/Approval Actions |
| **D3** | Critical value alerts | ✅ Implemented | ❌ Missing | Add UI Flags/Alerts for Criticals |
| **D4** | Test-level comments | ✅ Implemented | ❌ Missing | Add Comment Field in Result Entry |
| **D5** | Report-level remarks | ✅ Implemented | ❌ Missing | Add Remarks in Verification Screen |
| **E1** | PDF report generation | ✅ Implemented | ❌ Missing | Connect "Download Report" button |
| **F1** | Daily worklists | ✅ Implemented | ❌ Missing | Build Departmental Worklists |
| **F2** | Barcode / sample label | ✅ Implemented | ❌ Missing | Add "Print Label" Action |
| **G1** | Patient screens | ✅ Implemented | ⚠️ Partial | Polish Patient List/Search |
| **G2** | Order & sample workflow screens | ✅ Implemented | ❌ Missing | Build Workflow Screens |
| **G3** | Result entry screens | ✅ Implemented | ❌ Missing | Build Result Entry Screens |
| **G4** | Report viewing | ✅ Implemented | ❌ Missing | Build Report Viewer |
| **G5** | Basic dashboard | ✅ Implemented | ❌ Missing | Build Dashboard Widgets |

## 2. Implementation Plan

### Phase 1: Planning (Current)
- Analyzed `lims-backend` and confirmed high coverage of required models and logic.
- Identified `frontend` structure exists but screens are largely missing or skeletal.
- Identified `B3` (Excel/Bulk Import) as the primary missing backend feature.

### Phase 2: Implementation Steps

#### Step 1: Backend Gaps (Bulk Import)
- **Task:** Implement Bulk Import for Test Catalog and Reference Ranges.
- **Details:** Add `BulkImportViewSet` in `laboratory` app to handle Excel files. parsing logic for Tests and Reference Ranges.
- **Verification:** Unit tests for import logic.

#### Step 2: Frontend - Core Infrastructure
- **Task:** Verify Authentication and Base Layout.
- **Details:** Ensure Login works, Sidebar navigation is correct, and API client is configured.
- **Verification:** Login successful, token stored, navigation functional.

#### Step 3: Frontend - Patient & Registration (A1, A2, G1)
- **Task:** Build Patient List and Registration Forms.
- **Details:**
    - `PatientList` with search/filter.
    - `PatientRegistration` modal/page.
    - `PatientDetail` with history tab.
- **Verification:** Create patient, view patient, search patient.

#### Step 4: Frontend - Test Catalog (B1, B2, B3)
- **Task:** Build Test Catalog Management.
- **Details:**
    - List Tests.
    - Add/Edit Test form.
    - Reference Range editor.
    - Bulk Import UI.
- **Verification:** Add test, set ranges, import excel.

#### Step 5: Frontend - Order Entry (C1, C4, C5)
- **Task:** Build Order Management.
- **Details:**
    - `OrderCreate` with patient selector and test selector.
    - `OrderList` with status filters.
    - Order cancellation.
- **Verification:** Create order, cancel order.

#### Step 6: Frontend - Sample Collection (C2, C3, F2)
- **Task:** Build Phlebotomy Worklist.
- **Details:**
    - `CollectionList` (Pending samples).
    - Collect action (generate barcode/time).
    - Reject action (reason).
    - Print Label stub (display barcode).
- **Verification:** Collect sample, reject sample.

#### Step 7: Frontend - Result Entry & Validation (D1-D5, F1)
- **Task:** Build Lab Technician & Pathologist Views.
- **Details:**
    - `ResultEntry` (Worksheet style).
    - `ResultVerification` (Pathologist view).
    - Critical alerts visibility.
- **Verification:** Enter results, verify, check flags.

#### Step 8: Frontend - Reporting & Dashboard (E1, G4, G5)
- **Task:** Build Dashboard and Report Access.
- **Details:**
    - Dashboard widgets (counts, charts).
    - Report download in Order/Patient view.
- **Verification:** View dashboard, download PDF.

### Phase 3: Testing & Verification
- Run full backend test suite.
- Run frontend type check and lint.
- Manual end-to-end flow verification.

### Phase 4: Cleanup
- Delete `lab_old/`
- Delete `archive/`

## 3. Immediate Next Actions
1.  Verify if `apps/laboratory` already has import logic hidden in utils (I saw some "Excel import support" mentions in docstrings).
2.  If yes, expose it. If no, build it.
3.  Start Frontend Step 2.
