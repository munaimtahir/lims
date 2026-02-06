# V2 Numbering System Implementation Summary

## Status: ✅ COMPLETE - Ready for Migration

This document summarizes the implementation of the V2 numbering system for the LIMS application.

---

## 📋 What Was Implemented

### 1. **Backend Models** ✅

#### New Models in `apps/core/models.py`:
- **CollectionCenter**: Manages registration/collection centers
  - Fields: `code` (00-99), `name`, `address`, `is_active`
  - Validation: 2-digit code format enforced
  
- **RegistrationCounter**: Atomic counter for Patient Registration Numbers
  - Scope: (YYMM, Center)
  - Unique constraint on (yymm, center)
  - Row-level locking for concurrency safety
  
- **LabDailyCounter**: Atomic counter for Lab Numbers
  - Scope: (Date, Center)
  - Unique constraint on (date, center)
  - Row-level locking for concurrency safety

#### Updated Models:

**Patient** (`apps/patients/models.py`):
- Added: `registration_number` (YYMM-CC-SSSS)
- Added: `registration_center` (FK to CollectionCenter)
- Added: `registration_datetime`
- Validator: `validate_registration_number`
- Auto-generation on save if not present
- Legacy fields (`mrn`, `patient_id`) maintained for compatibility

**Order** (`apps/orders/models.py`):
- Added: `lab_number` (MDD-XXX)
- Added: `lab_date`
- Added: `daily_serial` (001-999)
- Added: `collection_center` (FK to CollectionCenter)
- Validator: `validate_lab_number`
- Auto-generation on save if not present

---

### 2. **Number Generation Logic** ✅

File: `apps/core/numbering.py`

**`generate_registration_number(center, dt=None)`**:
- Format: `YYMM-CC-SSSS`
- Monthly reset per center
- Atomic with `SELECT ... FOR UPDATE`
- Example: `2602-00-0001`

**`generate_lab_number(center, dt=None)`**:
- Format: `MDD-XXX`
- Daily reset per center
- Atomic with `SELECT ... FOR UPDATE`
- Month letters: A=Jan, B=Feb, ..., L=Dec
- Example: `B07-001`
- Enforces 999 daily limit

---

### 3. **Validators** ✅

File: `apps/core/validators.py`

- **`validate_registration_number`**: Regex `^\d{4}-\d{2}-\d{4}$`
- **`validate_lab_number`**: Regex `^[A-L]\d{2}-\d{3}$`

---

### 4. **Database Migrations** ✅

Generated migrations:
- `apps/core/migrations/0006_*`: CollectionCenter, counters
- `apps/patients/migrations/0004_*`: registration fields
- `apps/orders/migrations/0005_*`: lab number fields

All migrations include:
- Unique constraints
- Indexes for performance
- Nullable fields for backward compatibility

---

### 5. **API Serializers** ✅

**Core** (`apps/core/serializers.py`):
- `CollectionCenterSerializer`
- `RegistrationCounterSerializer` (read-only)
- `LabDailyCounterSerializer` (read-only)

**Patients** (`apps/patients/serializers.py`):
- Added `registration_number`, `registration_center`, `registration_datetime`
- Read-only: `registration_number`, `registration_datetime`
- Writable: `registration_center` (for manual center selection)

**Orders** (`apps/orders/serializers.py`):
- Added `lab_number`, `lab_date`, `daily_serial`, `collection_center`
- All read-only (auto-generated)

---

### 6. **Admin Interface** ✅

File: `apps/core/admin.py`

- **CollectionCenterAdmin**: Full CRUD
- **RegistrationCounterAdmin**: Read-only (safety)
- **LabDailyCounterAdmin**: Read-only (safety)

Counter admins prevent manual creation/deletion to maintain integrity.

---

### 7. **Management Commands** ✅

**`python manage.py bootstrap_centers`**:
- Creates Head Office (code "00")
- Creates Test Center (code "10")
- Idempotent (safe to run multiple times)

---

### 8. **Tests** ✅

File: `apps/core/tests/test_numbering.py`

**Test Coverage**:
- ✅ Registration number format validation
- ✅ Registration number increments
- ✅ Monthly reset per center
- ✅ Center-scoped serials
- ✅ Lab number format validation
- ✅ Lab number month letter mapping
- ✅ Lab number increments
- ✅ Daily reset per center
- ✅ 999 daily limit enforcement
- ✅ Patient auto-generation
- ✅ Order auto-generation
- ✅ **Concurrency safety** (multi-threaded tests)
- ✅ Uniqueness constraints
- ✅ Center code validation

Run with: `pytest apps/core/tests/test_numbering.py -v`

---

### 9. **Documentation** ✅

**`DOCS/NUMBERING_SYSTEM.md`**:
- Complete specification
- Format examples
- Reset rules
- Concurrency guarantees
- Center code policy

**`CHANGELOG.md`**:
- V2.0.0 release entry
- Breaking changes notice
- Migration notes
- Technical details

**`config/numbering_constants.py`**:
- `NUMBERING_SYSTEM = "V2_LOCKED_2026_02"`

---

## 🚀 Deployment Steps

### 1. Run Migrations
```bash
cd lims-backend
source .venv/bin/activate
python manage.py migrate
```

### 2. Bootstrap Centers
```bash
python manage.py bootstrap_centers
```

### 3. Run Tests
```bash
pytest apps/core/tests/test_numbering.py -v
```

### 4. Verify
```bash
# Check centers exist
python manage.py shell
>>> from apps.core.models import CollectionCenter
>>> CollectionCenter.objects.all()
```

---

## 🔒 Safety Guarantees

### Concurrency
- ✅ Row-level locking (`SELECT ... FOR UPDATE`)
- ✅ No race conditions
- ✅ Tested with multi-threaded simulations

### Data Integrity
- ✅ Unique constraints on all number fields
- ✅ Validators prevent invalid formats
- ✅ Counters are read-only in admin
- ✅ Numbers are immutable after creation

### Backward Compatibility
- ✅ Legacy `mrn` and `patient_id` fields maintained
- ✅ New fields nullable for existing records
- ✅ Auto-fallback to Head Office (00) if center not specified

---

## 📊 Example Usage

### Creating a Patient
```python
from apps.patients.models import Patient
from apps.core.models import CollectionCenter

center = CollectionCenter.objects.get(code="00")
patient = Patient.objects.create(
    first_name="John",
    last_name="Doe",
    phone="03001234567",
    gender="Male",
    registration_center=center
)
# registration_number auto-generated: "2602-00-0001"
```

### Creating an Order
```python
from apps.orders.models import Order

order = Order.objects.create(
    patient=patient,
    collection_center=center
)
# lab_number auto-generated: "B07-001"
```

---

## 🎯 Next Steps (Frontend)

### Required Frontend Changes:

1. **Patient Registration Form**:
   - Add center selection dropdown
   - Display generated registration number
   - Make registration number read-only

2. **Order Creation Form**:
   - Add center selection dropdown
   - Display generated lab number
   - Make lab number read-only

3. **Patient List/Detail**:
   - Display `registration_number` prominently
   - Show registration center

4. **Order List/Worklist**:
   - Display `lab_number` prominently
   - Show collection center

5. **Tube Labels / Receipts**:
   - Print both:
     - Registration No: `2602-00-0001`
     - Lab No (Tube): `B07-001`

6. **API Integration**:
   - Update TypeScript interfaces to include new fields
   - Handle center selection in forms
   - Display read-only numbers in UI

---

## ✅ Checklist

- [x] Backend models created
- [x] Number generators implemented
- [x] Validators added
- [x] Migrations generated
- [x] Serializers updated
- [x] Admin interface configured
- [x] Management command created
- [x] Tests written and passing
- [x] Documentation complete
- [x] CHANGELOG updated
- [ ] Migrations applied (pending deployment)
- [ ] Centers bootstrapped (pending deployment)
- [ ] Frontend updated (pending)
- [ ] End-to-end testing (pending)

---

## 🔧 Troubleshooting

### Issue: "Daily serial limit reached"
**Solution**: This is expected behavior. Max 999 orders per day per center. If reached, either:
- Use a different center code
- Wait for next day (auto-reset)
- Contact admin to review business needs

### Issue: "Center 00 does not exist"
**Solution**: Run `python manage.py bootstrap_centers`

### Issue: "Duplicate registration number"
**Solution**: This should never happen due to row-level locking. If it does:
1. Check database transaction isolation level
2. Verify migrations applied correctly
3. Report as critical bug

---

## 📞 Support

For questions or issues:
1. Check `DOCS/NUMBERING_SYSTEM.md`
2. Review test cases in `apps/core/tests/test_numbering.py`
3. Consult CHANGELOG.md for migration notes
