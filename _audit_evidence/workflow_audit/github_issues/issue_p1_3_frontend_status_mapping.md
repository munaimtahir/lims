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
