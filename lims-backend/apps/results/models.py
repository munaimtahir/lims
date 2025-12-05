from django.db import models
from django.conf import settings
from apps.orders.models import OrderItem
from apps.laboratory.models import TestParameter


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
        ('normal', 'Normal'),
        ('low', 'Low'),
        ('high', 'High'),
        ('critical_low', 'Critical Low'),
        ('critical_high', 'Critical High'),
        ('abnormal', 'Abnormal'),  # For non-numeric
    ]

    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='results')
    test_parameter = models.ForeignKey(TestParameter, on_delete=models.PROTECT)

    result_value = models.CharField(max_length=500)

    # Auto-calculated flag
    flag = models.CharField(max_length=20, choices=FLAG_CHOICES, default='normal')

    # Verification Status
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')

    # Metadata
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='results_entered'
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='results_verified'
    )
    verified_at = models.DateTimeField(blank=True, null=True)

    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('order_item', 'test_parameter')
        ordering = ['test_parameter__display_order']

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
        """
        try:
            value = float(self.result_value)

            # Determine gender from patient
            gender = self.order_item.order.patient.gender

            # Get ranges
            if gender == 'Male':
                ref_min = self.test_parameter.reference_min_male
                ref_max = self.test_parameter.reference_max_male
            else:
                ref_min = self.test_parameter.reference_min_female
                ref_max = self.test_parameter.reference_max_female

            crit_low = self.test_parameter.critical_low
            crit_high = self.test_parameter.critical_high

            # Check criticals first
            if crit_low and value <= crit_low:
                self.flag = 'critical_low'
            elif crit_high and value >= crit_high:
                self.flag = 'critical_high'
            # Check normal ranges
            elif ref_min and value < ref_min:
                self.flag = 'low'
            elif ref_max and value > ref_max:
                self.flag = 'high'
            else:
                self.flag = 'normal'

        except (ValueError, TypeError):
            # Non-numeric result, can't auto-flag easily unless we add logic for text results
            # For now, default to normal or leave as is if manually set
            pass
