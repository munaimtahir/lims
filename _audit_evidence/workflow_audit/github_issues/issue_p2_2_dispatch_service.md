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
