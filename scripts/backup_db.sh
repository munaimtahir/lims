#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/srv/lims/backups"
mkdir -p "$BACKUP_DIR"

# shellcheck disable=SC2086
docker compose exec -T db pg_dump -U postgres -d ${POSTGRES_DB} \
  > "$BACKUP_DIR/lims_$(date +%F_%H-%M).sql"

echo "Backup completed."
