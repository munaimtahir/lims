"""Order models."""

from django.db import models

from catalog.models import TestCatalog
from patients.models import Patient


class OrderStatus(models.TextChoices):
    """
    Enumeration for the status of an order or order item.
    """

    NEW = "NEW", "New"
    COLLECTED = "COLLECTED", "Collected"
    IN_PROCESS = "IN_PROCESS", "In Process"
    VERIFIED = "VERIFIED", "Verified"
    PUBLISHED = "PUBLISHED", "Published"
    CANCELLED = "CANCELLED", "Cancelled"


class OrderPriority(models.TextChoices):
    """
    Enumeration for the priority of an order.
    """

    ROUTINE = "ROUTINE", "Routine"
    URGENT = "URGENT", "Urgent"
    STAT = "STAT", "STAT"


class Order(models.Model):
    """
    Represents a patient's order for one or more lab tests.

    Attributes:
        order_no (CharField): A unique, system-generated order number.
        patient (ForeignKey): The patient associated with the order.
        priority (CharField): The priority of the order (e.g., Routine, Urgent).
        status (CharField): The current status of the order.
        notes (TextField): Any notes or comments related to the order.
        created_at (DateTimeField): The timestamp when the order was created.
        updated_at (DateTimeField): The timestamp when the order was last updated.
    """

    order_no = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="orders"
    )
    priority = models.CharField(
        max_length=20,
        choices=OrderPriority.choices,
        default=OrderPriority.ROUTINE,
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_no"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        """Returns a string representation of the order."""
        return f"{self.order_no} - {self.patient.full_name}"

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to generate an order number.

        The order number is generated based on the current date and a
        sequential number for that day.
        """
        if not self.order_no:
            from django.utils import timezone

            today = timezone.now().strftime("%Y%m%d")
            last_order = (
                Order.objects.filter(order_no__startswith=f"ORD-{today}")
                .order_by("order_no")
                .last()
            )
            if last_order:
                last_num = int(last_order.order_no.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.order_no = f"ORD-{today}-{new_num:04d}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Represents a single test item within an order.

    Attributes:
        order (ForeignKey): The order this item belongs to.
        test (ForeignKey): The test from the catalog for this item.
        status (CharField): The current status of this specific test.
        created_at (DateTimeField): The timestamp when the item was created.
        updated_at (DateTimeField): The timestamp when the item was last updated.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    test = models.ForeignKey(TestCatalog, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order_items"
        ordering = ["id"]

    def __str__(self):
        """Returns a string representation of the order item."""
        return f"{self.order.order_no} - {self.test.name}"
