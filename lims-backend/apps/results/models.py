from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import logging
from apps.orders.models import OrderItem
from apps.laboratory.models import TestParameter

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
        ("normal", "Normal"),
        ("low", "Low"),
        ("high", "High"),
        ("critical_low", "Critical Low"),
        ("critical_high", "Critical High"),
        ("abnormal", "Abnormal"),  # For non-numeric
    ]

    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="results"
    )
    test_parameter = models.ForeignKey(TestParameter, on_delete=models.PROTECT)

    result_value = models.CharField(max_length=500)

    # Auto-calculated flag
    flag = models.CharField(max_length=20, choices=FLAG_CHOICES, default="normal")

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
        # Handle empty or None result values
        if not self.result_value or not self.result_value.strip():
            logger.warning(
                f"Empty result value for parameter {self.test_parameter.parameter_name} "
                f"in order {self.order_item.order.order_id}"
            )
            self.flag = "abnormal"
            return

        # Try to parse as numeric
        try:
            # Remove any whitespace and common non-numeric characters
            cleaned_value = self.result_value.strip().replace(',', '').replace(' ', '')
            value = float(cleaned_value)
        except (ValueError, TypeError, AttributeError):
            # Non-numeric result - check if it's a valid text result
            cleaned_value = self.result_value.strip().upper()
            
            # Common non-numeric result patterns
            if cleaned_value in ['NEGATIVE', 'NEG', '-', 'NONE', 'NOT DETECTED', 'ND']:
                self.flag = "normal"
                return
            elif cleaned_value in ['POSITIVE', 'POS', '+', 'DETECTED', 'REACTIVE']:
                self.flag = "abnormal"
                return
            else:
                # Unknown non-numeric result - mark as abnormal but don't fail
                logger.info(
                    f"Non-numeric result '{self.result_value}' for parameter "
                    f"{self.test_parameter.parameter_name} in order {self.order_item.order.order_id}. "
                    f"Marking as abnormal."
                )
                self.flag = "abnormal"
                return

        # Get patient gender for gender-specific ranges
        try:
            gender = self.order_item.order.patient.gender
        except AttributeError:
            logger.warning(
                f"Could not determine patient gender for order {self.order_item.order.order_id}. "
                f"Using default ranges."
            )
            gender = None

        # Get reference ranges based on gender
        if gender == "Male":
            ref_min = self.test_parameter.reference_min_male
            ref_max = self.test_parameter.reference_max_male
        elif gender == "Female":
            ref_min = self.test_parameter.reference_min_female
            ref_max = self.test_parameter.reference_max_female
        else:
            # Unknown gender or not specified - use male ranges as default, or both if available
            ref_min = self.test_parameter.reference_min_male or self.test_parameter.reference_min_female
            ref_max = self.test_parameter.reference_max_male or self.test_parameter.reference_max_female

        # Get critical values (gender-independent)
        crit_low = self.test_parameter.critical_low
        crit_high = self.test_parameter.critical_high

        # Validate critical values are reasonable
        if crit_low is not None and crit_high is not None and crit_low >= crit_high:
            logger.warning(
                f"Invalid critical range for parameter {self.test_parameter.parameter_name}: "
                f"critical_low ({crit_low}) >= critical_high ({crit_high})"
            )

        # Check critical values first (highest priority)
        if crit_low is not None and value <= crit_low:
            self.flag = "critical_low"
            logger.warning(
                f"Critical low value detected: {value} <= {crit_low} for parameter "
                f"{self.test_parameter.parameter_name} in order {self.order_item.order.order_id}"
            )
            return
        elif crit_high is not None and value >= crit_high:
            self.flag = "critical_high"
            logger.warning(
                f"Critical high value detected: {value} >= {crit_high} for parameter "
                f"{self.test_parameter.parameter_name} in order {self.order_item.order.order_id}"
            )
            return

        # Check reference ranges
        if ref_min is None and ref_max is None:
            # No reference range available - mark as normal but log
            logger.info(
                f"No reference range available for parameter {self.test_parameter.parameter_name} "
                f"(gender: {gender}). Marking as normal."
            )
            self.flag = "normal"
            return

        # Check if value is within range
        if ref_min is not None and ref_max is not None:
            # Both min and max defined
            if ref_min > ref_max:
                logger.warning(
                    f"Invalid reference range for parameter {self.test_parameter.parameter_name}: "
                    f"min ({ref_min}) > max ({ref_max})"
                )
                self.flag = "normal"  # Default to normal if range is invalid
                return

            if value < ref_min:
                self.flag = "low"
            elif value > ref_max:
                self.flag = "high"
            else:
                self.flag = "normal"
        elif ref_min is not None:
            # Only minimum defined
            if value < ref_min:
                self.flag = "low"
            else:
                self.flag = "normal"
        elif ref_max is not None:
            # Only maximum defined
            if value > ref_max:
                self.flag = "high"
            else:
                self.flag = "normal"
        else:
            # Should not reach here, but default to normal
            self.flag = "normal"
        
        # Send critical value alert if needed
        if self.flag in ["critical_low", "critical_high"]:
            try:
                from apps.notifications.utils import send_critical_value_alert
                send_critical_value_alert(self)
            except Exception as e:
                # Don't fail save if notification fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send critical value alert: {e}")
