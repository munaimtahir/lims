from django.contrib import admin

from .models import Test, TestCategory, TestPanel, TestParameter


class TestParameterInline(admin.TabularInline):
    model = TestParameter
    fields = (
        "parameter",
        "display_order",
        "is_required_for_verification",
        "is_printable",
        "value_source",
        "default_value",
    )
    extra = 1


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name",)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("test_code", "test_name", "category", "price", "is_active")
    list_filter = ("category", "is_active", "print_group")
    search_fields = ("test_code", "test_name", "loinc_code")
    fieldsets = (
        (None, {"fields": ("test_code", "test_name", "category", "price", "is_active")}),
        ("Sample & TAT", {"fields": ("sample_type", "sample_volume", "turnaround_time", "instructions")}),
        ("Printing Rules", {
            "fields": (
                "print_group",
                "print_priority",
                "force_separate_page",
                "omit_blank_parameters",
                "print_if_any_result_present",
                "footer_comments_static",
            )
        }),
    )
    inlines = [TestParameterInline]


@admin.register(TestPanel)
class TestPanelAdmin(admin.ModelAdmin):
    list_display = ("panel_code", "panel_name", "category", "price", "is_active")
    list_filter = ("category", "is_active", "print_group")
    search_fields = ("panel_code", "panel_name")
    filter_horizontal = ("tests",)
    fieldsets = (
        (None, {"fields": ("panel_code", "panel_name", "category", "price", "is_active")}),
        ("Composition", {"fields": ("tests", "description")}),
        ("Sample & TAT", {"fields": ("sample_type", "sample_volume", "turnaround_time")}),
        ("Printing Rules", {
            "fields": (
                "print_group",
                "print_priority",
                "force_separate_page",
                "omit_blank_parameters",
                "print_if_any_result_present",
                "footer_comments_static",
            )
        }),
    )


@admin.register(TestParameter)
class TestParameterAdmin(admin.ModelAdmin):
    list_display = (
        "test",
        "parameter",
        "display_order",
        "is_required_for_verification",
        "value_source",
    )
    list_filter = ("value_source", "is_required_for_verification", "is_printable")
    search_fields = (
        "test__test_name",
        "parameter__name",
        "parameter__short_name",
    )
