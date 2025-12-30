"""Admin configuration for settings app."""

from django.contrib import admin

from .models import RolePermission, WorkflowSettings


@admin.register(WorkflowSettings)
class WorkflowSettingsAdmin(admin.ModelAdmin):
    """Admin for workflow settings."""

    list_display = [
        "enable_sample_collection",
        "enable_sample_receive",
        "enable_verification",
        "updated_at",
    ]

    def has_add_permission(self, request):
        """Prevent adding more than one instance."""
        return not WorkflowSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton."""
        return False


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Admin for role permissions."""

    list_display = [
        "role",
        "can_register",
        "can_collect",
        "can_enter_result",
        "can_verify",
        "can_publish",
        "can_edit_catalog",
        "can_edit_settings",
    ]
    list_filter = ["role"]
