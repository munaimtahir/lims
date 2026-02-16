# Feature Flags Implementation

## 1. Feature Flag Locations
The feature flags are located in the `TenantSettings` model (within `apps/core/models.py`).

The flags are:
- `enable_branches` (default: `False`)
- `enable_collection_centers` (default: `False`)
- `sample_workflow_enabled` (default: `False`, often relevant if branch/centers disabled)

## 2. Default Configuration (Code)

```python
class TenantSettings(models.Model):
    # ...
    enable_branches = models.BooleanField(
        default=False,
        # ...
    )
    enable_collection_centers = models.BooleanField(
        default=False,
        # ...
    )
    # ...
```

## 3. Disablement Mechanism

When these flags are **FALSE**:

- **Backend**:
  - `FeatureFlagPermission` logic returns `404 Not Found` for key CRUD endpoints.
  - Core models (Patient/Order) are modified (Phase 3) to:
    - NOT assign default branch/collection relations.
    - Validate successfully with `None` references.
  - Number generation services (Phase 3) fall back to a "Head Office" counter scope *internally* but do NOT expose the relationship.

- **Frontend**:
  - UI checks `enableBranches` and `enableCollectionCenters` from the `/api/core/features/` endpoint.
  - Routes and menu items are hidden.
  - Form fields are hidden/disabled.

## 4. Verification

To verify disablement:
1. Ensure `TenantSettings` for the active tenant has flags set to False.
2. Check CRUD endpoints (`/api/core/branches/`) return 404.
3. Check Registration/Order APIs accept successful payload without branch/collection fields.
4. Check that created entities have `collection_center=None` and `collection_branch=None` in DB.
