from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import Branch, Tenant
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
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="samples",
    )
    collected_at_branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="samples_collected",
    )
    current_branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="samples_current",
    )
    sample_type = models.CharField(max_length=50)
    barcode = models.CharField(max_length=50, unique=True, db_index=True)
    sample_id = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        db_index=True,
        help_text="Tenant-wide unique sample identifier (order-scoped).",
    )
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
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "sample_id"], name="unique_sample_per_tenant"
            )
        ]

    def __str__(self):
        """Return a string representation of the sample."""
        return f"{self.barcode} - {self.sample_type}"

    def clean(self):
        # Enforce terminal and forbidden transitions at model level
        if self.pk:
            previous = Sample.objects.get(pk=self.pk)
            if previous.status == SampleStatus.RECEIVED:
                raise ValidationError("Received samples are immutable.")
            allowed = {
                SampleStatus.PENDING: {SampleStatus.COLLECTED, SampleStatus.POSTPONED},
                SampleStatus.POSTPONED: {SampleStatus.COLLECTED},
                SampleStatus.COLLECTED: {SampleStatus.RECEIVED},
            }
            if self.status == previous.status:
                return
            if self.status not in allowed.get(previous.status, set()):
                raise ValidationError(
                    f"Invalid transition from {previous.status} to {self.status}."
                )

    def delete(self, *args, **kwargs):
        if self.status in [SampleStatus.COLLECTED, SampleStatus.RECEIVED]:
            raise ValidationError("Collected/received samples cannot be deleted.")
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Override the save method to generate a barcode if it doesn't exist.

        The barcode is generated based on the current date and a sequential number.
        """
        order = self.order_item.order if self.order_item else None

        # Default tenant/branches from order if missing
        if not self.tenant and order:
            self.tenant = order.tenant
        if not self.collected_at_branch and order:
            self.collected_at_branch = order.collection_branch
        if not self.current_branch:
            self.current_branch = self.collected_at_branch

        # Sample ID generation: {order_id}-S{n}
        if not self.sample_id and order:
            existing = (
                Sample.objects.filter(order_item__order=order)
                .exclude(pk=self.pk)
                .count()
            )
            self.sample_id = f"{order.order_id}-S{existing + 1}"

        # Keep barcode aligned to sample_id for compatibility
        if not self.barcode and self.sample_id:
            self.barcode = self.sample_id

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

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="sample_collections"
    )
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
