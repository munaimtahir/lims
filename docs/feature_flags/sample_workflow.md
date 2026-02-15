# Sample Workflow (Tenant Toggle)

## Overview

The **sample workflow** is an optional module controlled by a tenant-level setting: `sample_workflow_enabled` (boolean). When **enabled** (default), the lab uses the full sample collection and receiving pipeline before result entry. When **disabled**, small-scale labs can skip sample steps: after patient registration and receipt/payment, the case moves directly into Result Entry → Verification → Report Publish.

## Setting

- **Model:** `core.TenantSettings.sample_workflow_enabled`
- **Default:** `True` (backward compatible: existing tenants keep current behavior)
- **Editable:** Yes, in Admin/Settings UI (Settings → Lab Workflow tab) and via API `PATCH /api/v1/core/settings/tenant/`
- **Audit:** `updated_by` and `updated_at` are stored; `TENANT_SETTINGS_UPDATED` audit event is emitted on change

## Behavior Summary

| `sample_workflow_enabled` | Sample menus / routes | Sample API (list, create, update, etc.) | Result entry eligibility | Order transition NEW → … |
|---------------------------|------------------------|------------------------------------------|--------------------------|---------------------------|
| **True**                  | Visible                | Allowed                                  | Only after sample collected/received | NEW → COLLECTED → IN_PROCESS → … |
| **False**                 | Hidden; direct URL redirects | 403 with message “Sample workflow is disabled…” | Paid orders eligible immediately | NEW → IN_PROCESS allowed (skip COLLECTED) |

## Backend Rules

### When `sample_workflow_enabled = False`

- **Sample endpoints** (e.g. `/api/v1/samples/`, collection/receiving actions): return **403** with a clear message that the module is disabled.
- **Result worklist** (`/api/v1/results/worklist/`): includes order items from **paid** orders in status NEW/COLLECTED/IN_PROCESS (no requirement for sample collected/received).
- **Order transitions:** Order can go **NEW → IN_PROCESS** (skip COLLECTED). Result entry, verification, and report publish are allowed without sample events.
- **Payment:** When an order becomes paid, **no** sample records are created (no `ensure_samples_for_paid_order`).
- **Reports:** Report generation does **not** require sample timestamps/IDs; specimen/sample fields show **N/A** when no sample data exists.

### When `sample_workflow_enabled = True`

- Current behavior is preserved: sample collection/receiving is required where it is today; result entry remains gated by sample state as in the existing pipeline.

### Historical Data

- Turning the toggle **off** does **not** delete or corrupt existing sample data. Orders already in “sample pending/collected/received” continue to behave consistently; the toggle only affects what is **required going forward**.

## Frontend Rules

- **Menus:** When the toggle is **off**, “Samples” and “Sample Collection” / “Collection Worklist” are hidden from the sidebar.
- **Routes:** Direct navigation to `/dashboard/samples` or `/dashboard/collection` is **guarded**: user is redirected to dashboard with the message “Module disabled by lab settings.”
- **Result Entry:** When the toggle is off, Result Entry is available for paid/confirmed orders without visiting sample steps.

## API

- **GET** `/api/v1/core/settings/tenant/`  
  Returns tenant settings, including `sample_workflow_enabled`.
- **PATCH** `/api/v1/core/settings/tenant/`  
  Update tenant settings (e.g. `sample_workflow_enabled`). Admin-only. Sets `updated_by` to the current user.

## Edge Cases

- **Multi-tenant:** Each tenant has its own `TenantSettings`; toggling one tenant does not affect another.
- **No tenant:** If the user has no tenant, tenant settings endpoints return 404.
- **Report PDF when no samples:** Specimen/sample date and type fields show **N/A** when there are no samples for the order (e.g. workflow was off).

## How to Toggle

1. **UI:** Log in as Admin → **Settings** → **Lab Workflow** tab → check/uncheck “Enable sample workflow (collection/receiving)” → change is saved on toggle.
2. **API:** `PATCH /api/v1/core/settings/tenant/` with `{"sample_workflow_enabled": true}` or `false`.
3. **Django Admin:** `core.TenantSettings` → edit the tenant row and set **Sample workflow enabled**.

## Testing

- **Backend:** `apps.core.tests.test_sample_workflow_toggle`  
  Covers: tenant A ON (sample list 200), tenant B OFF (sample list 403), result worklist includes paid order when OFF, settings API returns flag, multi-tenant isolation, NEW → IN_PROCESS when OFF.
- **Frontend:** When toggle OFF, sample menu hidden and direct route to `/dashboard/samples` or `/dashboard/collection` is blocked and redirects with message; when ON, sample menu and routes behave as before.
