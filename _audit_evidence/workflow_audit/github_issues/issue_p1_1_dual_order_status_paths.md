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
