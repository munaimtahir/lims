# LIMS E2E Workflow Verification Summary

**Date:** February 16, 2026  
**Status:** ✅ **PREREQUISITES CONFIGURED - READY FOR UI TESTING**

---

## ✅ VERIFIED CONFIGURATION

### Stack Status
```bash
docker compose ps
# All services: ✅ Healthy
```

### Albumin Test
- **Test Code:** `ALBUMIN`
- **Test ID:** 48
- **Price:** ✅ **Rs 500.00** (VERIFIED IN DATABASE)
- **Status:** Active
- **Parameter:** p89 (Albumin, g/dL)

**Verification:**
```bash
docker compose exec -T backend python manage.py shell -c "from apps.laboratory.models import Test; t = Test.objects.filter(test_code='ALBUMIN').first(); print(f'ID={t.test_id}, Price=Rs {t.price}, Active={t.is_active}')"
```

### Users
| Username | Password | Role | Status |
|----------|----------|------|--------|
| receptionist | recep123 | Receptionist | ✅ Active |
| labtech | labtech123 | Lab Technician | ✅ Active |
| pathologist | patho123 | Pathologist | ✅ Active |
| admin | admin123 | Admin | ✅ Active |

### Sample Workflow
- **Status:** ✅ **ENABLED** (True)
- **Impact:** Sample collection and receiving steps are REQUIRED before result entry

---

## 🎯 MANUAL UI TESTING CHECKLIST

### Step 1: Register Patient ✅
- [ ] Login: `receptionist` / `recep123`
- [ ] Navigate: Patient Registration
- [ ] Create patient:
  - Name: "Test Patient Albumin"
  - Age: 35
  - Gender: Male
  - Phone: 0300-0000000
- [ ] Verify: Patient created, MRN/ID shown
- [ ] **Record:** Patient ID = _______________

### Step 2: Create Order ✅
- [ ] From patient detail → Create Order
- [ ] Add test: Search "Albumin" or "ALBUMIN"
- [ ] **VERIFY:** Only Albumin test added (no other tests)
- [ ] **VERIFY:** Total shows **Rs 500.00** (exactly)
- [ ] Save/Generate receipt
- [ ] **Record:** Order ID = _______________, Receipt # = _______________

### Step 3: Sample Collection ✅
- [ ] Login: `phlebotomist` / `phleb123` (or receptionist if has permission)
- [ ] Navigate: Sample Collection Queue
- [ ] Find order from Step 2
- [ ] Mark sample as collected
- [ ] Enter collector info if required
- [ ] **Verify:** Status changes to "Collected"

### Step 4: Sample Receiving ✅
- [ ] Navigate: Sample Receiving
- [ ] Find order from Step 2
- [ ] Receive sample
- [ ] **Verify:** Status changes to "Received"

### Step 5: Result Entry ✅
- [ ] Login: `labtech` / `labtech123`
- [ ] Navigate: Result Entry Queue
- [ ] Find order from Step 2
- [ ] Open order/test
- [ ] Enter result: **Albumin = 4.5**
- [ ] **Verify:** Unit: g/dL
- [ ] Save results
- [ ] **Verify:** Status = ENTERED
- [ ] **Verify:** Result persists after refresh

### Step 6: Verification ✅
- [ ] Login: `pathologist` / `patho123`
- [ ] Navigate: Verification Queue
- [ ] Find order from Step 2
- [ ] Review: Albumin = 4.5
- [ ] Verify/Approve results
- [ ] **Verify:** Status changes to VERIFIED

### Step 7: Publish PDF ✅
- [ ] From verification page → Publish/Generate Report
- [ ] **Verify:** PDF downloads/opens (HTTP 200)
- [ ] **VERIFY PDF CONTENT:**
  - [ ] Patient name: "Test Patient Albumin"
  - [ ] Test: Albumin
  - [ ] **Result: 4.5** ✅
  - [ ] Unit: g/dL
- [ ] **Record:** PDF URL = _______________

---

## 🔍 QUICK VERIFICATION COMMANDS

### Check Albumin Test
```bash
docker compose exec -T backend python manage.py shell -c "from apps.laboratory.models import Test; t = Test.objects.filter(test_code='ALBUMIN').first(); print(f'✅ Albumin: ID={t.test_id}, Price=Rs {t.price}, Active={t.is_active}')"
```

### Check Users
```bash
docker compose exec -T backend python manage.py shell -c "from apps.accounts.models import User; users = ['receptionist', 'labtech', 'pathologist']; [print(f'✅ {u}: {User.objects.filter(username=u).first().is_active if User.objects.filter(username=u).first() else \"NOT FOUND\"}') for u in users]"
```

### Check Sample Workflow
```bash
docker compose exec -T backend python manage.py shell -c "from apps.core.models import TenantSettings; ts = TenantSettings.objects.first(); print(f'Sample workflow: {\"ENABLED\" if ts and ts.sample_workflow_enabled else \"DISABLED\"}')"
```

### Check Recent Orders
```bash
docker compose exec -T backend python manage.py shell -c "from apps.orders.models import Order; from apps.laboratory.models import Test; albumin = Test.objects.filter(test_code='ALBUMIN').first(); orders = Order.objects.filter(order_items__test=albumin).order_by('-created_at')[:5]; [print(f'Order {o.order_id}: Total=Rs {o.total_amount}, Status={o.status}') for o in orders]"
```

---

## 📊 EXPECTED RESULTS

| Step | Expected Outcome | Verification |
|------|------------------|--------------|
| Registration | Patient created with MRN | Patient appears in list |
| Order Creation | Order with Albumin, Total = Rs 500 | Receipt shows Rs 500 |
| Sample Collection | Status: Collected | Order visible in collection queue |
| Sample Receiving | Status: Received | Order visible in receiving queue |
| Result Entry | Albumin = 4.5, Status: ENTERED | Result persists, status correct |
| Verification | Status: VERIFIED | Order moves to verified state |
| PDF Report | PDF contains Albumin = 4.5 | Download successful, content verified |

---

## 🐛 TROUBLESHOOTING

### If Order Total ≠ Rs 500
```bash
# Check test price
docker compose exec -T backend python manage.py shell -c "from apps.laboratory.models import Test; t = Test.objects.filter(test_code='ALBUMIN').first(); print(f'Price: Rs {t.price}')"

# Update if needed
docker compose exec -T backend python manage.py shell -c "from apps.laboratory.models import Test; from decimal import Decimal; Test.objects.filter(test_code='ALBUMIN').update(price=Decimal('500.00')); print('Updated')"
```

### If Sample Workflow Not Showing
- Check tenant settings: Sample workflow should be ENABLED
- Verify user has phlebotomist permissions
- Check if menus are hidden (feature flag)

### If Result Entry Fails
- Verify parameter mapping exists:
```bash
docker compose exec -T backend python manage.py shell -c "from apps.laboratory.models import Test, TestParameter; t = Test.objects.filter(test_code='ALBUMIN').first(); mappings = TestParameter.objects.filter(test=t); print(f'Mappings: {mappings.count()}'); [print(f'  - {m.parameter.parameter_name}') for m in mappings]"
```

### If PDF Generation Fails
- Check Celery worker is running: `docker compose ps celery`
- Check backend logs: `docker compose logs backend --tail 50`
- Verify report endpoint: Check browser DevTools Network tab

---

## 📝 TEST EXECUTION LOG TEMPLATE

```
Date: _______________
Tester: _______________

Step 1 - Registration:
  Patient ID: _______________
  Status: [ ] PASS [ ] FAIL
  Notes: _______________

Step 2 - Order Creation:
  Order ID: _______________
  Receipt #: _______________
  Total Amount: Rs _______________
  Status: [ ] PASS [ ] FAIL
  Notes: _______________

Step 3 - Sample Collection:
  Status: [ ] PASS [ ] FAIL [ ] N/A (workflow disabled)
  Notes: _______________

Step 4 - Sample Receiving:
  Status: [ ] PASS [ ] FAIL [ ] N/A (workflow disabled)
  Notes: _______________

Step 5 - Result Entry:
  Result Value: _______________
  Status: [ ] PASS [ ] FAIL
  Notes: _______________

Step 6 - Verification:
  Status: [ ] PASS [ ] FAIL
  Notes: _______________

Step 7 - PDF Report:
  PDF URL: _______________
  Albumin Value in PDF: _______________
  Status: [ ] PASS [ ] FAIL
  Notes: _______________

Overall Status: [ ] ALL PASS [ ] SOME FAIL [ ] BLOCKED
```

---

**Next Steps:** Execute manual UI testing using the checklist above and document results.
