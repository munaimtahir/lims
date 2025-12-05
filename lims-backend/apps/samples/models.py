from django.db import models
from django.conf import settings
from apps.orders.models import Order, OrderItem


class SampleCollection(models.Model):
    """
    Represents the collection of a sample for a laboratory order.

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
        ('pending', 'Pending'),
        ('collected', 'Collected'),
        ('received', 'Received in Lab'),
        ('rejected', 'Rejected'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='samples')
    # Can be linked to specific items or the whole order
    order_items = models.ManyToManyField(OrderItem, related_name='samples')

    sample_type = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    collected_at = models.DateTimeField(blank=True, null=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='samples_collected'
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-collected_at']

    def __str__(self):
        """
        Return a string representation of the sample collection.

        Returns:
            str: A string in the format "Sample barcode/id for order_id".
        """
        return f"Sample {self.barcode or self.id} for {self.order.order_id}"
