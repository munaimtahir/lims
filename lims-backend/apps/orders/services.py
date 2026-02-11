"""Centralized order/visit transitions."""

from django.db import transaction

from apps.audit.utils import emit_audit_event
from apps.core.state import InvalidTransitionError, PermissionDeniedError

from .models import Order


def transition_visit_state(order: Order, target_state: str, actor, source: str = "api") -> Order:
    """Transition order/visit status with validation, lock, and audit logging."""
    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        before_state = locked.status

        if before_state in {"PUBLISHED", "CANCELLED"}:
            raise InvalidTransitionError("Terminal order state cannot transition.")
        if before_state == target_state:
            return locked
        if not locked.can_transition_to(target_state):
            raise InvalidTransitionError(
                f"Invalid transition from {before_state} to {target_state}."
            )

        if target_state == "CANCELLED":
            if not (getattr(actor, "is_admin", False) or getattr(actor, "is_manager", False)):
                raise PermissionDeniedError("Only Admin/Manager may cancel orders.")
        elif target_state == "COLLECTED":
            if not (
                getattr(actor, "is_phlebotomist", False)
                or getattr(actor, "is_admin", False)
                or getattr(actor, "is_manager", False)
            ):
                raise PermissionDeniedError("Only Phlebotomist/Admin/Manager may collect.")
        elif target_state == "IN_PROCESS":
            if not (
                getattr(actor, "is_lab_technician", False)
                or getattr(actor, "is_admin", False)
                or getattr(actor, "is_manager", False)
            ):
                raise PermissionDeniedError("Only Lab Technician/Admin/Manager may start processing.")
        elif target_state in {"VERIFIED", "PUBLISHED"}:
            if not actor.has_perm("results.can_verify_results"):
                raise PermissionDeniedError("Verifier permission is required.")

        locked.status = target_state
        locked.ordered_by = actor
        locked.save(update_fields=["status", "ordered_by", "updated_at"])

        emit_audit_event(
            actor=actor,
            entity_type="order",
            entity_id=locked.pk,
            action="VISIT_STATE_CHANGED",
            before={"status": before_state},
            after={"status": target_state},
            metadata={"order_id": locked.order_id},
            source=source,
        )
        return locked
