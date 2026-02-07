from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("order", "generated_at", "generated_by", "is_final")
    list_filter = ("generated_at", "is_final")
    search_fields = ("order__order_id",)
