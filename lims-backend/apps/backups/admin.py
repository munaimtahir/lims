from django.contrib import admin

from .models import BackupArtifact


@admin.register(BackupArtifact)
class BackupArtifactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "type",
        "status",
        "size_bytes",
        "offsite_provider",
        "offsite_status",
    )
    list_filter = ("type", "status", "offsite_provider", "offsite_status", "created_at")
    search_fields = ("id", "filename", "error_message")
    readonly_fields = ("id", "created_at", "updated_at")
