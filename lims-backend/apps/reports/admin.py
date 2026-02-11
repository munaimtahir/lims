from django.contrib import admin

from .models import Report, ReportExportLog


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("order", "generated_at", "generated_by", "is_final")
    list_filter = ("generated_at", "is_final")
    search_fields = ("order__order_id",)


@admin.register(ReportExportLog)
class ReportExportLogAdmin(admin.ModelAdmin):
    list_display = (
        "report_key",
        "file_format",
        "user",
        "row_count",
        "generated_at",
    )
    list_filter = ("report_key", "file_format", "generated_at")
    search_fields = ("report_key", "user__username")
