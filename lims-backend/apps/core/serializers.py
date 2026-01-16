"""
Serializers for core models.
"""

from rest_framework import serializers
from .models import SystemSettings

class SystemSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the SystemSettings model.
    """
    
    updated_by_name = serializers.CharField(source="updated_by.full_name", read_only=True)
    
    class Meta:
        model = SystemSettings
        fields = [
            "id",
            "lab_name",
            "lab_address",
            "lab_phone",
            "lab_email",
            "lab_logo",
            "report_header",
            "report_footer",
            "currency",
            "tax_rate",
            "email_host",
            "email_port",
            "email_use_tls",
            "email_use_ssl",
            "email_host_user",
            "email_host_password",
            "email_from",
            "backup_enabled",
            "backup_frequency",
            "updated_at",
            "updated_by",
            "updated_by_name",
        ]
        read_only_fields = ["updated_at"]
    
    def validate_email_port(self, value):
        """Validate email port is in valid range."""
        if value < 1 or value > 65535:
            raise serializers.ValidationError("Email port must be between 1 and 65535")
        return value
    
    def validate_tax_rate(self, value):
        """Validate tax rate is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Tax rate cannot be negative")
        return value

