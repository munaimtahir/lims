"""
Audit trail models for LIMS compliance and logging.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    """
    Represents an audit log entry for tracking changes to critical data.

    Attributes:
        user (User): The user who performed the action.
        action (str): The type of action (CREATE, UPDATE, DELETE, etc.).
        content_type (ContentType): The type of the affected model.
        object_id (str): The primary key of the affected object.
        content_object (GenericForeignKey): A generic reference to the affected object.
        table_name (str): The database table name of the affected model.
        old_value (dict): The previous state of the object (for updates/deletes).
        new_value (dict): The new state of the object (for creates/updates).
        timestamp (datetime): When the action occurred.
        ip_address (str): The IP address of the user.
        user_agent (str): The user agent string of the client.
        notes (str): Additional notes about the action.
    """

    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("VERIFY", "Verify"),
        ("APPROVE", "Approve"),
        ("REJECT", "Reject"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Denormalized for easier querying
    table_name = models.CharField(max_length=100, db_index=True)

    # Store old and new values as JSON
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["table_name", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
        ]

    def __str__(self):
        """
        Return a string representation of the audit log entry.

        Returns:
            str: A string describing the action.
        """
        user_name = self.user.full_name if self.user else "System"
        return f"{user_name} - {self.action} on {self.table_name} at {self.timestamp}"
