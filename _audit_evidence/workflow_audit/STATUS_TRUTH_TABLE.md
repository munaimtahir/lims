# LIMS Status Truth Table - Consistency Audit

**Generated:** 2026-02-19  
**Purpose:** Document all status read/write locations and identify single source of truth

---

## Executive Summary

### Verdict: **PARTIALLY CENTRALIZED ⚠️**

The LIMS system has a **primary aggregation function** (`OrderWorkflowService._recalculate_order_status()`) that serves as the source of truth for Order status, but:

1. ✅ **Good:** Order status is computed from child entities (Samples, Results)
2. ⚠️ **Issue:** Two different write paths exist for Order status
3. ⚠️ **Issue:** OrderItem status may fall out of sync if not recalculated
4. ⚠️ **Issue:** Direct status assignments exist outside service layer
5. ✅ **Good:** TestResult and Report have dedicated transition services
6. ⚠️ **Issue:** Sample status has mixed write patterns

---

## 1. ORDER STATUS (MOST CRITICAL)

### 1.1 Status Definition

**File:** `/lims-backend/apps/orders/models.py:40-47, 69`

```python
STATUS_CHOICES = [
    ('NEW', 'New Order'),
    ('COLLECTED', 'Sample Collected'),
    ('IN_PROCESS', 'Processing'),
    ('VERIFIED', 'Verified'),
    ('PUBLISHED', 'Published'),
    ('CANCELLED', 'Cancelled'),
]
status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
```

**Valid Transitions:**
```
NEW → COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED (terminal)
 ↓        ↓            ↓           ↓
 └────────┴────────────┴───────────┴──→ CANCELLED (terminal)
```

---

### 1.2 Status READ Locations (Display/Filtering)

| Location | Type | Line | Purpose |
|----------|------|------|---------|
| `OrderListSerializer` | Serializer | 115 | List view display |
| `OrderSerializer` | Serializer | 170 | Detail view display |
| `OrderVerificationSerializer` | Serializer | 91 | Verification context |
| `OrderViewSet.destroy()` | View | 70 | Validate deletion (must be NEW) |
| `OrderViewSet.dispatch actions` | View | 82-92 | Dispatch status checks |
| `reports/views.py` | View | 30-31 | Report eligibility check |
| `reports/logic.py:collect_report_blockers()` | Logic | - | Validates order ready for report |
| `OrderWorkflowService._recalculate_order_status()` | Service | 184-186 | Reads sample statuses |
| **Frontend:** `OrdersPage.tsx` | UI | - | Status badge display |
| **Frontend:** `VerificationQueuePage.tsx` | UI | - | Filter by IN_PROCESS/VERIFIED |
| **Frontend:** `ReportsPage.tsx` | UI | - | Show orders with PUBLISHED status |

---

### 1.3 Status WRITE Locations ⚠️ (CRITICAL AUDIT POINT)

| Location | Type | File | Line | Write Method | Audit Event |
|----------|------|------|------|--------------|-------------|
| ⭐ **OrderWorkflowService._transition_order()** | Service | `apps/orders/workflow.py` | 243 | **CANONICAL** - validates & writes | ✅ Yes |
| ⭐ **OrderWorkflowService._recalculate_order_status()** | Service | `apps/orders/workflow.py` | 231-232 | **AGGREGATION** - computes from children | ✅ Yes |
| ⚠️ **transition_visit_state()** | Service | `apps/orders/services.py` | 51 | **ALTERNATIVE** - direct write | ✅ Yes |
| `Order.transition_to()` | Model Method | `apps/orders/models.py` | 335 | Validates transition before write | ✅ Yes |
| `OrderSerializer.update()` | Serializer | `apps/orders/serializers.py` | ~193 | Delegates to transition_visit_state | Via API |
| `OrderViewSet.perform_update()` | View | `apps/orders/views.py` | 93 | Calls transition_visit_state | Via API |
| Test code | Tests | Multiple | - | Direct assignments (test only) | No |

**⚠️ INCONSISTENCY IDENTIFIED:**
- **Two service functions write Order.status:**
  1. `OrderWorkflowService._transition_order()` (primary, used internally)
  2. `transition_visit_state()` (exposed via API, used by OrderViewSet)
- **Risk:** Inconsistent validation or audit trail if different paths used
- **Recommendation:** Consolidate into single entry point

---

### 1.4 Aggregation Logic ⭐ (SOURCE OF TRUTH)

**File:** `/lims-backend/apps/orders/workflow.py:174-232`  
**Function:** `OrderWorkflowService._recalculate_order_status(order)`

**Logic:**
```python
def _recalculate_order_status(order):
    """
    Compute order status from samples and results
    This is the SINGLE SOURCE OF TRUTH for order status
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        
        # Gather child entities
        samples = Sample.objects.filter(order_item__order=order)
        results = TestResult.objects.filter(order_item__order=order)
        required_results = results.filter(test_parameter__is_required=True)
        
        # Status decision tree
        all_samples_collected = samples.filter(
            status__in=[SampleStatus.COLLECTED, SampleStatus.RECEIVED]
        ).count() == samples.count()
        
        any_sample_received = samples.filter(
            status=SampleStatus.RECEIVED
        ).exists()
        
        any_result_entered = results.filter(
            status__gte=ResultStatus.ENTERED
        ).exists()
        
        all_required_verified = (
            required_results.count() > 0 and
            required_results.filter(
                status__gte=ResultStatus.VERIFIED
            ).count() == required_results.count()
        )
        
        # Transition logic
        if all_required_verified:
            new_status = 'VERIFIED'
        elif any_sample_received or any_result_entered:
            new_status = 'IN_PROCESS'
        elif all_samples_collected:
            new_status = 'COLLECTED'
        else:
            new_status = 'NEW'
        
        # Write status if changed
        if order.status != new_status:
            order.status = new_status
            order.save()
            emit_audit_event('ORDER_STATUS_CHANGED', ...)
```

**Trigger Points (where _recalculate_order_status is called):**
1. `OrderWorkflowService.receive_sample()` - line 41
2. `OrderWorkflowService.confirm_collection()` - line 70
3. `OrderWorkflowService.enter_result()` - line 96
4. `OrderWorkflowService.verify_result()` - line 124
5. `OrderWorkflowService.verify_order()` - line 149
6. `update_order_item_status()` - `/lims-backend/apps/results/services/transitions.py:74`

**✅ CONCLUSION:** Order status is derived, not directly set (except via explicit publish/cancel actions)

---

## 2. SAMPLE STATUS

### 2.1 Status Definition

**File:** `/lims-backend/apps/samples/models.py:10-19, 89-91`

```python
class SampleStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Collection'
    COLLECTED = 'COLLECTED', 'Collected'
    RECEIVED = 'RECEIVED', 'Received in Lab'
    REJECTED = 'REJECTED', 'Rejected'
    POSTPONED = 'POSTPONED', 'Postponed'

status = models.CharField(max_length=20, choices=SampleStatus.choices, default=SampleStatus.PENDING)
```

**Valid Transitions:**
```
PENDING → COLLECTED → RECEIVED (terminal)
   ↓          ↓
   ↓          └──→ REJECTED (terminal)
   └──→ POSTPONED → COLLECTED → RECEIVED
                        ↓
                        └──→ REJECTED
```

---

### 2.2 Status READ Locations

| Location | Type | Purpose |
|----------|------|---------|
| `SampleSerializer` | Serializer | Display sample status |
| `OrderWorkflowService._recalculate_order_status()` | Service | Check if COLLECTED/RECEIVED |
| `SampleViewSet.pending_collections()` | View | Filter PENDING/POSTPONED |
| **Frontend:** `CollectionWorklistPage.tsx` | UI | Display collection queue |
| **Frontend:** `SamplesPage.tsx` | UI | Sample status badges |

---

### 2.3 Status WRITE Locations

| Location | Type | File | Line | Write Method | Validation |
|----------|------|------|------|--------------|------------|
| **transition_sample_state()** | Service | `apps/samples/services.py` | 84-164 | **CANONICAL** | ✅ Validates transitions |
| `OrderWorkflowService.receive_sample()` | Service | `apps/orders/workflow.py` | 30 | Direct write | ⚠️ No service call |
| `OrderWorkflowService.confirm_collection()` | Service | `apps/orders/workflow.py` | 61 | Direct write | ⚠️ No service call |
| `SampleViewSet.perform_update()` | View | `apps/samples/views.py` | 85 | Calls transition_sample_state | ✅ Via service |
| `Sample.clean()` | Model | `apps/samples/models.py` | 117-133 | Validation only | ✅ Enforces immutability |

**⚠️ INCONSISTENCY IDENTIFIED:**
- `OrderWorkflowService` directly writes `sample.status = SampleStatus.RECEIVED` (line 30)
- Should call `transition_sample_state()` instead for consistency
- **Risk:** Missing audit events or validation checks

---

### 2.4 Validation Logic

**File:** `/lims-backend/apps/samples/models.py:117-133`

```python
def clean(self):
    # Enforce immutability: RECEIVED cannot be changed
    if self.pk and self.status == SampleStatus.RECEIVED:
        old_sample = Sample.objects.get(pk=self.pk)
        if old_sample.status == SampleStatus.RECEIVED and self.status != SampleStatus.RECEIVED:
            raise ValidationError("Cannot change status of a received sample")
    
    # Validate timestamps
    if self.status == SampleStatus.COLLECTED and not self.collected_at:
        raise ValidationError("collected_at required when status is COLLECTED")
    if self.status == SampleStatus.RECEIVED and not self.received_at:
        raise ValidationError("received_at required when status is RECEIVED")
```

---

## 3. TEST RESULT STATUS

### 3.1 Status Definition

**File:** `/lims-backend/apps/results/models.py:50-59`

```python
class ResultStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    READY = 'READY', 'Ready for Entry'
    ENTERED = 'ENTERED', 'Entered'
    VERIFIED = 'VERIFIED', 'Verified'
    FINAL = 'FINAL', 'Final'
    REJECTED = 'REJECTED', 'Rejected'  # Legacy

status = models.CharField(max_length=20, choices=ResultStatus.choices, default=ResultStatus.DRAFT)
```

**Valid Transitions:**
```
DRAFT → READY → ENTERED → VERIFIED → FINAL (immutable)
              ↑            ↓
              └────────────┘
              (reject/return)
```

**⚠️ FRONTEND MAPPING ISSUE:**  
**File:** `/lims-backend/apps/results/serializers.py:51-60`

```python
def get_status(self, obj):
    # Maps backend status to frontend values
    status_map = {
        'DRAFT': 'pending',
        'ENTERED': 'pending',  # ⚠️ Same as DRAFT
        'VERIFIED': 'verified',
        'FINAL': 'verified',  # ⚠️ Same as VERIFIED
    }
    return status_map.get(obj.status, obj.status)
```

**Risk:** Frontend cannot distinguish DRAFT vs ENTERED, or VERIFIED vs FINAL

---

### 3.2 Status READ Locations

| Location | Type | Purpose |
|----------|------|---------|
| `TestResultSerializer.get_status()` | Serializer | Maps to frontend values |
| `OrderWorkflowService._recalculate_order_status()` | Service | Check if VERIFIED |
| `ResultsViewSet.worklist()` | View | Filter DRAFT results |
| `ResultsViewSet.verification_queue()` | View | Filter ENTERED/VERIFIED results |
| **Frontend:** `ResultEntryWorklistPage.tsx` | UI | Display pending results |
| **Frontend:** `VerificationQueuePage.tsx` | UI | Display verification queue |

---

### 3.3 Status WRITE Locations

| Location | Type | File | Line | Write Method | Validation |
|----------|------|------|------|--------------|------------|
| ⭐ **transition_result_state()** | Service | `apps/results/services/transitions.py` | 103-141 | **CANONICAL** | ✅ Validates transitions |
| `OrderWorkflowService.enter_result()` | Service | `apps/orders/workflow.py` | 87 | Direct write | ⚠️ No service call |
| `OrderWorkflowService.verify_result()` | Service | `apps/orders/workflow.py` | 114 | Direct write | ⚠️ No service call |
| `OrderWorkflowService.publish_order()` | Service | `apps/orders/workflow.py` | 169 | Bulk update to FINAL | ⚠️ No service call |
| `TestResultViewSet.bulk_entry()` | View | `apps/results/views.py` | 541, 568 | Direct write | ⚠️ No service call |
| `TestResultViewSet.verify()` | View | `apps/results/views.py` | 701 | Calls transition_result_state | ✅ Via service |
| `TestResultViewSet.bulk_verify()` | View | `apps/results/views.py` | 749 | Calls transition_result_state | ✅ Via service |
| `TestResult.save()` | Model | `apps/results/models.py` | 98-127 | Validation | ✅ Enforces immutability |

**⚠️ INCONSISTENCY IDENTIFIED:**
- Multiple places write `result.status = ...` directly
- Should always call `transition_result_state()` for consistency
- **Risk:** Missing audit events or validation checks

---

### 3.4 Validation Logic

**File:** `/lims-backend/apps/results/models.py:98-127, 169-182`

```python
def save(self, *args, **kwargs):
    # Enforce immutability: FINAL cannot be changed
    if self.pk:
        old = TestResult.objects.get(pk=self.pk)
        if old.status == ResultStatus.FINAL:
            raise ValidationError("Cannot modify FINAL result")
    
    # Validate required fields
    if self.status in [ResultStatus.ENTERED, ResultStatus.VERIFIED, ResultStatus.FINAL]:
        if self.test_parameter.is_required and not self.result_value:
            raise ValidationError("Required parameter must have a value")
    
    super().save(*args, **kwargs)

def can_transition_to(self, new_status):
    valid_transitions = {
        ResultStatus.DRAFT: [ResultStatus.READY, ResultStatus.ENTERED],
        ResultStatus.READY: [ResultStatus.ENTERED],
        ResultStatus.ENTERED: [ResultStatus.VERIFIED],
        ResultStatus.VERIFIED: [ResultStatus.FINAL],
        ResultStatus.FINAL: [],  # Immutable
    }
    return new_status in valid_transitions.get(self.status, [])
```

---

## 4. ORDER ITEM STATUS

### 4.1 Status Definition

**File:** `/lims-backend/apps/orders/models.py:425-427`

```python
# OrderItem inherits Order.STATUS_CHOICES
status = models.CharField(
    max_length=20,
    choices=Order.STATUS_CHOICES,
    default='NEW'
)
```

---

### 4.2 Status READ Locations

| Location | Type | Purpose |
|----------|------|---------|
| `OrderItemSerializer` | Serializer | Display item status |
| `OrderItemVerificationSerializer` | Serializer | Verification context |

---

### 4.3 Status WRITE Locations (DERIVED FROM RESULTS)

| Location | Type | File | Line | Write Method |
|----------|------|------|------|--------------|
| ⭐ **update_order_item_status()** | Service | `apps/results/services/transitions.py` | 35-77 | **CANONICAL AGGREGATION** |
| Direct assignments | Service | Same | 62, 69 | Via aggregation logic |

**⚠️ CRITICAL:** OrderItem status is **DERIVED, NOT DIRECTLY SET**

---

### 4.4 Aggregation Logic ⭐ (SOURCE OF TRUTH)

**File:** `/lims-backend/apps/results/services/transitions.py:35-77`

```python
def update_order_item_status(order_item):
    """
    Compute OrderItem status from its TestResults
    """
    results = order_item.results.all()
    
    if not results.exists():
        order_item.status = 'NEW'
    elif all(r.status == ResultStatus.FINAL for r in results):
        order_item.status = 'VERIFIED'
    elif any(r.status in [ResultStatus.ENTERED, ResultStatus.VERIFIED, ResultStatus.FINAL] for r in results):
        order_item.status = 'IN_PROCESS'
    else:
        order_item.status = 'NEW'
    
    order_item.save()
    
    # Cascade to Order
    OrderWorkflowService._recalculate_order_status(order_item.order)
```

**Trigger Points:**
1. After result entry (bulk_entry)
2. After result verification
3. After result rejection

**✅ CONCLUSION:** OrderItem status is correctly derived from child results

---

## 5. REPORT STATUS

### 5.1 Status Definition

**File:** `/lims-backend/apps/reports/models.py:8-14, 51-55`

```python
class ReportStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    FINAL = 'FINAL', 'Final'
    AMENDED = 'AMENDED', 'Amended'
    CANCELLED = 'CANCELLED', 'Cancelled'

status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.DRAFT)
```

**Valid Transitions:**
```
DRAFT → FINAL → AMENDED (creates new report, marks original)
  ↓
  └──→ CANCELLED
```

---

### 5.2 Status READ Locations

| Location | Type | Purpose |
|----------|------|---------|
| `ReportSerializer` | Serializer | Display report status |
| `reports/views.py` | View | Check status before download |
| **Frontend:** `ReportsPage.tsx` | UI | Status badge display |

---

### 5.3 Status WRITE Locations

| Location | Type | File | Line | Write Method | Validation |
|----------|------|------|------|--------------|------------|
| ⭐ **transition_report_state()** | Service | `apps/reports/services.py` | 13-100+ | **CANONICAL** | ✅ Validates transitions |
| `ReportViewSet.generate()` | View | `apps/reports/views.py` | 388, 392 | Calls transition_report_state | ✅ Via service |
| `OrderViewSet.publish_report()` | View | `apps/orders/views.py` | 342 | Calls transition_report_state | ✅ Via service |
| `Report.create_amendment()` | Model | `apps/reports/models.py` | ~160 | Sets AMENDED via service | ✅ Via service |

**✅ GOOD:** All writes go through service function

---

### 5.4 Validation Logic

**File:** `/lims-backend/apps/reports/services.py`

```python
def transition_report_state(report, new_status, user):
    valid_transitions = {
        ReportStatus.DRAFT: [ReportStatus.FINAL, ReportStatus.CANCELLED],
        ReportStatus.FINAL: [ReportStatus.AMENDED],
        ReportStatus.AMENDED: [],  # Terminal
        ReportStatus.CANCELLED: []  # Terminal
    }
    
    if new_status not in valid_transitions.get(report.status, []):
        raise ValidationError(f"Cannot transition from {report.status} to {new_status}")
    
    report.status = new_status
    if new_status == ReportStatus.FINAL:
        report.verified_by = user
        report.verified_at = timezone.now()
    report.save()
    
    emit_audit_event('REPORT_STATUS_CHANGED', ...)
```

---

## 6. DISPATCH STATUS (Bonus)

### 6.1 Status Definition

**File:** `/lims-backend/apps/orders/models.py:462-465`

```python
STATUS_CHOICES = [
    ('CREATED', 'Created'),
    ('IN_TRANSIT', 'In Transit'),
    ('RECEIVED', 'Received'),
]
status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')
```

**Valid Transitions:**
```
CREATED → IN_TRANSIT → RECEIVED (terminal)
```

---

### 6.2 Status WRITE Locations

| Location | Type | Line | Write Method |
|----------|------|------|--------------|
| `OrderViewSet.send_dispatch()` | View | Sets to IN_TRANSIT | Direct write |
| `OrderViewSet.receive_dispatch()` | View | Sets to RECEIVED | Direct write |

**⚠️ ISSUE:** No dedicated service function for dispatch transitions

---

## 7. COMPARISON TABLE: EXPECTED VS ACTUAL

### 7.1 Order Status Truth Table

| Samples Status | Results Status | Expected Order Status | Actual Order Status | Match? |
|----------------|----------------|----------------------|---------------------|--------|
| All PENDING | All DRAFT | NEW | NEW | ✅ |
| All COLLECTED | All DRAFT | COLLECTED | COLLECTED | ✅ |
| Any RECEIVED | All DRAFT | IN_PROCESS | IN_PROCESS | ✅ |
| Any RECEIVED | Any ENTERED | IN_PROCESS | IN_PROCESS | ✅ |
| Any RECEIVED | All required VERIFIED | VERIFIED | VERIFIED | ✅ |
| Any RECEIVED | All required VERIFIED + report FINAL | PUBLISHED | PUBLISHED (manual) | ⚠️ Manual |

**⚠️ Note:** PUBLISHED requires explicit action, not auto-computed

---

### 7.2 OrderItem Status Truth Table

| Results Status | Expected OrderItem Status | Actual OrderItem Status | Match? |
|----------------|--------------------------|------------------------|--------|
| All DRAFT | NEW | NEW | ✅ |
| Any ENTERED | IN_PROCESS | IN_PROCESS | ✅ |
| All VERIFIED | VERIFIED | VERIFIED | ✅ |
| All FINAL | VERIFIED | VERIFIED | ✅ |

---

## 8. FINDINGS SUMMARY

### 8.1 Critical Issues ⚠️

1. **Dual Order Status Write Paths**
   - **Severity:** HIGH
   - **Location:** `OrderWorkflowService._transition_order()` vs `transition_visit_state()`
   - **Impact:** Inconsistent validation, audit trail
   - **Recommendation:** Consolidate into single entry point

2. **Direct Status Writes in Workflow Service**
   - **Severity:** MEDIUM
   - **Location:** `OrderWorkflowService.receive_sample()`, `enter_result()`, etc.
   - **Impact:** Bypasses validation and audit
   - **Recommendation:** Always call dedicated transition services

3. **Result Status Frontend Mapping Confusion**
   - **Severity:** MEDIUM
   - **Location:** `TestResultSerializer.get_status()`
   - **Impact:** Frontend cannot distinguish DRAFT vs ENTERED
   - **Recommendation:** Use full status values or add metadata

### 8.2 Minor Issues ⚠️

4. **OrderItem Status May Fall Out of Sync**
   - **Severity:** LOW
   - **Location:** `update_order_item_status()` called conditionally
   - **Impact:** Status may not reflect reality if recalc not triggered
   - **Recommendation:** Add scheduled consistency check job

5. **Missing Transaction Wrapping**
   - **Severity:** MEDIUM
   - **Location:** Some direct model saves
   - **Impact:** Race conditions in concurrent updates
   - **Recommendation:** Use `select_for_update()` consistently

6. **No Dedicated Dispatch Service**
   - **Severity:** LOW
   - **Location:** Dispatch status writes in OrderViewSet
   - **Impact:** No validation or audit trail
   - **Recommendation:** Create `transition_dispatch_state()` service

### 8.3 Good Practices ✅

1. ✅ Order status is derived from child entities
2. ✅ Report transitions use dedicated service
3. ✅ Sample and Result have validation in model clean/save
4. ✅ All status changes emit audit events (when using services)
5. ✅ Pessimistic locking used in critical paths

---

## 9. RECOMMENDED FIXES

### Priority 1: Consolidate Order Status Writes

**Current:**
```python
# TWO DIFFERENT PATHS
OrderWorkflowService._transition_order(order, 'PUBLISHED', user)
transition_visit_state(order, 'PUBLISHED', user)
```

**Proposed:**
```python
# SINGLE ENTRY POINT
from apps.orders.workflow import OrderWorkflowService
OrderWorkflowService.transition_order(order, 'PUBLISHED', user)
```

### Priority 2: Add Status Write Guards

**Current:**
```python
sample.status = SampleStatus.RECEIVED
sample.save()
```

**Proposed:**
```python
from apps.samples.services import transition_sample_state
transition_sample_state(sample, SampleStatus.RECEIVED, user)
```

### Priority 3: Fix Frontend Status Mapping

**Current:**
```python
'ENTERED': 'pending',  # Same as DRAFT
'FINAL': 'verified',   # Same as VERIFIED
```

**Proposed:**
```python
# Return full status or add metadata
return {
    'status': obj.status,
    'display_status': status_map.get(obj.status),
    'is_final': obj.status == 'FINAL'
}
```

---

## 10. FILE REFERENCE MAP

```
Core Models:
  Order:        apps/orders/models.py (40-335)
  OrderItem:    apps/orders/models.py (402-460)
  Sample:       apps/samples/models.py (22-186)
  TestResult:   apps/results/models.py (14-182)
  Report:       apps/reports/models.py (17-234)
  Dispatch:     apps/orders/models.py (462-541)

Workflow/Services (Write):
  OrderWorkflowService:         apps/orders/workflow.py (11-247) ⭐
  transition_visit_state:       apps/orders/services.py (14-65) ⚠️ Duplicate
  transition_sample_state:      apps/samples/services.py (84-164)
  transition_result_state:      apps/results/services/transitions.py (103-141)
  update_order_item_status:     apps/results/services/transitions.py (35-77)
  transition_report_state:      apps/reports/services.py (13-100+)

Serializers (Read):
  OrderSerializer:              apps/orders/serializers.py (137-336)
  TestResultSerializer:         apps/results/serializers.py (6-164)
  SampleSerializer:             apps/samples/serializers.py
  ReportSerializer:             apps/reports/serializers.py

Views (Entry Points):
  OrderViewSet:                 apps/orders/views.py (46-360)
  TestResultViewSet:            apps/results/views.py (160-768)
  SampleViewSet:                apps/samples/views.py (54-93)
  ReportViewSet:                apps/reports/views.py (320-404)
```

---

**END OF STATUS_TRUTH_TABLE.md**
