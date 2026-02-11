from django.conf import settings
from django.db import models

from apps.orders.models import Order


class Payment(models.Model):
    """
    Represents a payment record for an order.

    Attributes:
        order (Order): The order associated with this payment.
        amount (Decimal): The amount paid.
        payment_method (str): The method of payment (e.g., cash, card).
        transaction_id (str, optional): The unique identifier for the transaction.
        payment_date (datetime): The timestamp of when the payment was recorded.
        recorded_by (User): The user who recorded the payment.
        notes (str, optional): Any notes related to the payment.
    """

    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("card", "Credit/Debit Card"),
        ("bank_transfer", "Bank Transfer"),
        ("mobile_money", "Mobile Money"),
        ("insurance", "Insurance"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["payment_date"]),
            models.Index(fields=["payment_method"]),
        ]

    def __str__(self):
        """
        Return a string representation of the payment.

        Returns:
            str: A string in the format "amount for order_id".
        """
        return f"{self.amount} for {self.order.order_id}"

    def save(self, *args, **kwargs):
        """
        Override the save method to update the order's payment status.
        """
        super().save(*args, **kwargs)
        self.order.update_payment_status()

    def delete(self, *args, **kwargs):
        """
        Override the delete method to update the order's payment status.
        """
        order = self.order
        super().delete(*args, **kwargs)
        order.update_payment_status()
