from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import logging
from apps.orders.models import OrderItem
from apps.laboratory.models import TestParameter
from apps.laboratory.ranges import compute_flag, pick_reference_range

logger = logging.getLogger(__name__)


class TestResult(models.Model):
    """
    Represents the result for a specific test parameter within an order item.

    Attributes:
        order_item (OrderItem): The order item this result belongs to.
        test_parameter (TestParameter): The specific parameter being measured.
        result_value (str): The value of the result.
        flag (str): An automatically calculated flag indicating if the result is normal, low, high, etc.
        status (str): The verification status of the result.
        entered_by (User): The user who entered the result.
        entered_at (datetime): The timestamp of when the result was entered.
        verified_by (User, optional): The user who verified the result.
        verified_at (datetime, optional): The timestamp of when the result was verified.
        remarks (str, optional): Any remarks about the result.
    """

    FLAG_CHOICES = [
        ("", "Normal"),
        ("L", "Low"),
        ("H", "High"),
        ("C", "Critical"),
    ]

    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="results"
    )
    test_parameter = models.ForeignKey(TestParameter, on_delete=models.PROTECT)

    result_value = models.CharField(max_length=500)

    # Auto-calculated flag
    flag = models.CharField(max_length=20, choices=FLAG_CHOICES, default="")

    # Verification Status - matches legacy workflow
    VERIFICATION_STATUS = [
        ("DRAFT", "Draft"),
        ("ENTERED", "Entered"),
        ("VERIFIED", "Verified"),
        ("PUBLISHED", "Published"),
    ]
    status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS, default="DRAFT"
    )

    # Metadata
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="results_entered",
    )
    entered_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="results_verified",
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)

    remarks = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes about the result")

    class Meta:
        unique_together = ("order_item", "test_parameter")
        ordering = ["test_parameter__display_order"]

    def __str__(self):
        """
        Return a string representation of the test result.

        Returns:
            str: A string in the format "parameter_name: result_value".
        """
        return f"{self.test_parameter.parameter_name}: {self.result_value}"

    def save(self, *args, **kwargs):
        """
        Override the save method to validate the result before saving.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.validate_result()
        super().save(*args, **kwargs)

    def validate_result(self):
        """
        Validate the result against the test parameter's reference ranges and set the appropriate flag.

        This method checks for critical, high, and low values based on the patient's gender.
        Handles edge cases including missing ranges, invalid data types, and non-numeric results.

        Raises:
            ValidationError: If result value cannot be validated and is required to be numeric.
        """
        if not self.result_value or not str(self.result_value).strip():
            logger.warning(
                f"Empty result value for parameter {self.test_parameter.parameter_name} "
                f"in order {self.order_item.order.order_id}"
            )
            self.flag = ""
            return

        patient = None
        try:
            patient = self.order_item.order.patient
        except AttributeError:
            logger.warning(
                f"Could not determine patient for order {self.order_item.order.order_id}. "
                f"Using fallback ranges."
            )

        range_info = pick_reference_range(self.test_parameter, patient)
        self.flag = compute_flag(
            self.result_value,
            range_info["ref_min"],
            range_info["ref_max"],
            range_info["critical_low"],
            range_info["critical_high"],
        )
