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
    list_filter = ("category", "is_active")
    search_fields = ("test_code", "test_name", "loinc_code")
    inlines = [TestParameterInline]


@admin.register(TestPanel)
class TestPanelAdmin(admin.ModelAdmin):
    list_display = ("panel_code", "panel_name", "category", "price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("panel_code", "panel_name")
    filter_horizontal = ("tests",)


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
