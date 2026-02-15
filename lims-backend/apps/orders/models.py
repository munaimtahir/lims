import logging
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import Branch, CollectionCenter, Tenant
from apps.core.numbering import generate_branch_order_id, generate_lab_number
from apps.core.validators import validate_lab_number
from apps.laboratory.models import Test, TestPanel
from apps.patients.models import Patient

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
        max_length=30, editable=False, db_index=True
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
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
        help_text="Tube Label (MDD-XXX)",
    )
    lab_date = models.DateField(blank=True, null=True, db_index=True)
    daily_serial = models.IntegerField(blank=True, null=True)
    collection_center = models.ForeignKey(
        CollectionCenter,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )
    # Multi-branch
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )
    collection_branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders_collected",
    )
    processing_branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders_processing",
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
            models.Index(fields=["referred_by"]),
            models.Index(fields=["lab_number"]),
            models.Index(fields=["lab_date", "collection_center", "daily_serial"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "order_id"], name="unique_order_id_per_tenant"
            )
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
        # Default tenant from patient or fallback
        if not self.tenant:
            self.tenant = getattr(self.patient, "tenant", None)
        if not self.tenant:
            from apps.core.models import get_default_tenant

            self.tenant = get_default_tenant()

        # Default branches only when enable_branches is True (small-lab flow works with null branch)
        from apps.core.services.settings import get_tenant_settings

        tenant_settings = get_tenant_settings(self.tenant) if self.tenant else None
        enable_branches = getattr(tenant_settings, "enable_branches", False) if tenant_settings else False
        if enable_branches:
            if not self.collection_branch:
                from apps.core.models import Branch

                hq_branch = (
                    Branch.objects.filter(tenant=self.tenant, code="00").first()
                    or Branch.objects.filter(code="00").first()
                )
                self.collection_branch = hq_branch
            if not self.processing_branch:
                self.processing_branch = self.collection_branch

        if not self.order_id:
            # Branch-based order ID if branch available
            if self.tenant and self.collection_branch:
                self.order_id = generate_branch_order_id(
                    tenant=self.tenant,
                    branch=self.collection_branch,
                    dt=self.created_at or timezone.now(),
                )
            else:
                self.order_id = self.generate_order_id()

        # Prevent mutation of immutable lab identity fields after creation
        if self.pk:
            try:
                old = Order.objects.get(pk=self.pk)
                if old.lab_number and self.lab_number and old.lab_number != self.lab_number:
                    raise ValidationError("Lab number is immutable after creation.")
                if old.lab_date and self.lab_date and old.lab_date != self.lab_date:
                    raise ValidationError("Lab date is immutable after creation.")
                if old.daily_serial and self.daily_serial and old.daily_serial != self.daily_serial:
                    raise ValidationError("Daily serial is immutable after creation.")
                if old.status in ["PUBLISHED", "CANCELLED"]:
                    raise ValidationError("Published or cancelled orders cannot be modified.")
            except Order.DoesNotExist:
                pass

        # V2 Lab Numbering (legacy) retained; branch fields separate
        if not self.lab_number:
            if not self.collection_center:
                center_00, _ = CollectionCenter.objects.get_or_create(
                    code="00", defaults={"name": "Head Office", "is_active": True}
                )
                self.collection_center = center_00

            generation_dt = self.created_at or timezone.now()
            self.lab_date = generation_dt.date()

            self.lab_number, self.daily_serial = generate_lab_number(
                self.collection_center, generation_dt
            )

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
        # Define valid transitions (NEW may go to IN_PROCESS when sample workflow is disabled)
        valid_transitions = {
            "NEW": ["COLLECTED", "IN_PROCESS", "CANCELLED"],
            "COLLECTED": ["IN_PROCESS", "CANCELLED"],
            "IN_PROCESS": ["VERIFIED", "CANCELLED"],
            "VERIFIED": ["IN_PROCESS", "PUBLISHED", "CANCELLED"],  # Allow return to IN_PROCESS (Unverify)
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
        total_paid = self.payments.aggregate(total=models.Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        self.paid_amount = total_paid
        self.save()

        # If the order has just become paid, trigger sample generation only when sample workflow is enabled
        if not was_paid_before and self.is_paid:
            from apps.core.services.settings import get_tenant_settings
            tenant_settings = get_tenant_settings(self.tenant)
            if tenant_settings and getattr(tenant_settings, "sample_workflow_enabled", True):
                from apps.samples.services import ensure_samples_for_paid_order
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


class DispatchStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    IN_TRANSIT = "IN_TRANSIT", "In Transit"
    RECEIVED = "RECEIVED", "Received"


class Dispatch(models.Model):
    """Minimal dispatch manifest: batch of orders sent from a branch to main lab."""

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="dispatches",
    )
    from_branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="dispatches_sent",
    )
    to_branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="dispatches_received",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="dispatches_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=DispatchStatus.choices,
        default=DispatchStatus.CREATED,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispatches_received",
    )

    class Meta:
        db_table = "orders_dispatch"
        ordering = ["-created_at"]
        verbose_name = "Dispatch"
        verbose_name_plural = "Dispatches"

    def __str__(self):
        return f"Dispatch {self.id} {self.from_branch} → {self.to_branch} ({self.status})"


class DispatchItem(models.Model):
    """Order included in a dispatch."""

    dispatch = models.ForeignKey(
        Dispatch,
        on_delete=models.CASCADE,
        related_name="items",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="dispatch_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders_dispatch_item"
        unique_together = [["dispatch", "order"]]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.order.order_id} in Dispatch {self.dispatch_id}"
