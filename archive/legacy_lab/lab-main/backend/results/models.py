"""Result models for test results and verification."""

from django.db import models

from orders.models import OrderItem


class ResultStatus(models.TextChoices):
    """
    Enumeration for the status of a test result.
    """

    DRAFT = "DRAFT", "Draft"
    ENTERED = "ENTERED", "Entered"
    VERIFIED = "VERIFIED", "Verified"
    PUBLISHED = "PUBLISHED", "Published"


class Result(models.Model):
    """
    Represents the result of a single test parameter for an order item.

    Attributes:
        order_item (ForeignKey): The order item this result is for.
        value (CharField): The result value.
        unit (CharField): The unit of measurement for the result.
        reference_range (CharField): The reference range for this result.
        flags (CharField): Flags for abnormal results (e.g., 'H' for high).
        status (CharField): The current status of the result in the workflow.
        entered_by (ForeignKey): The user who entered the result.
        entered_at (DateTimeField): The timestamp when the result was entered.
        verified_by (ForeignKey): The user who verified the result.
        verified_at (DateTimeField): The timestamp when the result was verified.
        published_at (DateTimeField): The timestamp when the result was published.
        notes (TextField): Any notes or comments related to the result.
        created_at (DateTimeField): The timestamp when the result was created.
        updated_at (DateTimeField): The timestamp when the result was last updated.
    """

    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="results"
    )
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=255, blank=True)
    flags = models.CharField(
        max_length=50, blank=True, help_text="H=High, L=Low, N=Normal"
    )
    status = models.CharField(
        max_length=20, choices=ResultStatus.choices, default=ResultStatus.DRAFT
    )
    entered_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="entered_results",
    )
    entered_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="verified_results",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "results"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        """Returns a string representation of the result."""
        return f"{self.order_item} - {self.value} {self.unit}"
