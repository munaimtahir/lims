"""Centralized receipt/payment state enforcement."""

from django.db import transaction

from apps.audit.utils import emit_audit_event
from apps.core.state import BadPayloadError, PermissionDeniedError

from .models import Payment


def transition_receipt_state(payment: Payment, actor, source: str = "api") -> Payment:
    """Receipt artifacts are implicitly RECORDED once created; emit audit event."""
    emit_audit_event(
        actor=actor,
        entity_type="receipt",
        entity_id=payment.pk,
        action="RECEIPT_RECORDED",
        before=None,
        after={"state": "RECORDED", "amount": str(payment.amount)},
        metadata={"order_id": payment.order_id},
        source=source,
    )
    return payment


def admin_override_receipt(payment: Payment, actor, updates: dict, reason: str, source: str = "api") -> Payment:
    """Explicit admin-only override method for immutable receipts."""
    if not getattr(actor, "is_admin", False):
        raise PermissionDeniedError("Only Admin may override a recorded receipt.")
    if not reason or not str(reason).strip():
        raise BadPayloadError("Override reason is required.")

    allowed_fields = {"transaction_id", "notes"}
    patch = {k: v for k, v in updates.items() if k in allowed_fields}
    if not patch:
        raise BadPayloadError("No supported override fields provided.")

    with transaction.atomic():
        locked = Payment.objects.select_for_update().get(pk=payment.pk)
        before = {k: getattr(locked, k) for k in patch.keys()}
        for field, value in patch.items():
            setattr(locked, field, value)
        locked.save(update_fields=list(patch.keys()))

        emit_audit_event(
            actor=actor,
            entity_type="receipt",
            entity_id=locked.pk,
            action="RECEIPT_OVERRIDE",
            before=before,
            after=patch,
            metadata={"reason": reason},
            source=source,
        )
        return locked
