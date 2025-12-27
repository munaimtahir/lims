# Migration Documentation

## orders/0002_alter_order_status_alter_orderitem_status.py

### Purpose
Adds CANCELLED status to Order and OrderItem models to support order cancellation feature.

### Changes
- Alters `Order.status` field to include CANCELLED in choices
- Alters `OrderItem.status` field to include CANCELLED in choices

### Idempotency
✅ **This migration is idempotent.**

Django's `AlterField` operation is inherently idempotent:
- Running the migration multiple times will not cause errors
- The operation checks current field definition before applying changes
- If the field already has the correct definition, no changes are made
- No data migration or transformation occurs

### Testing
```bash
# Test forward migration
python manage.py migrate orders 0002

# Test idempotency (run again)
python manage.py migrate orders 0002
# Should complete without errors

# Test rollback
python manage.py migrate orders 0001

# Re-apply
python manage.py migrate orders 0002
```

### Rollback Safety
✅ **Rollback is safe if no CANCELLED orders exist.**

If orders with CANCELLED status exist in database:
- Django will raise IntegrityError on rollback
- This is expected behavior (data integrity protection)
- Before rolling back, ensure no orders are in CANCELLED status
- Or write a data migration to handle status transition

### Production Deployment Notes
1. Migration adds a new choice value - safe to deploy
2. No existing data is modified
3. No indexes or constraints are added/removed
4. Migration runs in milliseconds (ALTER TABLE operation)
5. No downtime required for this migration

### Related Features
- Order cancellation endpoint: `POST /api/orders/{id}/cancel/`
- Only affects orders with status=NEW
- Prevents cancellation after sample collection
- Requires Admin or Reception role

### Status Flow
```
NEW ─┬→ COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED
     └→ CANCELLED (terminal state)
```

### Database Impact
- **Storage**: No additional storage required (VARCHAR field unchanged)
- **Indexes**: No index changes
- **Performance**: No performance impact
- **Backwards Compatibility**: New status value doesn't affect existing queries
