"""Sample models for sample collection and tracking."""

from django.db import models

from orders.models import OrderItem


class SampleStatus(models.TextChoices):
    """
    Enumeration for the status of a lab sample.
    """

    PENDING = "PENDING", "Pending Collection"
    COLLECTED = "COLLECTED", "Collected"
    RECEIVED = "RECEIVED", "Received in Lab"
    REJECTED = "REJECTED", "Rejected"


class Sample(models.Model):
    """
    Represents a single lab specimen for an order item.

    Attributes:
        order_item (ForeignKey): The order item this sample is for.
        sample_type (CharField): The type of sample (e.g., 'Blood', 'Urine').
        barcode (CharField): A unique, system-generated barcode for the
            sample.
        collected_at (DateTimeField): The timestamp when the sample was
            collected.
        collected_by (ForeignKey): The user who collected the sample.
        received_at (DateTimeField): The timestamp when the sample was
            received in the lab.
        received_by (ForeignKey): The user who received the sample.
        status (CharField): The current status of the sample in the workflow.
        rejection_reason (TextField): The reason for sample rejection, if applicable.
        notes (TextField): Any notes or comments related to the sample.
        created_at (DateTimeField): The timestamp when the sample was created.
        updated_at (DateTimeField): The timestamp when the sample was last updated.
    """

    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="samples"
    )
    sample_type = models.CharField(max_length=50)
    barcode = models.CharField(max_length=50, unique=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="collected_samples",
    )
    received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="received_samples",
    )
    status = models.CharField(
        max_length=20, choices=SampleStatus.choices, default=SampleStatus.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "samples"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["barcode"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        """Returns a string representation of the sample."""
        return f"{self.barcode} - {self.sample_type}"

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to generate a barcode.

        The barcode is generated based on the current date and a sequential number.
        """
        if not self.barcode:
            from django.utils import timezone

            today = timezone.now().strftime("%Y%m%d")
            last_sample = (
                Sample.objects.filter(barcode__startswith=f"SAM-{today}")
                .order_by("barcode")
                .last()
            )
            if last_sample:
                last_num = int(last_sample.barcode.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.barcode = f"SAM-{today}-{new_num:04d}"
        super().save(*args, **kwargs)
