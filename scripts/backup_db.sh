#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/srv/lims/backups"
mkdir -p "$BACKUP_DIR"

DB_NAME=${POSTGRES_DB:-lims_db}

# shellcheck disable=SC2086
docker compose exec -T db pg_dump -U postgres -d "$DB_NAME" \
  > "$BACKUP_DIR/lims_$(date +%F_%H-%M).sql"

echo "Backup completed to $BACKUP_DIR"
