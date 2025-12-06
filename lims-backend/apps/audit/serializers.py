"""
Serializers for the Audit app.
"""
from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the AuditLog model.

    Provides read-only access to audit log entries.
    """

    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "user_role",
            "action",
            "table_name",
            "object_id",
            "old_value",
            "new_value",
            "timestamp",
            "ip_address",
            "notes",
        ]
        read_only_fields = fields
