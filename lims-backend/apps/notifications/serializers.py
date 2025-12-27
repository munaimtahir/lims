"""
Serializers for notifications app.
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    
    recipient_user_name = serializers.CharField(
        source="recipient_user.full_name", read_only=True
    )
    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "recipient_email",
            "recipient_user",
            "recipient_user_name",
            "subject",
            "message",
            "status",
            "status_display",
            "sent_at",
            "error_message",
            "related_order",
            "related_payment",
            "related_report",
            "created_at",
        ]
        read_only_fields = ["sent_at", "created_at"]

