"""Centralized transitions for result entry lifecycle."""

from django.db import transaction
from django.utils import timezone

from apps.audit.utils import emit_audit_event
from apps.core.state import BadPayloadError, InvalidTransitionError, PermissionDeniedError
from apps.results.models import TestResult

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
            if not _has_valid_result_value(locked):
                # Only block if it's required and missing. 
                # If optional and missing, we allow it (it's ABSENT).
                # But actually, if it is absent, do we mark it verified? 
                # Yes, 'verified absent' or just 'verified'.
                # The rule: "Verify must NOT be blocked by empty fields that are legitimately not entered (skipped)"
                if locked.test_parameter.is_required:
                     raise BadPayloadError(f"Result value required for {locked.test_parameter.effective_parameter_name} before verification.")
            
            locked.status = "VERIFIED"
            locked.verified_by = actor
            locked.verified_at = timezone.now()
            locked.save(update_fields=["status", "verified_by", "verified_at"])
            action = "RESULT_VERIFIED"
        elif target_state == "ENTERED":
            # Return to entry / Unverify
            if before_state not in ["VERIFIED", "DRAFT"]: # Can also return from DRAFT to reset? Or just VERIFIED to ENTERED.
                 # Usually used to Unverify.
                 if before_state == "FINAL":
                     raise InvalidTransitionError("Cannot return FINAL results.")
            
            locked.status = "ENTERED"
            locked.verified_by = None
            locked.verified_at = None
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
        return locked
