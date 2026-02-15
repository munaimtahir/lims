"""Admin interface for core models."""
from django.contrib import admin

from .models import (
    Branch,
    CollectionCenter,
    LabDailyCounter,
    LabTerminal,
    OrderIdSequence,
    PrintTemplate,
    RegistrationCounter,
    SystemSettings,
    Tenant,
    TenantMrnSequence,
    TenantSettings,
)


@admin.register(CollectionCenter)
class CollectionCenterAdmin(admin.ModelAdmin):
    """Admin for Collection Centers."""

    list_display = ["code", "name", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["code", "name", "address"]
    ordering = ["code"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(RegistrationCounter)
class RegistrationCounterAdmin(admin.ModelAdmin):
    """Admin for Registration Counters (read-only for safety)."""

    list_display = ["yymm", "center", "last_value", "updated_at"]
    list_filter = ["center", "yymm"]
    search_fields = ["yymm", "center__name"]
    ordering = ["-yymm", "center"]
    readonly_fields = ["yymm", "center", "last_value", "updated_at"]

    def has_add_permission(self, request):
        """Prevent manual creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion."""
        return False


@admin.register(LabDailyCounter)
class LabDailyCounterAdmin(admin.ModelAdmin):
    """Admin for Lab Daily Counters (read-only for safety)."""

    list_display = ["date", "center", "last_value", "updated_at"]
    list_filter = ["center", "date"]
    search_fields = ["center__name"]
    ordering = ["-date", "center"]
    readonly_fields = ["date", "center", "last_value", "updated_at"]

    def has_add_permission(self, request):
        """Prevent manual creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion."""
        return False


@admin.register(LabTerminal)
class LabTerminalAdmin(admin.ModelAdmin):
    """Admin for Lab Terminals."""

    list_display = ["name", "location", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "location"]
    ordering = ["name"]


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin for System Settings."""

    fieldsets = (
        (
            "Lab Information",
            {
                "fields": (
                    "lab_name",
                    "lab_display_name",
                    "lab_address",
                    "lab_phone",
                    "lab_email",
                    "lab_logo",
                )
            },
        ),
        (
            "Report Customization",
            {
                "fields": (
                    "report_header",
                    "report_footer",
                    "report_header_image",
                    "report_footer_image",
                )
            },
        ),
        ("Financial Settings", {"fields": ("currency", "tax_rate")}),
        (
            "Email Configuration",
            {
                "fields": (
                    "email_host",
                    "email_port",
                    "email_use_tls",
                    "email_use_ssl",
                    "email_host_user",
                    "email_host_password",
                    "email_from",
                )
            },
        ),
        ("Backup Settings", {"fields": ("backup_enabled", "backup_frequency")}),
        (
            "Metadata",
            {"fields": ("updated_at", "updated_by"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ["updated_at", "updated_by"]

    def has_add_permission(self, request):
        """Only allow one settings instance."""
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings."""
        return False


@admin.register(PrintTemplate)
class PrintTemplateAdmin(admin.ModelAdmin):
    """Admin for Print Templates."""

    list_display = ["template_key", "type", "name", "is_active", "created_at"]
    list_filter = ["type", "is_active", "created_at"]
    search_fields = ["template_key", "name", "description"]
    ordering = ["type", "name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "updated_at"]
    search_fields = ["code", "name"]
    list_filter = ["is_active"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["tenant", "code", "name", "capability_mode", "is_hq", "is_active"]
    list_filter = ["tenant", "capability_mode", "is_active", "is_hq"]
    search_fields = ["code", "name", "tenant__code", "tenant__name"]
    ordering = ["tenant__code", "code"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(OrderIdSequence)
class OrderIdSequenceAdmin(admin.ModelAdmin):
    list_display = ["tenant", "branch", "date", "last_seq", "updated_at"]
    list_filter = ["tenant", "branch", "date"]
    readonly_fields = ["updated_at"]


@admin.register(TenantMrnSequence)
class TenantMrnSequenceAdmin(admin.ModelAdmin):
    list_display = ["tenant", "year_suffix", "last_seq", "updated_at"]
    list_filter = ["tenant", "year_suffix"]
    readonly_fields = ["updated_at"]


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "tenant",
        "enable_collection_centers",
        "sample_workflow_enabled",
        "default_branch",
        "default_collection_center",
        "updated_at",
        "updated_by",
    ]
    list_filter = ["enable_collection_centers", "sample_workflow_enabled", "tenant"]
    raw_id_fields = ["default_branch", "default_collection_center"]
    readonly_fields = ["created_at", "updated_at"]
