"""Centralized report artifact transitions."""

from django.core.files.base import ContentFile
from django.db import transaction

from apps.audit.utils import emit_audit_event
from apps.core.state import BadPayloadError, InvalidTransitionError, PermissionDeniedError

from .models import Report, ReportStatus
from .utils import generate_pdf_report


def transition_report_state(report: Report, target_state: str, actor, source: str = "api", **kwargs) -> Report:
    """Transition report status and enforce immutability rules."""
    if target_state not in {ReportStatus.FINAL, ReportStatus.AMENDED, ReportStatus.CANCELLED}:
        raise InvalidTransitionError(f"Unsupported target state {target_state}.")

    with transaction.atomic():
        locked = Report.objects.select_for_update().select_related("order").get(pk=report.pk)
        before_state = (locked.status or "").upper()

        if before_state in {ReportStatus.FINAL, ReportStatus.AMENDED} and target_state != ReportStatus.AMENDED:
            raise InvalidTransitionError("Final/amended reports are immutable.")

        if target_state == ReportStatus.CANCELLED:
            if before_state != ReportStatus.DRAFT:
                raise InvalidTransitionError("Only draft reports can be cancelled.")
            if not (getattr(actor, "is_admin", False) or getattr(actor, "is_manager", False)):
                raise PermissionDeniedError("Only Admin/Manager may cancel draft reports.")
            locked.status = ReportStatus.CANCELLED
            locked.save(update_fields=["status"])
            emit_audit_event(
                actor=actor,
                entity_type="report",
                entity_id=locked.pk,
                action="REPORT_CANCELLED",
                before={"status": before_state},
                after={"status": locked.status},
                source=source,
            )
            return locked

        if target_state == ReportStatus.FINAL:
            if not (
                actor.has_perm("results.can_verify_results")
                or getattr(actor, "is_pathologist", False)
                or getattr(actor, "is_admin", False)
                or getattr(actor, "is_manager", False)
            ):
                raise PermissionDeniedError("Verifier permission is required.")
            if before_state != ReportStatus.DRAFT:
                raise InvalidTransitionError("Only draft reports can be finalized in-place.")
            locked.status = ReportStatus.FINAL
            locked.generated_by = actor
            if not locked.report_file:
                pdf_content = generate_pdf_report(locked.order_id)
                filename = f"Report_{locked.order.order_id}_{locked.order_id}.pdf"
                locked.report_file.save(filename, ContentFile(pdf_content))
            locked.save()
            emit_audit_event(
                actor=actor,
                entity_type="report",
                entity_id=locked.pk,
                action="REPORT_FINALIZED",
                before={"status": before_state},
                after={"status": locked.status},
                source=source,
            )
            return locked

        # target_state == AMENDED (explicitly creates a new report record)
        if not (getattr(actor, "is_pathologist", False) or getattr(actor, "is_admin", False)):
            raise PermissionDeniedError("Only Pathologist/Admin may amend a report.")
        if before_state != ReportStatus.FINAL:
            raise InvalidTransitionError("Only FINAL reports may be amended.")
        reason = kwargs.get("reason")
        if not reason or not str(reason).strip():
            raise BadPayloadError("Amendment reason is required.")

        pdf_content = generate_pdf_report(
            locked.order.id,
            lab_name=kwargs.get("lab_name"),
            lab_address=kwargs.get("lab_address"),
            lab_phone=kwargs.get("lab_phone"),
            lab_email=kwargs.get("lab_email"),
        )
        amended = locked.create_amendment(reason, actor)
        filename = f"Report_Amended_{amended.report_number}.pdf"
        amended.report_file.save(filename, ContentFile(pdf_content))
        amended.status = ReportStatus.AMENDED
        amended.save()

        emit_audit_event(
            actor=actor,
            entity_type="report",
            entity_id=amended.pk,
            action="REPORT_AMENDED",
            before={"status": before_state, "amended_from": locked.pk},
            after={"status": amended.status, "amended_from": locked.pk},
            metadata={"reason": reason},
            source=source,
        )
        return amended
