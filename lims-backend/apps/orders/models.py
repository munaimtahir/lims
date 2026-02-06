from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging
from apps.patients.models import Patient
from apps.laboratory.models import Test, TestPanel
from apps.core.models import CollectionCenter
from apps.core.numbering import generate_lab_number
from apps.core.validators import validate_lab_number

logger = logging.getLogger(__name__)


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
    referred_by = models.CharField(max_length=255, blank=True, null=True)
    
    # Lab Numbering (V2)
    lab_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        validators=[validate_lab_number],
        help_text="Tube Label (MDD-XXX)"
    )
    lab_date = models.DateField(blank=True, null=True, db_index=True)
    daily_serial = models.IntegerField(blank=True, null=True)
    collection_center = models.ForeignKey(
        CollectionCenter,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders"
    )

    # Financials
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    net_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    paid_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    due_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["lab_number"]),
            models.Index(fields=["lab_date", "collection_center", "daily_serial"]),
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
        Override the save method to generate an order ID, calculate the net amount,
        and validate status transitions.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        if not self.order_id:
            self.order_id = self.generate_order_id()
        
        # V2 Lab Numbering
        if not self.lab_number:
            if not self.collection_center:
                # Fallback to Head Office (00) if not set
                center_00, _ = CollectionCenter.objects.get_or_create(code="00", defaults={"name": "Head Office", "is_active": True})
                self.collection_center = center_00
            
            # Use created_at if available, else now
            generation_dt = self.created_at or timezone.now()
            self.lab_date = generation_dt.date()
            
            # Generate number
            self.lab_number, self.daily_serial = generate_lab_number(self.collection_center, generation_dt)

        # Calculate net amount
        self.net_amount = max(self.total_amount - self.discount, Decimal("0.00"))
        
        # Calculate due amount
        self.due_amount = max(self.net_amount - self.paid_amount, Decimal("0.00"))
        
        # Update is_paid status
        self.is_paid = self.due_amount <= Decimal("0.00")
        
        # Validate status transition if status is being changed
        if self.pk:  # Only validate if this is an update
            try:
                old_order = Order.objects.get(pk=self.pk)
                if old_order.status != self.status:
                    self.validate_status_transition(old_order.status, self.status)
            except Order.DoesNotExist:
                pass  # New order, no validation needed

        super().save(*args, **kwargs)

    def validate_status_transition(self, old_status, new_status):
        """
        Validate that a status transition is allowed.

        Valid transitions:
        - NEW -> COLLECTED, CANCELLED
        - COLLECTED -> IN_PROCESS, CANCELLED
        - IN_PROCESS -> VERIFIED, CANCELLED
        - VERIFIED -> PUBLISHED, CANCELLED
        - PUBLISHED -> (no transitions, final state)
        - CANCELLED -> (no transitions, final state)

        Args:
            old_status (str): The current status.
            new_status (str): The desired new status.

        Raises:
            ValidationError: If the transition is not allowed.
        """
        # Define valid transitions
        valid_transitions = {
            "NEW": ["COLLECTED", "CANCELLED"],
            "COLLECTED": ["IN_PROCESS", "CANCELLED"],
            "IN_PROCESS": ["VERIFIED", "CANCELLED"],
            "VERIFIED": ["PUBLISHED", "CANCELLED"],
            "PUBLISHED": [],  # Final state, no transitions allowed
            "CANCELLED": [],  # Final state, no transitions allowed
        }

        # Check if transition is valid
        if new_status not in valid_transitions.get(old_status, []):
            error_msg = (
                f"Invalid status transition from '{old_status}' to '{new_status}'. "
                f"Valid transitions from '{old_status}': {', '.join(valid_transitions.get(old_status, []))}"
            )
            logger.warning(
                f"Invalid status transition attempted for order {self.order_id}: "
                f"{old_status} -> {new_status}"
            )
            raise ValidationError(error_msg)

    def can_transition_to(self, new_status):
        """
        Check if the order can transition to a new status.

        Args:
            new_status (str): The desired new status.

        Returns:
            bool: True if the transition is allowed, False otherwise.
        """
        try:
            self.validate_status_transition(self.status, new_status)
            return True
        except ValidationError:
            return False

    def transition_to(self, new_status, user=None):
        """
        Transition the order to a new status with validation.

        Args:
            new_status (str): The desired new status.
            user (User, optional): The user making the transition.

        Raises:
            ValidationError: If the transition is not allowed.
        """
        self.validate_status_transition(self.status, new_status)
        self.status = new_status
        if user:
            self.ordered_by = user  # Track who made the transition
        self.save()

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

    def update_payment_status(self):
        """
        Update the order's paid amount and recalculate payment status.
        This should be called whenever a related Payment is saved or deleted.
        """
        from apps.billing.models import Payment
        
        was_paid_before = self.is_paid
        
        # Sum up all related payments
        total_paid = self.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        self.paid_amount = total_paid
        self.save()

        # If the order has just become paid, trigger sample generation
        if not was_paid_before and self.is_paid:
            from apps.samples.services import ensure_samples_for_paid_order
            # Assuming the last user to update the order is the one to credit for creation
            ensure_samples_for_paid_order(self, created_by=self.ordered_by)


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
