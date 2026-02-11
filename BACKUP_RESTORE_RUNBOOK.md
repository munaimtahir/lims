# Backup & Restore Runbook

## Scope
This runbook covers backup and restore for:
- PostgreSQL database
- Uploaded files (`media`)
- Backup metadata and config snapshot

## Storage Locations
- Local backups in containers: `/backups/lims`
- Host bind mount: `./backups`
- Backup archive format: `.zip` containing `db.dump`, `files.tar.gz`, `meta.json`, optional `checksums.sha256`

## Prerequisites
- Backend and Celery services running
- `postgresql-client`, `zip`, and `tar` available in backend image
- For offsite S3: `BACKUP_OFFSITE_PROVIDER=s3` and valid S3 credentials/env

## Automatic Schedule
- Celery beat runs scheduled backup task daily at 02:00 server time.
- Retention policy:
  - Daily: 7 buckets
  - Weekly: 4 buckets
  - Monthly: 6 buckets

## Manual Backup (UI)
1. Go to `Dashboard -> Backups`.
2. Click `Create Backup Now` or `Create + Push Offsite`.
3. Track status in history table.

## Manual Backup (CLI)
```bash
cd /app
python manage.py run_scheduled_backups
```

## Import Backup (UI)
1. Go to `Dashboard -> Backups`.
2. Upload `.zip` in `Import Backup` section.
3. Verify imported artifact appears with `IMPORTED` type.

## Download Backup (UI)
1. In backup row, click `Download`.
2. Verify archive includes expected files.

## Restore Backup (UI)
1. Open Backups page and click `Restore` for selected backup.
2. Confirm by typing exact value: `RESTORE <backup_id>`.
3. Wait for async restore completion and review logs.

## Emergency Restore (CLI)
From backend container:
```bash
python manage.py shell -c "from apps.backups.services import perform_restore_job; perform_restore_job('<backup_uuid>')"
```

## Offsite Push (UI)
1. Configure S3 env values.
2. Use `Test Offsite Connection`.
3. Click `Push` on a backup row.

## Troubleshooting
- `pg_dump`/`pg_restore` not found:
  - Rebuild backend image to include `postgresql-client`.
- Backup failed with permissions:
  - Ensure write access to `/backups` mount.
- Offsite push failed:
  - Validate `S3_BUCKET`, keys, endpoint, and region.
- Restore failed during media extraction:
  - Check free disk and file permissions for `MEDIA_ROOT`.

## Safety Notes
- Restore is destructive for current DB/media state.
- Always restore in staging first when possible.
- Keep backup files outside public web roots.
