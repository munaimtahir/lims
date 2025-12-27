from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from apps.patients.models import Patient
from apps.laboratory.models import Test, TestPanel


class Order(models.Model):
    """
    Represents a laboratory order for a patient.

    An order can contain multiple tests or panels.

    Attributes:
        order_id (str): The unique identifier for the order.
        patient (Patient): The patient this order belongs to.
        ordered_by (User): The user who created the order.
        created_at (datetime): The timestamp of when the order was created.
        updated_at (datetime): The timestamp of the last update.
        status (str): The current status of the order.
        notes (str, optional): Any notes related to the order.
        total_amount (Decimal): The total price of all items in the order.
        discount (Decimal): The discount applied to the order.
        net_amount (Decimal): The final amount after discount.
        is_paid (bool): Whether the order has been paid for.
    """

    ORDER_ID_PREFIX = "ORD"

    STATUS_CHOICES = [
        ("NEW", "New"),
        ("COLLECTED", "Collected"),
        ("IN_PROCESS", "In Process"),
        ("VERIFIED", "Verified"),
        ("PUBLISHED", "Published"),
        ("CANCELLED", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("ROUTINE", "Routine"),
        ("URGENT", "Urgent"),
        ("STAT", "STAT"),
    ]

    order_id = models.CharField(
        max_length=20, unique=True, editable=False, db_index=True
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="orders"
    )
    ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="NEW"
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="ROUTINE"
    )
    notes = models.TextField(blank=True)

    # Financials
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    net_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """
        Return a string representation of the order.

        Returns:
            str: A string in the format "order_id - patient".
        """
        return f"{self.order_id} - {self.patient}"

    def save(self, *args, **kwargs):
        """
        Override the save method to generate an order ID and calculate the net amount.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        if not self.order_id:
            self.order_id = self.generate_order_id()

        # Calculate net amount
        self.net_amount = max(self.total_amount - self.discount, Decimal("0.00"))

        super().save(*args, **kwargs)

    def generate_order_id(self):
        """
        Generate a unique order ID in the format ORD-YYYYMMDD-NNNN.

        This matches the legacy format for consistency.

        Returns:
            str: The generated order ID.
        """
        today = timezone.now().strftime("%Y%m%d")
        prefix = f"{self.ORDER_ID_PREFIX}-{today}-"

        last_order = (
            Order.objects.filter(order_id__startswith=prefix)
            .order_by("order_id")
            .last()
        )

        if last_order:
            try:
                last_number = int(last_order.order_id.split("-")[-1])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    def calculate_total(self):
        """
        Recalculate the total amount for the order from its items.
        """
        total = sum(item.price for item in self.items.all())
        self.total_amount = total
        self.save()


class OrderItem(models.Model):
    """
    Represents a single item within an order, which can be a test or a panel.

    Attributes:
        order (Order): The order this item belongs to.
        test (Test, optional): The test associated with this item.
        panel (TestPanel, optional): The panel associated with this item.
        price (Decimal): The price of the item.
        status (str): The status of the item's result.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # Can be a single test or a panel
    test = models.ForeignKey(Test, on_delete=models.PROTECT, null=True, blank=True)
    panel = models.ForeignKey(
        TestPanel, on_delete=models.PROTECT, null=True, blank=True
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Result tracking - status matches order status workflow
    status = models.CharField(
        max_length=20, choices=Order.STATUS_CHOICES, default="NEW"
    )

    class Meta:
        unique_together = ("order", "test", "panel")

    def __str__(self):
        """
        Return a string representation of the order item.

        Returns:
            str: A string in the format "item_name for order_id".
        """
        item_name = (
            self.test.test_name
            if self.test
            else (self.panel.panel_name if self.panel else "Unknown")
        )
        return f"{item_name} for {self.order.order_id}"

    def save(self, *args, **kwargs):
        """
        Override the save method to auto-set the price if not provided.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        if not self.price:
            if self.test:
                self.price = self.test.price
            elif self.panel:
                self.price = self.panel.price
        super().save(*args, **kwargs)
