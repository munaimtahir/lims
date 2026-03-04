# GitHub Issues to Create - Workflow Audit Findings

**Generated:** 2026-02-19  
**Source:** LIMS Workflow Audit  
**Priority Levels:** P1 (Critical) and P2 (High-Priority)

---

## Priority 1 Issues (Critical - 3 issues)

### Issue 1: Consolidate Dual Order Status Write Paths

**Title:** `[P1 Critical] Consolidate Dual Order Status Write Paths`

**Labels:** `bug`, `priority:critical`, `workflow`, `backend`

**Description:**

```markdown
## Problem

**Severity:** CRITICAL  
**Source:** Workflow Audit - Finding 1.1  
**Risk:** Data inconsistency, missing audit trail, validation bypass

Two different service functions write `Order.status`, creating risk of inconsistent behavior:
1. `OrderWorkflowService._transition_order()` (internal use)
2. `transition_visit_state()` (API-exposed)

## Evidence

```
File: apps/orders/workflow.py:243
  OrderWorkflowService._transition_order(order, new_status, user)

File: apps/orders/services.py:51
  transition_visit_state(order, new_status, user)

File: apps/orders/views.py:93
  OrderViewSet.perform_update() calls transition_visit_state()
```

## Impact

- Different validation rules may apply
- Audit events may differ
- Code maintainability suffers
- Risk of using wrong function in new code

## Root Cause

- Historical refactoring left both functions in place
- No clear documentation on which to use

## Proposed Fix

**Step 1:** Consolidate into single entry point

Create canonical method in `apps/orders/workflow.py`:
```python
class OrderWorkflowService:
    @staticmethod
    def transition_order(order, new_status, user, reason=None):
        """
        CANONICAL method to transition order status
        All order status writes MUST use this method
        """
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)
            
            # Validate transition
            if not order.can_transition_to(new_status):
                raise ValidationError(
                    f"Cannot transition order from {order.status} to {new_status}"
                )
            
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Emit audit event
            emit_audit_event(
                event_type='ORDER_STATUS_CHANGED',
                entity_type='order',
                entity_id=order.id,
                user=user,
                tenant=order.tenant,
                details={
                    'old_status': old_status,
                    'new_status': new_status,
                    'reason': reason
                }
            )
            
            return order
```

**Step 2:** Deprecate `transition_visit_state()` in `apps/orders/services.py`

**Step 3:** Update all callers in `apps/orders/views.py`

## Verification Checklist

- [ ] Grep for `transition_visit_state` calls
- [ ] Update all references
- [ ] Run integration tests
- [ ] Verify audit events still emitted

## Effort Estimate

**4 hours**  
**Files to Change:** 3 files (workflow.py, services.py, views.py)

## References

- Full audit: `_audit_evidence/workflow_audit/FINDINGS_AND_FIX_PLAN.md`
- Workflow call graph: `_audit_evidence/workflow_audit/WORKFLOW_CALL_GRAPH.md`
- Related issues: #[issue for Finding 1.2]
```

---

### Issue 2: Replace Direct Status Writes with Service Calls

**Title:** `[P1 Critical] Replace Direct Status Writes with Service Calls`

**Labels:** `bug`, `priority:critical`, `workflow`, `backend`, `audit-trail`

**Description:**

```markdown
## Problem

**Severity:** CRITICAL  
**Source:** Workflow Audit - Finding 1.2  
**Risk:** Missing audit trail, validation bypass, inconsistent behavior

Multiple locations directly assign status fields without calling transition services, bypassing validation and audit trail generation.

## Evidence

Direct status writes found in:

```python
# File: apps/orders/workflow.py:30
sample.status = SampleStatus.RECEIVED
sample.save()

# File: apps/orders/workflow.py:87
result.status = ResultStatus.ENTERED
result.save()

# File: apps/orders/workflow.py:114
result.status = ResultStatus.VERIFIED
result.save()

# File: apps/results/views.py:541, 568
result.status = ResultStatus.ENTERED
result.save()
```

## Impact

- Audit events may not be emitted
- Validation rules may be skipped
- Timestamps (verified_at, entered_at) may not be set
- Inconsistent with other code paths
- Potential data integrity issues

## Proposed Fix

**Step 1:** Add status write guards in all service methods

Example for sample status in `apps/orders/workflow.py`:
```python
def receive_sample(self, sample, user):
    # OLD:
    # sample.status = SampleStatus.RECEIVED
    # sample.save()
    
    # NEW:
    from apps.samples.services import transition_sample_state
    transition_sample_state(
        sample=sample,
        new_status=SampleStatus.RECEIVED,
        user=user
    )
    
    # Recalculate order status
    self._recalculate_order_status(sample.order_item.order)
```

**Step 2:** Update result entry in `apps/results/views.py`

Replace direct assignments with:
```python
from apps.results.services.transitions import transition_result_state
transition_result_state(
    result=result,
    new_status=ResultStatus.ENTERED,
    user=request.user
)
```

**Step 3:** Add linting rule to catch direct status writes

Create custom linter rule or pre-commit hook to flag `.status = ` patterns outside of transition services.

## Files Affected

- `apps/orders/workflow.py` (3 locations)
- `apps/results/views.py` (2 locations)
- `apps/samples/services.py` (validation)
- `apps/results/services/transitions.py` (validation)

## Verification Checklist

- [ ] Grep for `.status = ` in codebase
- [ ] Update all direct assignments
- [ ] Run full test suite
- [ ] Verify audit events emitted for all transitions
- [ ] Check that timestamps are properly set
- [ ] Validate transaction rollback on validation errors

## Effort Estimate

**6 hours**  
**Files to Change:** 5 files (workflow.py, views.py × 2, transitions.py)

## References

- Full audit: `_audit_evidence/workflow_audit/FINDINGS_AND_FIX_PLAN.md`
- Status truth table: `_audit_evidence/workflow_audit/STATUS_TRUTH_TABLE.md`
- Related issues: #[issue for Finding 1.1]
```

---

### Issue 3: Fix Frontend Status Mapping to Preserve Granularity

**Title:** `[P1 Critical] Fix Frontend Status Mapping to Preserve Granularity`

**Labels:** `bug`, `priority:high`, `frontend`, `backend`, `serializer`, `ui/ux`

**Description:**

```markdown
## Problem

**Severity:** MEDIUM-HIGH  
**Source:** Workflow Audit - Finding 1.3  
**Risk:** Frontend cannot distinguish critical status differences

The `TestResultSerializer.get_status()` maps backend statuses to simplified frontend values, losing important distinctions:
- `DRAFT` → `"pending"` 
- `ENTERED` → `"pending"` ⚠️ **Same as DRAFT**
- `VERIFIED` → `"verified"`
- `FINAL` → `"verified"` ⚠️ **Same as VERIFIED**

## Evidence

```python
# File: apps/results/serializers.py:51-60
def get_status(self, obj):
    status_map = {
        'DRAFT': 'pending',
        'ENTERED': 'pending',  # ⚠️ Loss of information
        'VERIFIED': 'verified',
        'FINAL': 'verified',   # ⚠️ Loss of information
    }
    return status_map.get(obj.status, obj.status)
```

## Impact

- Frontend cannot distinguish entered-but-unverified results from drafts
- Frontend cannot show "finalized" badge for immutable FINAL results
- UI may mislead users about actual workflow state
- Users cannot see if results are still editable or locked

## Proposed Fix

**Option A (Recommended):** Return full status with metadata

Update `apps/results/serializers.py`:
```python
class TestResultSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    is_draft = serializers.SerializerMethodField()
    is_entered = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    is_final = serializers.SerializerMethodField()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_is_draft(self, obj):
        return obj.status == ResultStatus.DRAFT
    
    def get_is_entered(self, obj):
        return obj.status == ResultStatus.ENTERED
    
    def get_is_verified(self, obj):
        return obj.status == ResultStatus.VERIFIED
    
    def get_is_final(self, obj):
        return obj.status == ResultStatus.FINAL
    
    class Meta:
        fields = [..., 'status', 'status_display', 'is_draft', 'is_entered', 'is_verified', 'is_final']
```

**Option B:** Use full status values in frontend

Remove status mapping entirely:
```python
status = serializers.CharField(source='status')
```

**Frontend Update (for Option B):**

Update `frontend/src/pages/results/ResultsPage.tsx`:
```typescript
const getStatusBadge = (status: string) => {
  switch (status) {
    case 'DRAFT':
      return <Badge color="gray">Draft</Badge>;
    case 'ENTERED':
      return <Badge color="blue">Entered</Badge>;
    case 'VERIFIED':
      return <Badge color="green">Verified</Badge>;
    case 'FINAL':
      return <Badge color="purple">Final</Badge>;
    default:
      return <Badge>{status}</Badge>;
  }
};
```

## Verification Checklist

- [ ] Update serializer (choose Option A or B)
- [ ] Update frontend status display logic
- [ ] Test all status badges render correctly
- [ ] Verify no regressions in worklist/queue filtering
- [ ] Test result entry workflow still works
- [ ] Test verification workflow still works
- [ ] Check that FINAL results show as immutable

## Effort Estimate

**3 hours**  
**Files to Change:** 2 files (serializers.py, frontend components)

## References

- Full audit: `_audit_evidence/workflow_audit/FINDINGS_AND_FIX_PLAN.md`
- Status truth table: `_audit_evidence/workflow_audit/STATUS_TRUTH_TABLE.md`
- Workflow call graph: `_audit_evidence/workflow_audit/WORKFLOW_CALL_GRAPH.md`
```

---

## Priority 2 Issues (High-Priority - 2 issues)

### Issue 4: Add OrderItem Status Consistency Check

**Title:** `[P2 High] Add OrderItem Status Consistency Check and Auto-Sync`

**Labels:** `enhancement`, `priority:high`, `workflow`, `backend`, `data-integrity`

**Description:**

```markdown
## Problem

**Severity:** MEDIUM  
**Source:** Workflow Audit - Finding 2.1  
**Risk:** Display inconsistencies, incorrect workflow state

`update_order_item_status()` is called after result transitions, but:
- Not called after all bulk operations
- No scheduled consistency check to catch drift
- Manual status edits could bypass recalculation
- Status may not reflect reality if recalc not triggered

## Evidence

```python
# File: apps/results/services/transitions.py:35-77
# Only called explicitly after certain operations
def update_order_item_status(order_item):
    # Derives status from results
    # BUT: only called when explicitly invoked
```

## Impact

- OrderItem status may not match actual result states
- Users may see incorrect status in UI
- Workflow logic may make wrong decisions based on stale status
- Data integrity concerns

## Proposed Fix

**Step 1:** Add consistency check management command

Create `apps/orders/management/commands/check_status_consistency.py`:
```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        from apps.results.services.transitions import update_order_item_status
        from apps.orders.workflow import OrderWorkflowService
        
        # Check OrderItems
        inconsistent_items = []
        for item in OrderItem.objects.all():
            old_status = item.status
            update_order_item_status(item)
            item.refresh_from_db()
            if old_status != item.status:
                inconsistent_items.append((item.id, old_status, item.status))
        
        # Check Orders
        inconsistent_orders = []
        for order in Order.objects.all():
            old_status = order.status
            OrderWorkflowService._recalculate_order_status(order)
            order.refresh_from_db()
            if old_status != order.status:
                inconsistent_orders.append((order.id, old_status, order.status))
        
        self.stdout.write(
            f"Found {len(inconsistent_items)} inconsistent items, "
            f"{len(inconsistent_orders)} inconsistent orders"
        )
```

**Step 2:** Add post-save signal for automatic sync

Update `apps/orders/apps.py`:
```python
class OrdersConfig(AppConfig):
    def ready(self):
        from django.db.models.signals import post_save
        from .signals import recalculate_on_result_save
        post_save.connect(recalculate_on_result_save, sender=TestResult)
```

**Step 3:** Schedule periodic consistency check

Add to cron or Celery beat:
```bash
0 2 * * * python manage.py check_status_consistency
```

## Verification Checklist

- [ ] Run consistency check on production data
- [ ] Fix any inconsistencies found
- [ ] Schedule daily consistency check cron job
- [ ] Add monitoring/alerting for inconsistencies
- [ ] Document the consistency check process

## Effort Estimate

**4 hours**  
**Files to Change:** 3 files (new management command, apps.py, signals.py)

## References

- Full audit: `_audit_evidence/workflow_audit/FINDINGS_AND_FIX_PLAN.md`
- Status truth table: `_audit_evidence/workflow_audit/STATUS_TRUTH_TABLE.md`
```

---

### Issue 5: Create Dispatch Status Transition Service

**Title:** `[P2 High] Create Dispatch Status Transition Service for Audit Trail`

**Labels:** `enhancement`, `priority:high`, `workflow`, `backend`, `audit-trail`

**Description:**

```markdown
## Problem

**Severity:** MEDIUM  
**Source:** Workflow Audit - Finding 2.2  
**Risk:** No validation, no audit trail for dispatch transitions

Dispatch status changes happen directly in `OrderViewSet` without a dedicated service:
- No validation of transitions
- No audit trail
- No timestamp management
- Inconsistent with other entity status management

## Evidence

```python
# File: apps/orders/views.py
# No transition service, direct writes
dispatch.status = 'IN_TRANSIT'
dispatch.save()
```

## Impact

- Dispatch status changes are not audited
- No validation of valid state transitions
- Timestamps (sent_at, received_at) may not be properly managed
- Inconsistent with other workflow entity patterns

## Proposed Fix

**Step 1:** Create dispatch transition service

Add to `apps/orders/services.py` (or new file):
```python
def transition_dispatch_state(dispatch, new_status, user):
    valid_transitions = {
        'CREATED': ['IN_TRANSIT'],
        'IN_TRANSIT': ['RECEIVED'],
        'RECEIVED': [],  # Terminal
    }
    
    if new_status not in valid_transitions.get(dispatch.status, []):
        raise ValidationError(
            f"Cannot transition dispatch from {dispatch.status} to {new_status}"
        )
    
    with transaction.atomic():
        dispatch = Dispatch.objects.select_for_update().get(pk=dispatch.pk)
        old_status = dispatch.status
        dispatch.status = new_status
        
        if new_status == 'IN_TRANSIT':
            dispatch.sent_at = timezone.now()
            dispatch.sent_by = user
        elif new_status == 'RECEIVED':
            dispatch.received_at = timezone.now()
            dispatch.received_by = user
        
        dispatch.save()
        
        emit_audit_event(
            event_type='DISPATCH_STATUS_CHANGED',
            entity_type='dispatch',
            entity_id=dispatch.id,
            user=user,
            tenant=dispatch.tenant,
            details={'old_status': old_status, 'new_status': new_status}
        )
```

**Step 2:** Update viewset actions

Update `apps/orders/views.py`:
```python
@action(detail=True, methods=['post'])
def send_dispatch(self, request, pk=None):
    dispatch = self.get_object()
    transition_dispatch_state(dispatch, 'IN_TRANSIT', request.user)
    return Response({'status': 'success'})

@action(detail=True, methods=['post'])
def receive_dispatch(self, request, pk=None):
    dispatch = self.get_object()
    transition_dispatch_state(dispatch, 'RECEIVED', request.user)
    return Response({'status': 'success'})
```

## Verification Checklist

- [ ] Test dispatch send/receive flow
- [ ] Verify audit events emitted
- [ ] Validate transition rules enforced
- [ ] Check timestamps are set correctly
- [ ] Test invalid transitions are rejected

## Effort Estimate

**3 hours**  
**Files to Change:** 2 files (services.py, views.py)

## References

- Full audit: `_audit_evidence/workflow_audit/FINDINGS_AND_FIX_PLAN.md`
- Status truth table: `_audit_evidence/workflow_audit/STATUS_TRUTH_TABLE.md`
```

---

## Summary

**Total Issues:** 5 (3 Priority 1 + 2 Priority 2)

**Priority 1 (Critical):**
1. Consolidate Dual Order Status Write Paths - 4 hours
2. Replace Direct Status Writes with Service Calls - 6 hours
3. Fix Frontend Status Mapping to Preserve Granularity - 3 hours

**Total P1 Effort:** 13 hours

**Priority 2 (High):**
4. Add OrderItem Status Consistency Check and Auto-Sync - 4 hours
5. Create Dispatch Status Transition Service - 3 hours

**Total P2 Effort:** 7 hours

**Grand Total Effort:** 20 hours (~2.5 dev days)

---

## How to Create These Issues

### Option 1: Manual Creation via GitHub UI

1. Go to https://github.com/munaimtahir/lims/issues/new
2. Copy the title and description from each issue above
3. Add the specified labels
4. Submit the issue

### Option 2: Using GitHub CLI

```bash
# Issue 1
gh issue create \
  --title "[P1 Critical] Consolidate Dual Order Status Write Paths" \
  --label "bug,priority:critical,workflow,backend" \
  --body-file issue1_body.md

# Issue 2
gh issue create \
  --title "[P1 Critical] Replace Direct Status Writes with Service Calls" \
  --label "bug,priority:critical,workflow,backend,audit-trail" \
  --body-file issue2_body.md

# ... and so on for each issue
```

### Option 3: Using GitHub API

See example script in this directory for automated issue creation.

---

**Generated from:** LIMS Workflow Audit  
**Date:** 2026-02-19  
**Audit Evidence:** `_audit_evidence/workflow_audit/`
