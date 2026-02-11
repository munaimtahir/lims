# Migration Notes

## Added Migration
- `lims-backend/apps/audit/migrations/0002_phase2_audit_fields.py`

## Change Summary
- Added canonical Phase 2 audit fields to `audit_logs`:
  - `created_at`, `actor`, `entity_type`, `entity_id`, `before`, `after`, `metadata`, `source`
- Included SQL backfill to map legacy fields:
  - `timestamp -> created_at`
  - `user -> actor`
  - `table_name -> entity_type`
  - `object_id -> entity_id`
  - `old_value -> before`
  - `new_value -> after`

## Runtime Validation
- Migration applied successfully in containerized backend (`docker compose run --rm backend python manage.py migrate`).
