# Disable Branch & Collection Modules - Impact Report

## 1. Inventory of Affected Components

### Backend Models
- **Core App**:
  - `Branch` (`core.models`)
  - `CollectionCenter` (`core.models`)
  - `TenantSettings` (`core.models`) - *Contains Feature Flags*
  - `RegistrationCounter` (Scope: `center`)
  - `LabDailyCounter` (Scope: `center`)
  - `OrderIdSequence` (Scope: `branch`)
- **Patients App**:
  - `Patient` (`patients.models`): `registration_center` (FK)
- **Orders App**:
  - `Order` (`orders.models`): `collection_center`, `collection_branch`, `processing_branch` (FKs)
  - `Dispatch` (`orders.models`): `from_branch`, `to_branch` (FKs)

### Backend Services & Logic
- **Numbering Services** (`apps.core.numbering`):
  - `generate_registration_number(center, dt)`: Uses center code in format.
  - `generate_lab_number(center, dt)`: Uses center for counter scope.
  - `generate_branch_order_id(tenant, branch, dt)`: Uses branch for ID generation.
- **Model Logic (Hooks)**:
  - `Patient.save()`: Defaults `registration_center` to "00".
  - `Order.save()`: Defaults `collection_center`, `collection_branch`, `processing_branch`.

### API & Views
- **ViewSets**:
  - `BranchViewSet` (`apps.core.views`)
  - `CollectionCenterViewSet` (`apps.core.views`)
     - *Already protected by `FeatureFlagPermission`*
  - `TenantSettingsView` (`apps.core.views`)
- **Serializers**:
  - `PatientSerializer`: Needs validation review.
  - `OrderSerializer`: Needs validation review.

### Frontend
- **Pages**:
  - `BranchesAndCentersPage.tsx`
- **Logic**:
  - `enableBranches` / `enableCollectionCenters` flags used in various components.
  - Registration forms (likely checking for center dropdowns).

## 2. Impact Analysis

### Core Workflow Dependencies
The core workflow (Registration -> Order -> Result -> Report) currently has **hard dependencies** on Branch/Collection Center entities for:
1.  **Number Generation**: MRNs and Accession numbers use Center scope.
2.  **Order ID Generation**: Can be Branch-scoped.
3.  **Defaulting**: Legacy code forces "Head Office" (00) if no center is provided.

### Strategy for Disablement
To disable these modules while keeping core flow functional:
1.  **Feature Flags**: Use `TenantSettings.enable_branches` and `TenantSettings.enable_collection_centers`.
2.  **Data Isolation**: ensuring `Order.collection_center` and `Patient.registration_center` are **NULL** when flags are OFF.
3.  **Service Resiliency**: Update `generate_lab_number` and `generate_registration_number` to handle `None` input by falling back to a default counter scope *internally* without exposing the relationship.

## 3. Disablement Plan
- **Phase 1**: Logic updates in `models.py` (Order/Patient) to stop auto-assignment.
- **Phase 2**: Service updates in `numbering.py` to tolerate None.
- **Phase 3**: Frontend UI hiding (if not already handled by flags).
