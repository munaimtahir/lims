"""Admin configuration for core models."""

from django.contrib import admin

from .models import LabTerminal


@admin.register(LabTerminal)
class LabTerminalAdmin(admin.ModelAdmin):
    """Admin interface for LabTerminal."""

    list_display = [
        "code",
        "name",
        "offline_range_start",
        "offline_range_end",
        "offline_current",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["code", "name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Terminal Information",
            {
                "fields": ("code", "name", "is_active"),
            },
        ),
        (
            "Offline Range Configuration",
            {
                "fields": (
                    "offline_range_start",
                    "offline_range_end",
                    "offline_current",
                ),
                "description": (
                    "Configure the MRN range this terminal uses when offline. "
                    "Current shows the last allocated number (0 = range not yet used)."
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
