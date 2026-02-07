from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.orders.models import Order


class ReportStatus(models.TextChoices):
    """Report status choices."""

    DRAFT = "DRAFT", "Draft"
    FINAL = "FINAL", "Final"
    AMENDED = "AMENDED", "Amended"
    CANCELLED = "CANCELLED", "Cancelled"


class Report(models.Model):
    """
    Represents a generated PDF report for an order.

    Attributes:
        order (Order): The order this report is for.
        report_file (FileField): The path to the generated PDF file.
        report_number (str): Unique report number for tracking.
        status (str): Report status (DRAFT, FINAL, AMENDED, CANCELLED).
        template_name (str): Template used for generation.
        generated_at (datetime): The timestamp of when the report was generated.
        generated_by (User): The user who generated the report.
        is_final (bool): Whether this is the final report for the order (deprecated, use status).
        pathologist_signature (FileField, optional): Digital signature of the pathologist.
        technician_signature (FileField, optional): Digital signature of the lab technician.
        verified_by (User, optional): The pathologist who verified the report.
        verified_at (datetime, optional): When the report was verified.
        amended_from (Report, optional): Original report if this is an amendment.
        amendment_reason (str, optional): Reason for amendment.
        delivered_at (datetime, optional): When the report was delivered to patient.
        delivered_by (User, optional): User who delivered the report.
        delivery_method (str, optional): Method of delivery (email, print, etc.).
        reprint_count (int): Number of times this report has been reprinted.
        last_reprinted_at (datetime, optional): Last reprint timestamp.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="reports")
    report_file = models.FileField(upload_to="reports/%Y/%m/%d/")
    report_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique report number (e.g., RPT-YYYYMMDD-NNNN)",
    )
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
    )
    template_name = models.CharField(
        max_length=100,
        default="default",
        help_text="Template used for report generation",
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports_generated",
    )

    is_final = models.BooleanField(
        default=True,
        help_text="Deprecated: Use status field instead",
    )

    # Digital signatures
    pathologist_signature = models.FileField(
        upload_to="signatures/pathologist/%Y/%m/%d/", blank=True, null=True
    )
    technician_signature = models.FileField(
        upload_to="signatures/technician/%Y/%m/%d/", blank=True, null=True
    )

    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports_verified",
    )
    verified_at = models.DateTimeField(blank=True, null=True)

    # Amendment tracking
    amended_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="amendments",
        help_text="Original report if this is an amendment",
    )
    amendment_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for creating this amendment",
    )

    # Delivery tracking
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_delivered",
    )
    delivery_method = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ("email", "Email"),
            ("print", "Printed"),
            ("download", "Downloaded"),
            ("sms", "SMS"),
        ],
    )

    # Reprint tracking
    reprint_count = models.IntegerField(default=0)
    last_reprinted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["report_number"]),
            models.Index(fields=["generated_at"]),
        ]

    def __str__(self):
        """
        Return a string representation of the report.

        Returns:
            str: A string in the format "Report for order_id at generated_at".
        """
        return f"Report {self.report_number} for {self.order.order_id} at {self.generated_at}"

    def save(self, *args, **kwargs):
        """Override save to generate report number if not provided."""
        if not self.report_number:
            self.report_number = self.generate_report_number()

        # Sync is_final with status for backward compatibility
        if self.status == ReportStatus.FINAL:
            self.is_final = True
        elif self.status == ReportStatus.AMENDED:
            self.is_final = True  # Amended reports are also final

        super().save(*args, **kwargs)

    def generate_report_number(self):
        """Generate a unique report number."""
        today = timezone.now().strftime("%Y%m%d")
        prefix = f"RPT-{today}-"

        last_report = (
            Report.objects.filter(report_number__startswith=prefix)
            .order_by("report_number")
            .last()
        )

        if last_report:
            try:
                last_number = int(last_report.report_number.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    def mark_delivered(self, user, method="print"):
        """Mark report as delivered."""
        self.delivered_at = timezone.now()
        self.delivered_by = user
        self.delivery_method = method
        self.save(update_fields=["delivered_at", "delivered_by", "delivery_method"])

    def increment_reprint(self):
        """Increment reprint count."""
        self.reprint_count += 1
        self.last_reprinted_at = timezone.now()
        self.save(update_fields=["reprint_count", "last_reprinted_at"])

    def create_amendment(self, reason, user):
        """
        Create an amended version of this report.

        Args:
            reason (str): Reason for the amendment.
            user (User): User creating the amendment.

        Returns:
            Report: The new amended report instance.
        """
        # Mark original as amended
        self.status = ReportStatus.AMENDED
        self.save(update_fields=["status"])

        # Create new report linked to this one
        amended_report = Report.objects.create(
            order=self.order,
            status=ReportStatus.FINAL,
            amended_from=self,
            amendment_reason=reason,
            generated_by=user,
            template_name=self.template_name,
        )

        return amended_report
