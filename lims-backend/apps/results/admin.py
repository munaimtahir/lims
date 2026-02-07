from django.contrib import admin

from .models import TestResult


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        "order_item",
        "test_parameter",
        "result_value",
        "flag",
        "entered_by",
        "verified_by",
    )
    list_filter = ("flag", "entered_at", "verified_at")
    search_fields = ("order_item__order__order_id", "result_value")
