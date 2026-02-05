from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.orders.models import Order, OrderItem


class SampleStatus(models.TextChoices):
    """
    Enumeration for the status of a lab sample.
    """
    PENDING = "PENDING", "Pending Collection"
    COLLECTED = "COLLECTED", "Collected"
    RECEIVED = "RECEIVED", "Received in Lab"
    REJECTED = "REJECTED", "Rejected"
    POSTPONED = "POSTPONED", "Postponed"


class Sample(models.Model):
    """
    Represents a single lab specimen for an order item.

    This matches the legacy structure where each sample is linked to a specific order item.

    Attributes:
        order_item (OrderItem): The order item this sample is for.
        sample_type (str): The type of sample (e.g., 'Blood', 'Urine').
        barcode (str): A unique, system-generated barcode for the sample.
        collected_at (datetime): The timestamp when the sample was collected.
        collected_by (User): The user who collected the sample.
        received_at (datetime): The timestamp when the sample was received in the lab.
        received_by (User): The user who received the sample.
        status (str): The current status of the sample in the workflow.
        rejection_reason (str): The reason for sample rejection, if applicable.
        postponement_reason (str): The reason for sample postponement, if applicable.
        notes (str): Any notes or comments related to the sample.
    """

    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="samples"
    )
    sample_type = models.CharField(max_length=50)
    barcode = models.CharField(max_length=50, unique=True, db_index=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="collected_samples",
    )
    received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="received_samples",
    )
    status = models.CharField(
        max_length=20, choices=SampleStatus.choices, default=SampleStatus.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    postponement_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "samples"
        verbose_name = "Sample"
        verbose_name_plural = "Samples"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["barcode"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        """Return a string representation of the sample."""
        return f"{self.barcode} - {self.sample_type}"

    def save(self, *args, **kwargs):
        """
        Override the save method to generate a barcode if it doesn't exist.

        The barcode is generated based on the current date and a sequential number.
        """
        if not self.barcode:
            today = timezone.now().strftime("%Y%m%d")
            last_sample = (
                Sample.objects.filter(barcode__startswith=f"SAM-{today}")
                .order_by("barcode")
                .last()
            )
            if last_sample:
                try:
                    last_num = int(last_sample.barcode.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.barcode = f"SAM-{today}-{new_num:04d}"
        super().save(*args, **kwargs)


# Keep SampleCollection for backward compatibility
class SampleCollection(models.Model):
    """
    Represents the collection of a sample for a laboratory order.

    DEPRECATED: Use Sample model instead. Kept for backward compatibility.

    Attributes:
        order (Order): The order this sample is for.
        order_items (ManyToManyField): The specific order items this sample is for.
        sample_type (str): The type of sample collected (e.g., "EDTA Blood").
        barcode (str, optional): The barcode on the sample tube.
        status (str): The current status of the sample.
        collected_at (datetime, optional): The timestamp of when the sample was collected.
        collected_by (User, optional): The user who collected the sample.
        notes (str, optional): Any notes related to the sample collection.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("collected", "Collected"),
        ("received", "Received in Lab"),
        ("rejected", "Rejected"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="sample_collections")
    # Can be linked to specific items or the whole order
    order_items = models.ManyToManyField(OrderItem, related_name="sample_collections")

    sample_type = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    collected_at = models.DateTimeField(blank=True, null=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sample_collections_collected",
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-collected_at"]

    def __str__(self):
        """
        Return a string representation of the sample collection.

        Returns:
            str: A string in the format "Sample barcode/id for order_id".
        """
        return f"Sample {self.barcode or self.id} for {self.order.order_id}"
