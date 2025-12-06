from django.db import models
from django.conf import settings
from apps.orders.models import Order


class Report(models.Model):
    """
    Represents a generated PDF report for an order.

    Attributes:
        order (Order): The order this report is for.
        report_file (FileField): The path to the generated PDF file.
        generated_at (datetime): The timestamp of when the report was generated.
        generated_by (User): The user who generated the report.
        is_final (bool): Whether this is the final report for the order.
        pathologist_signature (FileField, optional): Digital signature of the pathologist.
        technician_signature (FileField, optional): Digital signature of the lab technician.
        verified_by (User, optional): The pathologist who verified the report.
        verified_at (datetime, optional): When the report was verified.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="reports")
    report_file = models.FileField(upload_to="reports/%Y/%m/%d/")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports_generated",
    )

    is_final = models.BooleanField(default=True)

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

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        """
        Return a string representation of the report.

        Returns:
            str: A string in the format "Report for order_id at generated_at".
        """
        return f"Report for {self.order.order_id} at {self.generated_at}"
