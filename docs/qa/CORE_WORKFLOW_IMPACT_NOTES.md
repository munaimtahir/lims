# Core Workflow Impact Notes: Disabling Branch/Collection Modules

## 1. Overview
The Multi-Branch and Collection Center modules have been disabled by feature flags (`enable_branches=False`, `enable_collection_centers=False`).
The goal is to render these modules invisible and inactive while keeping the core Patient -> Order -> Result -> Report workflow fully functional.

## 2. Core Workflow Analysis

| Workflow Step | Dependents | Impact & Mitigation | Status |
|---|---|---|---|
| **Patient Registration** | `registration_center` (FK) | **Mitigated**: Field is now optional. Logic defaults to None if flag OFF. | ✅ Stable |
| **Number Generation** | `RegistrationCounter` | **Mitigated**: `generate_registration_number` uses internal "Head Office" scope for counter if center is None. | ✅ Stable |
| **Order Creation** | `collection_center`, `collection_branch` | **Mitigated**: Fields default to None if flag OFF. | ✅ Stable |
| **Lab Numbering** | `LabDailyCounter` | **Mitigated**: `generate_lab_number` uses internal "Head Office" scope for counter if center is None. | ✅ Stable |
| **Result Entry** | None found | No direct dependency on branch/center. | ✅ Stable |
| **Verification** | None found | No direct dependency on branch/center. | ✅ Stable |
| **Reporting (PDF)** | Address/Phone headers | **Expected**: Should fallback to Global System Settings if branch info is missing. | ⚠️ Verify |

## 3. Configuration

Ensure `TenantSettings` has:
- `enable_branches = False`
- `enable_collection_centers = False`

## 4. Verification Steps (Manual)

1. **Check Flags**: Verify `settings.py` or database has flags disabled.
2. **Register Patient**: Ensure registration succeeds without sending `registration_center`. Verify `registration_center_id` is NULL in DB.
3. **Create Order**: Ensure order creation succeeds. Verify `collection_center_id`, `collection_branch_id` are NULL in DB.
4. **Generate Report**: Verify PDF report shows Global Lab Name/Address, not empty or error.

## 5. Potential Risks

- **Report Header**: If report templates explicitly rely on `order.collection_center.address`, they might show blank space.
  - *Fix*: Ensure report templates fallback to `SystemSettings.lab_address`.
- **Analytics**: Branch-based analytics will be empty (expected).

## 6. Migration Notes
Existing data with Branch/Center relations remains untouched. New data will have NULL relations. Use caution if re-enabling later (mixed null/non-null data).
