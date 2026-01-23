#!/bin/bash
set -e

echo "=== LIMS Catalog Stabilization Runbook ==="

# Check service status
if ! docker ps | grep -q lims_backend; then
    echo "LIMS backend container is not running. Please start docker compose."
    exit 1
fi

echo "1. Verifying Database Schema..."
docker exec lims_backend python manage.py verify_catalog_schema

echo "2. Converting Excel Contract..."
# Assuming source_catalog.xlsx is at /app/source_catalog.xlsx (copied manually or via pipeline setup)
# Ensure script is present
docker cp scripts/catalog/convert_excel_to_import_contract.py lims_backend:/app/scripts/catalog/
# Copy auxiliary CSV if present
if [ -f parameters.csv ]; then
    docker cp parameters.csv lims_backend:/app/parameters.csv
fi

docker exec lims_backend python -u scripts/catalog/convert_excel_to_import_contract.py source_catalog.xlsx derived_catalog.xlsx parameters.csv

echo "3. Importing Catalog (Dry Run)..."
docker exec lims_backend python manage.py catalog_import_excel --path derived_catalog.xlsx --dry-run

echo "4. Importing Catalog (Real)..."
docker exec lims_backend python manage.py catalog_import_excel --path derived_catalog.xlsx

echo "5. Ensuring Minimum Parameters..."
docker exec lims_backend python manage.py catalog_ensure_minimum_parameters

echo "6. Running Smoke Test..."
docker exec lims_backend python manage.py smoke_test_catalog

echo "=== PIPELINE COMPLETE ==="
