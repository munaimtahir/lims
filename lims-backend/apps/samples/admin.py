from django.contrib import admin
from .models import Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ("id", "order_item", "sample_type", "barcode", "status", "collected_at", "received_at")
    list_filter = ("status", "sample_type", "collected_at", "received_at")
    search_fields = ("barcode", "order_item__order__order_id")
    readonly_fields = ("barcode", "created_at", "updated_at")
