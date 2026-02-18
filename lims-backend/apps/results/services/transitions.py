"""Centralized transitions for result entry lifecycle."""

from django.db import transaction
from django.utils import timezone
import logging

from apps.audit.utils import emit_audit_event
from apps.core.state import BadPayloadError, InvalidTransitionError, PermissionDeniedError
from apps.results.models import TestResult
from apps.orders.models import Order, OrderItem
from apps.orders.workflow import OrderWorkflowService

logger = logging.getLogger(__name__)

PLACEHOLDER_VALUES = {"-", "pending", "placeholder"}


def _has_valid_result_value(result: TestResult) -> bool:
    """
    Check if result has a valid value.
    If parameter is required for verification, it must be non-empty/non-placeholder.
    If parameter is optional, empty/placeholder is considered 'ABSENT' (valid for skipping).
    """
    value = result.result_value
    is_absent = value is None or str(value).strip() == "" or str(value).lower() in PLACEHOLDER_VALUES
    
    # If required for verification, must be present
    if result.test_parameter.is_required_for_verification:
        return not is_absent
        
    # If optional, it's valid whether present or absent
    return True


def update_order_item_status(order_item: OrderItem, user=None):
    """
    Derive OrderItem status from its TestResults.
    
    Canonical Rules:
    - If ALL results are VERIFIED or FINAL: status -> VERIFIED.
    - If ANY result is DRAFT or ENTERED: status -> IN_PROCESS.
      - Actually, let's simplify: Any non-VERIFIED/FINAL result means IN_PROCESS.
    - If NO results entered yet: status -> NEW (or whatever original state).
    """
    with transaction.atomic():
        item = OrderItem.objects.select_for_update().get(pk=order_item.pk)
        
        results = item.results.all()
        if not results.exists():
            return

        statuses = {r.status for r in results}
        
        new_status = item.status
        
        is_fully_verified = all(s in ["VERIFIED", "FINAL"] for s in statuses)
        
        if is_fully_verified:
            if item.status != "VERIFIED":
                new_status = "VERIFIED"
        else:
            if any(s in ["DRAFT", "ENTERED", "VERIFIED", "FINAL"] for s in statuses):
                new_status = "IN_PROCESS"
            else:
                pass

        if item.status != new_status:
            logger.info(f"Updating OrderItem {item.id} status: {item.status} -> {new_status}")
            item.status = new_status
            item.save(update_fields=["status"])
        
        # Propagate to Order via Workflow Service
        if user:
            OrderWorkflowService._recalculate_order_status(item.order, user)
        else:
            # Fallback for system updates?
            pass


# Removed update_order_status as logic is now centralized in OrderWorkflowService


def transition_result_state(result: TestResult, target_state: str, actor, source: str = "api", reason: str = None) -> TestResult:
    """Transition result status with strict validation and audit event."""
    if not actor.has_perm("results.can_verify_results"):
        raise PermissionDeniedError("You do not have permission to transition results.")

    with transaction.atomic():
        # Lock the result row
        locked = TestResult.objects.select_for_update().get(pk=result.pk)
        before_state = locked.status

        # 1. Validation Logic
        if before_state == "FINAL":
            raise InvalidTransitionError("FINAL is immutable.")
        if target_state == before_state:
            # Idempotent success
            return locked

        action = "RESULT_UPDATED"
        changes = {}

        if target_state == "VERIFIED":
            if before_state not in ["DRAFT", "ENTERED"]:
                raise InvalidTransitionError("Only DRAFT or ENTERED results can be verified.")
            
            # Check required value
            if not _has_valid_result_value(locked):
                 raise BadPayloadError(f"Result value required for {locked.test_parameter.effective_parameter_name} before verification.")
            
            locked.status = "VERIFIED"
            locked.verified_by = actor
            locked.verified_at = timezone.now()
            action = "RESULT_VERIFIED"
            changes = {"status": "VERIFIED", "verified_by": str(actor), "verified_at": str(locked.verified_at)}
            
        elif target_state == "ENTERED":
            # Return to entry / Unverify
            if before_state not in ["VERIFIED", "DRAFT"]: 
                 if before_state == "FINAL":
                     raise InvalidTransitionError("Cannot return FINAL results.")
            
            locked.status = "ENTERED"
            # Clear verification metadata
            locked.verified_by = None
            locked.verified_at = None
            locked.verification_notes = ""
            
            action = "RESULT_RETURNED"
            changes = {"status": "ENTERED", "verified_by": None, "verified_at": None, "verification_notes": ""}
            
        elif target_state == "FINAL":
            if before_state != "VERIFIED":
                raise InvalidTransitionError("Result must be VERIFIED before FINAL.")
            if not _has_valid_result_value(locked):
                raise BadPayloadError("Result value required before finalization.")
                
            locked.status = "FINAL"
            locked.published_at = timezone.now()
            action = "RESULT_FINALIZED"
            changes = {"status": "FINAL", "published_at": str(locked.published_at)}
            
        else:
            raise InvalidTransitionError(f"Unsupported target state {target_state}.")

        locked.save()
        
        # 2. Audit Trail
        emit_audit_event(
            actor=actor,
            entity_type="result",
            entity_id=locked.pk,
            action=action,
            before={"status": before_state},
            after=changes,
            metadata={"order_item_id": locked.order_item_id, "reason": reason},
            source=source,
        )
        
        # 3. Propagate Status Changes
        # 3. Propagate Status Changes
        update_order_item_status(locked.order_item, user=actor)
        
        return locked
