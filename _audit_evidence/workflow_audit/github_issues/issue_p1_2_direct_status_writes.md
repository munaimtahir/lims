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
