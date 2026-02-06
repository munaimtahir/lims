"""
Serializers for core models.
"""

from rest_framework import serializers
from .models import SystemSettings, PrintTemplate, CollectionCenter, RegistrationCounter, LabDailyCounter


class CollectionCenterSerializer(serializers.ModelSerializer):
    """Serializer for Collection Centers."""
    
    class Meta:
        model = CollectionCenter
        fields = ['id', 'code', 'name', 'address', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class RegistrationCounterSerializer(serializers.ModelSerializer):
    """Serializer for Registration Counters (read-only)."""
    center_name = serializers.CharField(source='center.name', read_only=True)
    center_code = serializers.CharField(source='center.code', read_only=True)
    
    class Meta:
        model = RegistrationCounter
        fields = ['id', 'yymm', 'center', 'center_name', 'center_code', 'last_value', 'updated_at']
        read_only_fields = ['yymm', 'center', 'last_value', 'updated_at']


class LabDailyCounterSerializer(serializers.ModelSerializer):
    """Serializer for Lab Daily Counters (read-only)."""
    center_name = serializers.CharField(source='center.name', read_only=True)
    center_code = serializers.CharField(source='center.code', read_only=True)
    
    class Meta:
        model = LabDailyCounter
        fields = ['id', 'date', 'center', 'center_name', 'center_code', 'last_value', 'updated_at']
        read_only_fields = ['date', 'center', 'last_value', 'updated_at']


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
            "lab_display_name",
            "lab_address",
            "lab_phone",
            "lab_email",
            "lab_logo",
            "report_header",
            "report_footer",
            "report_header_image",
            "report_footer_image",
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


class PrintTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for PrintTemplate with config validation.
    """

    class Meta:
        model = PrintTemplate
        fields = [
            "id",
            "template_key",
            "type",
            "name",
            "description",
            "is_active",
            "config",
            "disclaimer_text",
            "signatories",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("config must be an object")

        margins = value.get("margins", {})
        if not isinstance(margins, dict):
            raise serializers.ValidationError("config.margins must be an object")
        for side in ["top", "right", "bottom", "left"]:
            if side not in margins:
                raise serializers.ValidationError(f"config.margins.{side} is required")
            try:
                margin_val = float(margins[side])
            except (TypeError, ValueError):
                raise serializers.ValidationError(f"config.margins.{side} must be a number")
            if margin_val < 0:
                raise serializers.ValidationError(f"config.margins.{side} must be >= 0")

        font_scale = value.get("font_scale", 1.0)
        try:
            font_scale = float(font_scale)
        except (TypeError, ValueError):
            raise serializers.ValidationError("config.font_scale must be a number")
        if font_scale < 0.5 or font_scale > 2.0:
            raise serializers.ValidationError("config.font_scale must be between 0.5 and 2.0")

        paper_size = value.get("paper_size", "A4")
        if paper_size not in ["A4", "Letter"]:
            raise serializers.ValidationError("config.paper_size must be 'A4' or 'Letter'")

        for key in [
            "show_logo",
            "show_header_image",
            "show_footer_image",
            "show_disclaimer",
            "show_signatures",
            "show_qr",
            "show_barcode",
        ]:
            if key in value and not isinstance(value[key], bool):
                raise serializers.ValidationError(f"config.{key} must be true or false")

        return value

    def validate_signatories(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("signatories must be a list")
        for entry in value:
            if not isinstance(entry, dict):
                raise serializers.ValidationError("signatories entries must be objects")
            if "name" not in entry or not entry["name"]:
                raise serializers.ValidationError("signatories entry requires name")
            if "title" not in entry or not entry["title"]:
                raise serializers.ValidationError("signatories entry requires title")
        return value
    
    def validate_tax_rate(self, value):
        """Validate tax rate is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Tax rate cannot be negative")
        return value
