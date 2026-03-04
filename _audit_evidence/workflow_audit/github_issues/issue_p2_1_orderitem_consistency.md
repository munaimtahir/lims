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
