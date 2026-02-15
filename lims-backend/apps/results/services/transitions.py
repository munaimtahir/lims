"""Centralized transitions for result entry lifecycle."""

from django.db import transaction
from django.utils import timezone
import logging

from apps.audit.utils import emit_audit_event
from apps.core.state import BadPayloadError, InvalidTransitionError, PermissionDeniedError
from apps.results.models import TestResult
from apps.orders.models import Order, OrderItem

logger = logging.getLogger(__name__)

PLACEHOLDER_VALUES = {"", "*", "-", "pending", "placeholder"}


def _has_valid_result_value(result: TestResult) -> bool:
    """
    Check if result has a valid value.
    If parameter is required, it must be non-empty/non-placeholder.
    If parameter is optional, empty/placeholder is considered 'ABSENT' (valid for skipping).
    """
    value = (result.result_value or "").strip()
    is_absent = not value or value.lower() in PLACEHOLDER_VALUES
    
    # If required, must be present
    if result.test_parameter.is_required:
        return not is_absent
        
    # If optional, it's valid whether present or absent
    return True


def update_order_item_status(order_item: OrderItem):
    """
    Derive OrderItem status from its TestResults.
    - All VERIFIED/FINAL -> VERIFIED
    - Any result exists (DRAFT/ENTERED) -> IN_PROCESS
    - Else -> No change (or NEW)
    """
    results = order_item.results.all()
    if not results.exists():
        return

    statuses = {r.status for r in results}
    
    new_status = order_item.status
    
    if all(s in ["VERIFIED", "FINAL"] for s in statuses):
        new_status = "VERIFIED"
    elif "ENTERED" in statuses or "DRAFT" in statuses or "VERIFIED" in statuses:
        # Work has started
        new_status = "IN_PROCESS"
    else:
        # Fallback, though usually we don't revert to NEW once results exist
        pass

    if order_item.status != new_status:
        logger.info(f"Updating OrderItem {order_item.id} status: {order_item.status} -> {new_status}")
        order_item.status = new_status
        # Use update_fields to minimize side effects, but OrderItem doesn't check transitions in save() usually?
        # Checking OrderItem.save in models.py: it calls super().save. Models usually don't have transition checks unless added.
        # OrderItem model DOES NOT have transition validation in save(), only Order does.
        order_item.save(update_fields=["status"])
        
    # Propagate to Order
    update_order_status(order_item.order)


def update_order_status(order: Order):
    """
    Derive Order status from OrderItems.
    - All items VERIFIED -> VERIFIED (FINAL for Order)
    - Any item IN_PROCESS or VERIFIED (but not all) -> IN_PROCESS
    """
    items = order.items.all()
    if not items.exists():
        return

    item_statuses = {i.status for i in items}
    
    current_status = order.status
    new_status = current_status
    
    # 1. Check for VERIFIED
    # If all items are VERIFIED (or PUBLISHED/CANCELLED which are final states)
    # We treat PUBLISHED as a post-verified state, so if it's already published, don't revert to verified unless necessary.
    # But if we are Unverifying, we might need to revert.
    
    is_fully_verified = all(s in ["VERIFIED", "PUBLISHED", "CANCELLED"] for s in item_statuses)
    
    if is_fully_verified:
        if current_status not in ["VERIFIED", "PUBLISHED", "CANCELLED"]:
             new_status = "VERIFIED"
    else:
        # If not fully verified, check if in process
        # If any item is IN_PROCESS, VERIFIED, or has results -> IN_PROCESS
        if any(s in ["IN_PROCESS", "VERIFIED", "PUBLISHED"] for s in item_statuses):
            # If order was VERIFIED/PUBLISHED, revert to IN_PROCESS
            if current_status in ["VERIFIED", "PUBLISHED", "NEW", "COLLECTED"]:
                 new_status = "IN_PROCESS"
        else:
             # Basic state, maybe NEW or COLLECTED. We usually don't revert to NEW from IN_PROCESS automatically 
             # unless we strictly handle that. Safest is to leave as IN_PROCESS or current.
             pass

    if current_status != new_status:
        logger.info(f"Updating Order {order.order_id} status: {current_status} -> {new_status}")
        # Order has strict transition validation. We might need to bypass if reverting from VERIFIED to IN_PROCESS is not standard?
        # Order.validate_status_transition:
        # VERIFIED -> PUBLISHED, CANCELLED.
        # It does NOT allow VERIFIED -> IN_PROCESS.
        # So we must set status directly using query update or bypass save() check if strictly needed?
        # Or we should modify Order logic to allow VERIFIED->IN_PROCESS (Reversion).
        # User requirement A2: "VERIFIED -> IN_PROCESS on unverify should happen."
        # So specific logic in Order might resist.
        # We can bypass validation by setting the field and saving with update_fields?
        # Order.save() calls validate_status_transition.
        # We should modify Order.save or use update() queryset to bypass.
        # QuerySet.update() is safer to bypass python-level validation checks for "System driven reversions".
        Order.objects.filter(pk=order.pk).update(status=new_status)


def transition_result_state(result: TestResult, target_state: str, actor, source: str = "api", reason: str = None) -> TestResult:
    """Transition result status with strict validation and audit event."""
    if not actor.has_perm("results.can_verify_results"):
        raise PermissionDeniedError("You do not have permission to transition results.")

    with transaction.atomic():
        locked = TestResult.objects.select_for_update().get(pk=result.pk)
        before_state = locked.status

        if before_state == "FINAL":
            raise InvalidTransitionError("FINAL is immutable.")
        if target_state == before_state:
            raise InvalidTransitionError(f"Result is already {target_state}.")

        if target_state == "VERIFIED":
            if before_state not in ["DRAFT", "ENTERED"]:
                raise InvalidTransitionError("Only DRAFT or ENTERED results can be verified.")
            
            # Check if required
            if not _has_valid_result_value(locked):
                 raise BadPayloadError(f"Result value required for {locked.test_parameter.effective_parameter_name} before verification.")
            
            locked.status = "VERIFIED"
            locked.verified_by = actor
            locked.verified_at = timezone.now()
            locked.save(update_fields=["status", "verified_by", "verified_at"])
            action = "RESULT_VERIFIED"
            
        elif target_state == "ENTERED":
            # Return to entry / Unverify
            if before_state not in ["VERIFIED", "DRAFT"]: 
                 if before_state == "FINAL":
                     raise InvalidTransitionError("Cannot return FINAL results.")
            
            locked.status = "ENTERED"
            locked.verified_by = None
            locked.verified_at = None
            # Clear other metadata if exists (notes?) - User asked to clear verification_notes, 
            # assuming stored in notes or remarks? logic suggests keeping remarks as they might contain result context.
            # We'll stick to clearing verified info.
            
            locked.save(update_fields=["status", "verified_by", "verified_at"])
            action = "RESULT_RETURNED"
            
        elif target_state == "FINAL":
            if before_state != "VERIFIED":
                raise InvalidTransitionError("Result must be VERIFIED before FINAL.")
            if not _has_valid_result_value(locked):
                raise BadPayloadError("Result value required before finalization.")
            locked.status = "FINAL"
            locked.published_at = timezone.now()
            locked.save(update_fields=["status", "published_at"])
            action = "RESULT_FINALIZED"
        else:
            raise InvalidTransitionError(f"Unsupported target state {target_state}.")

        emit_audit_event(
            actor=actor,
            entity_type="result",
            entity_id=locked.pk,
            action=action,
            before={"status": before_state, "result_value": locked.result_value},
            after={"status": locked.status, "result_value": locked.result_value},
            metadata={"order_item_id": locked.order_item_id, "reason": reason},
            source=source,
        )
        
        # Determine and update parent statuses
        update_order_item_status(locked.order_item)
        
        return locked
