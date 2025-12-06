from django.contrib import admin
from .models import SampleCollection


@admin.register(SampleCollection)
class SampleCollectionAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "sample_type", "barcode", "status", "collected_at")
    list_filter = ("status", "sample_type", "collected_at")
    search_fields = ("barcode", "order__order_id")
    filter_horizontal = ("order_items",)
