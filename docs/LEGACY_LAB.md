# Legacy Lab Reference

## Purpose

The `legacy_lab/lab-main/` directory contains the original LIMS implementation that has been preserved for reference purposes. This code is **NOT** part of the active application and should **NOT** be run independently.

## Why It's Kept

### 1. Data Migration Reference

The legacy repository contains:
- **Excel seed data files** in `backend/seed_data/`:
  - `AlShifa_LIMS_Master.xlsx` - Main test catalog with categories, tests, parameters, and reference ranges
  - Archive folder with historical data
- **Seed data management command** in `backend/users/management/commands/seed_data.py`
- Original data models that inform the modern implementation

### 2. Feature Reference

Useful for understanding:
- Original workflows and business logic
- Test catalog structure and organization
- User roles and permissions model
- Report formats and layouts
- Any domain-specific requirements

### 3. Historical Context

Provides context for:
- Design decisions in the new implementation
- Feature evolution
- Technical debt lessons learned

## What NOT to Do

❌ **DO NOT** run the legacy application:
- It may have conflicting Docker configurations
- Database schemas may clash
- Dependencies may conflict with the main app
- Port conflicts may occur

❌ **DO NOT** copy code directly:
- The legacy code may not follow modern best practices
- It may have security vulnerabilities
- Django and React ecosystems have evolved

❌ **DO NOT** use legacy migrations:
- The new app has its own migration strategy
- Schema differences exist

## How to Use It

### For Seed Data Migration

1. **Review the Excel files**:
   ```bash
   cd legacy_lab/lab-main/backend/seed_data/
   # Review AlShifa_LIMS_Master.xlsx
   ```

2. **Extract test catalog data**:
   - Categories, tests, panels
   - Parameters and reference ranges
   - Pricing information

3. **Create import commands** in the modern app:
   ```bash
   cd lims-backend/apps/laboratory/management/commands/
   # Create import_test_catalog.py based on legacy logic
   ```

### For Feature Reference

1. **Review models** for data structure:
   ```bash
   cd legacy_lab/lab-main/backend/
   # Review various app models
   ```

2. **Check workflows** for business logic:
   - Order creation flow
   - Sample collection process
   - Result entry and verification
   - Report generation

3. **Adapt, don't copy**:
   - Understand the intent
   - Implement using modern Django/React patterns
   - Follow the architecture in `ARCHITECTURE.md`

## Modern Implementation

All active code is in:
- **Backend**: `lims-backend/` - Django 5 + DRF
- **Frontend**: `frontend/` - React 18 + TypeScript + Vite

See the main [README.md](../README.md) for setup and usage instructions.

## Extracting Test Catalog

To migrate the test catalog from legacy Excel files to the modern system:

### Option 1: Manual Entry via Django Admin
1. Start the modern app
2. Access admin at `http://localhost:8000/admin/`
3. Create test categories, tests, parameters, and reference ranges

### Option 2: Create Import Command (Recommended)

```python
# lims-backend/apps/laboratory/management/commands/import_test_catalog.py
from django.core.management.base import BaseCommand
from apps.laboratory.models import TestCategory, Test, TestParameter
import pandas as pd

class Command(BaseCommand):
    help = 'Import test catalog from Excel'
    
    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str)
    
    def handle(self, *args, **options):
        # Read Excel file
        df = pd.read_excel(options['excel_file'])
        
        # Process and create test catalog entries
        # ... implementation details
        
        self.stdout.write(
            self.style.SUCCESS('Successfully imported test catalog')
        )
```

### Option 3: Database Dump and Transform
If the schemas are similar enough, you could:
1. Dump relevant tables from legacy DB
2. Transform data to match new schema
3. Load into modern DB

**Note**: Always backup before any data migration operations.

## Questions?

For questions about the legacy code or migration strategies:
- Review `DATA_MODEL.md` for the modern schema
- Check `IMPLEMENTATION_PLAN.md` for migration strategy
- Open an issue on GitHub

---

**Remember**: The legacy code is a reference, not a dependency. The modern LIMS in `lims-backend/` and `frontend/` is the production application.
