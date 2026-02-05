# Deployment Safety Guide

## Safe Commands (retain data)
- `make up`
- `make build`
- `make restart`
- `make stop`
- `make logs`
- `make down`
- `./scripts/check_db_volume.sh`
- `./scripts/backup_db.sh`

## Dangerous Commands (may delete data)
- `docker compose down -v`
- `make down_hard`

> WARNING: `docker compose down -v` deletes the PostgreSQL catalog volume.

## Recommended Workflow
1. `make build`
2. `make restart`
3. `make logs`
4. (Optional) `./scripts/check_db_volume.sh` before rebuilds
5. (Optional) `./scripts/backup_db.sh` before major redeploys (keep last 7 backups)

> Tip: export the production env before running make/scripts to avoid missing-variable errors:
> `set -a; . .env.production; set +a`

## Database Persistence
- PostgreSQL data stored in named volume `lims_pgdata`
- Normal rebuilds/restarts will not recreate or delete the database
