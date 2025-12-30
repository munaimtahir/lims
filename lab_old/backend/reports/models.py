"""Report models and PDF generation."""

from django.db import models

from orders.models import Order


class Report(models.Model):
    """
    Represents a generated PDF report for a specific order.

    Attributes:
        order (OneToOneField): The order that this report is for.
        pdf_file (FileField): The generated PDF file.
        generated_at (DateTimeField): The timestamp when the report was generated.
        generated_by (ForeignKey): The user who generated the report.
    """

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="report")
    pdf_file = models.FileField(upload_to="reports/", null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_reports",
    )

    class Meta:
        db_table = "reports"
        ordering = ["-generated_at"]

    def __str__(self):
        """Returns a string representation of the report."""
        return f"Report for {self.order.order_no}"
