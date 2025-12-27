"""
Notification models for email and system notifications.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class NotificationType(models.TextChoices):
    """Notification type choices."""
    ORDER_COMPLETE = "ORDER_COMPLETE", "Order Complete"
    CRITICAL_VALUE = "CRITICAL_VALUE", "Critical Value Alert"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT", "Payment Receipt"
    REPORT_READY = "REPORT_READY", "Report Ready"
    SYSTEM_ALERT = "SYSTEM_ALERT", "System Alert"


class NotificationStatus(models.TextChoices):
    """Notification status choices."""
    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class Notification(models.Model):
    """
    Represents a notification sent to a user or patient.
    
    Attributes:
        notification_type (str): Type of notification.
        recipient_email (str): Email address of recipient.
        recipient_user (User, optional): User recipient (if applicable).
        subject (str): Email subject line.
        message (str): Email message body.
        status (str): Notification status.
        sent_at (datetime, optional): When notification was sent.
        error_message (str, optional): Error message if sending failed.
        related_order (Order, optional): Related order (for order notifications).
        related_payment (Payment, optional): Related payment (for payment notifications).
        related_report (Report, optional): Related report (for report notifications).
        created_at (datetime): When notification was created.
    """
    
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )
    recipient_email = models.EmailField()
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications_received",
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Related objects
    related_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    related_payment = models.ForeignKey(
        "billing.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    related_report = models.ForeignKey(
        "reports.Report",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["notification_type", "status"]),
            models.Index(fields=["recipient_email"]),
        ]
    
    def __str__(self):
        """Return string representation."""
        return f"{self.notification_type} to {self.recipient_email} - {self.status}"

