# Multi-Branch Foundations (Phase 1)

## ID Formats
- **MRN (patient)**: `TENANTCODE-YY-######` (tenant-wide sequence, annual reset). Existing MRNs stay unchanged.
- **Order ID**: `BC-YYMMDD-####` where `BC` is Branch.code (`00`–`99`), sequence per `(tenant, branch, date)`.
- **Sample ID**: `{order_id}-S{n}` (n = sample index within order). Barcode mirrors `sample_id` for compatibility.

## Models & Constraints
- `Tenant`: logical lab owner; `code` stable, unique.
- `Branch`: FK to tenant, 2-digit `code`, capability `COLLECT_ONLY` / `COLLECT_AND_PROCESS` / `HQ_PROCESSING`, `is_hq` auto when code `00`. Unique `(tenant, code)`.
- `UserBranchMembership`: user, branch, role, `is_active`, unique `(user, branch)`.
- `OrderIdSequence`: atomic per `(tenant, branch, date)` for order IDs.
- `TenantMrnSequence`: atomic per `(tenant, YY)` for MRNs.
- Added `tenant_id` to Patient, Order, Sample; `collection_branch` / `processing_branch` on Order; branch markers on Sample.

## RBAC Rules
- All querysets scoped to `request.user.tenant`.
- Branch users only see orders/samples from their active branches; Admin/superuser bypass.
- Capability guard: `COLLECT_ONLY` branches cannot enter/modify results or verification actions (blocked in results viewset).

## Search Behavior
- Patient lookup supports `mrn`, `cnic`, `mobile`, `name`; mobile returns list (not auto-select) with MRN, name, age/DOB, gender, last_visit_date, last_branch_code.

## Admin/Seed
- Admin screens for Tenant, Branch, sequences.
- Management command: `python manage.py seed_branches --tenant=<CODE> [--include-samples]` creates HQ `00` (HQ_PROCESSING) and optional sample branches.

## Capability Notes
- Phase-1: collection-only branches create orders/collections; processing/verification restricted.
- Foundation supports future processing branches by toggling `capability_mode`.

## TODO (Phase 1 follow-ups)
- [ ] Wire capability checks into all result/report pathways (verification, publishing).
- [ ] Extend patient/order serializers to expose branch codes where needed by UI.
- [ ] Add HQ/branch selection to auth/session so mobile/desktop clients pass branch context.
- [ ] Migrate legacy data to set tenant/branch defaults safely in production.
