#!/bin/bash
#
# LIMS Catalog Pipeline Runbook
# 
# This script automates the complete catalog stabilization pipeline:
# 1. Bring up Docker stack
# 2. Run migrations
# 3. Verify schema
# 4. Convert Excel to import format
# 5. Dry-run import
# 6. Import catalog
# 7. Ensure minimum parameters
# 8. Generate status report
#
# Usage:
#   ./scripts/catalog/run_catalog_pipeline.sh [--skip-docker] [--excel-file <path>]
#

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXCEL_AUTHORITATIVE="${1:-LIMS_TestCatalog_MVP_FINAL (1).xlsx}"
EXCEL_CONVERTED="$REPO_ROOT/LIMS_TestCatalog_IMPORT_READY.xlsx"
SKIP_DOCKER=false
MANAGE_PY="$REPO_ROOT/lims-backend/manage.py"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --excel-file)
            EXCEL_AUTHORITATIVE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found"
        exit 1
    fi
    log_info "Python3: $(python3 --version)"
    
    # Check Django manage.py
    if [ ! -f "$MANAGE_PY" ]; then
        log_error "manage.py not found at $MANAGE_PY"
        exit 1
    fi
    log_info "Django manage.py: Found"
    
    # Check Excel file
    if [ ! -f "$EXCEL_AUTHORITATIVE" ]; then
        log_error "Authoritative Excel file not found: $EXCEL_AUTHORITATIVE"
        exit 1
    fi
    log_info "Authoritative Excel: $EXCEL_AUTHORITATIVE"
    
    # Check Docker (if not skipping)
    if [ "$SKIP_DOCKER" = false ]; then
        if ! command -v docker &> /dev/null; then
            log_warn "Docker not found, will skip Docker steps"
            SKIP_DOCKER=true
        else
            log_info "Docker: $(docker --version)"
        fi
    fi
}

# Phase 0: Bring up Docker stack
phase0_docker_setup() {
    if [ "$SKIP_DOCKER" = true ]; then
        log_warn "Skipping Docker setup"
        return 0
    fi
    
    log_section "Phase 0: Docker Stack Setup"
    
    cd "$REPO_ROOT"
    
    log_info "Starting database and redis..."
    docker compose up -d db redis || {
        log_error "Failed to start Docker services"
        return 1
    }
    
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check if services are running
    if docker compose ps | grep -q "lims_db.*Up"; then
        log_info "✓ Database is running"
    else
        log_error "Database is not running"
        return 1
    fi
    
    if docker compose ps | grep -q "lims_redis.*Up"; then
        log_info "✓ Redis is running"
    else
        log_error "Redis is not running"
        return 1
    fi
}

# Phase 0: Run Django checks and migrations
phase0_django_setup() {
    log_section "Phase 0: Django Setup & Migrations"
    
    cd "$REPO_ROOT/lims-backend"
    
    # Set Django settings
    export DJANGO_SETTINGS_MODULE=config.settings.development
    
    log_info "Running Django system check..."
    python3 manage.py check || {
        log_error "Django system check failed"
        return 1
    }
    
    log_info "Showing migration status..."
    python3 manage.py showmigrations laboratory || true
    
    log_info "Running migrations..."
    python3 manage.py migrate || {
        log_error "Migrations failed"
        return 1
    }
    
    log_info "✓ Migrations completed"
}

# Phase 1: Schema verification
phase1_schema_verification() {
    log_section "Phase 1: Schema Verification"
    
    cd "$REPO_ROOT/lims-backend"
    export DJANGO_SETTINGS_MODULE=config.settings.development
    
    log_info "Running schema verification..."
    if python3 manage.py verify_catalog_schema; then
        log_info "✓ Schema verification passed"
        return 0
    else
        log_error "Schema verification failed"
        log_warn "You may need to run schema repair migrations"
        return 1
    fi
}

# Phase 2: Excel conversion
phase2_excel_conversion() {
    log_section "Phase 2: Excel Contract Conversion"
    
    cd "$REPO_ROOT"
    
    log_info "Converting Excel to import format..."
    python3 scripts/catalog/convert_excel_to_import_contract.py \
        "$EXCEL_AUTHORITATIVE" \
        "$EXCEL_CONVERTED" || {
        log_error "Excel conversion failed"
        return 1
    }
    
    log_info "✓ Excel conversion completed"
    log_info "Output file: $EXCEL_CONVERTED"
}

# Phase 4: Import (with dry-run first)
phase4_import() {
    log_section "Phase 4: Catalog Import"
    
    cd "$REPO_ROOT/lims-backend"
    export DJANGO_SETTINGS_MODULE=config.settings.development
    
    # Dry-run first
    log_info "Running dry-run import..."
    if python3 manage.py catalog_import_excel --path "$EXCEL_CONVERTED" --dry-run; then
        log_info "✓ Dry-run passed"
    else
        log_error "Dry-run failed - aborting import"
        return 1
    fi
    
    # Actual import
    log_info "Running actual import..."
    if python3 manage.py catalog_import_excel --path "$EXCEL_CONVERTED"; then
        log_info "✓ Import completed successfully"
        return 0
    else
        log_error "Import failed"
        return 1
    fi
}

# Phase 3: Ensure minimum parameters
phase3_ensure_minimum_parameters() {
    log_section "Phase 3: Ensure Minimum Parameters"
    
    cd "$REPO_ROOT/lims-backend"
    export DJANGO_SETTINGS_MODULE=config.settings.development
    
    log_info "Ensuring all tests have minimum parameters..."
    if python3 manage.py catalog_ensure_minimum_parameters; then
        log_info "✓ Minimum parameters ensured"
        return 0
    else
        log_error "Failed to ensure minimum parameters"
        return 1
    fi
}

# Phase 5: Generate status report
phase5_status_report() {
    log_section "Phase 5: Status Report"
    
    cd "$REPO_ROOT/lims-backend"
    export DJANGO_SETTINGS_MODULE=config.settings.development
    
    log_info "Generating status report..."
    
    python3 << 'PYTHON_EOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.laboratory.models import Test, Parameter, TestParameter, ReferenceRange
from django.db import connection

print("\n" + "="*60)
print("CATALOG STATUS REPORT")
print("="*60)

# Counts
test_count = Test.objects.count()
active_test_count = Test.objects.filter(is_active=True).count()
param_count = Parameter.objects.count()
active_param_count = Parameter.objects.filter(active=True).count()
mapping_count = TestParameter.objects.count()
range_count = ReferenceRange.objects.count()

print(f"\nTests:")
print(f"  Total: {test_count}")
print(f"  Active: {active_test_count}")

print(f"\nParameters:")
print(f"  Total: {param_count}")
print(f"  Active: {active_param_count}")

print(f"\nMappings:")
print(f"  Total: {mapping_count}")

print(f"\nReference Ranges:")
print(f"  Total: {range_count}")

# Tests without mappings
tests_with_mappings = Test.objects.filter(
    is_active=True,
    test_parameters__isnull=False
).distinct().count()

tests_without_mappings = active_test_count - tests_with_mappings

print(f"\nTest Coverage:")
print(f"  Tests with mappings: {tests_with_mappings}")
print(f"  Tests without mappings: {tests_without_mappings}")

if tests_without_mappings == 0:
    print("\n✓ All active tests have parameter mappings")
else:
    print(f"\n⚠ {tests_without_mappings} active tests still lack mappings")

# Schema check
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'parameters' AND column_name = 'parameter_id'
    """)
    has_param_id = cursor.fetchone() is not None

print(f"\nSchema:")
print(f"  parameter_id field exists: {'✓' if has_param_id else '✗'}")

print("\n" + "="*60)
PYTHON_EOF

    log_info "✓ Status report generated"
}

# Main execution
main() {
    log_section "LIMS Catalog Stabilization Pipeline"
    log_info "Starting pipeline execution..."
    log_info "Repository: $REPO_ROOT"
    log_info "Authoritative Excel: $EXCEL_AUTHORITATIVE"
    
    # Run phases
    check_prerequisites || exit 1
    
    phase0_docker_setup || {
        log_warn "Docker setup failed, continuing without Docker..."
        SKIP_DOCKER=true
    }
    
    phase0_django_setup || exit 1
    phase1_schema_verification || exit 1
    phase2_excel_conversion || exit 1
    phase4_import || exit 1
    phase3_ensure_minimum_parameters || exit 1
    phase5_status_report || exit 1
    
    log_section "Pipeline Complete"
    log_info "✓ All phases completed successfully"
    log_info "Converted Excel: $EXCEL_CONVERTED"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Review the status report above"
    log_info "  2. Test order/result entry in the UI"
    log_info "  3. Verify reports are generating correctly"
}

# Run main
main "$@"
