"""Serializers for settings app."""

from rest_framework import serializers

from .models import RolePermission, WorkflowSettings


class WorkflowSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the WorkflowSettings model.
    """

    class Meta:
        model = WorkflowSettings
        fields = [
            "enable_sample_collection",
            "enable_sample_receive",
            "enable_verification",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class RolePermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for the RolePermission model.
    """

    class Meta:
        model = RolePermission
        fields = [
            "id",
            "role",
            "can_register",
            "can_collect",
            "can_enter_result",
            "can_verify",
            "can_publish",
            "can_edit_catalog",
            "can_edit_settings",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
