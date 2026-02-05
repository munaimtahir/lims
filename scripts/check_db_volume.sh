#!/usr/bin/env bash
set -euo pipefail

VOL="lims_pgdata"

if ! docker volume ls --format '{{.Name}}' | grep -qx "$VOL"; then
  echo "❌ ERROR: Expected DB volume '$VOL' not found."
  echo "Aborting to prevent accidental data loss."
  exit 1
fi

echo "✅ DB volume '$VOL' exists."
