"""Admin configuration for catalog models."""

from django.contrib import admin

from .models import (
    Parameter,
    ParameterQuickText,
    ReferenceRange,
    Test,
    TestCatalog,
    TestParameter,
)


@admin.register(TestCatalog)
class TestCatalogAdmin(admin.ModelAdmin):
    """Admin for TestCatalog model."""

    list_display = ["code", "name", "category", "price", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["code", "name", "description"]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    """Admin for Parameter model."""

    list_display = ["code", "name", "unit", "data_type", "active"]
    list_filter = ["data_type", "active", "is_calculated"]
    search_fields = ["code", "name", "short_name"]


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Admin for Test model."""

    list_display = [
        "code",
        "name",
        "test_type",
        "department",
        "default_charge",
        "active",
    ]
    list_filter = ["test_type", "department", "active"]
    search_fields = ["code", "name", "short_name"]


class TestParameterInline(admin.TabularInline):
    """Inline for TestParameter model."""

    model = TestParameter
    extra = 0
    fields = ["parameter", "display_order", "is_mandatory", "show_on_report"]


@admin.register(TestParameter)
class TestParameterAdmin(admin.ModelAdmin):
    """Admin for TestParameter model."""

    list_display = [
        "test",
        "parameter",
        "display_order",
        "is_mandatory",
        "show_on_report",
    ]
    list_filter = ["is_mandatory", "show_on_report"]
    search_fields = ["test__code", "test__name", "parameter__code", "parameter__name"]


@admin.register(ReferenceRange)
class ReferenceRangeAdmin(admin.ModelAdmin):
    """Admin for ReferenceRange model."""

    list_display = [
        "parameter",
        "sex",
        "age_min",
        "age_max",
        "normal_low",
        "normal_high",
        "unit",
    ]
    list_filter = ["sex", "age_unit", "population_group"]
    search_fields = ["parameter__code", "parameter__name", "reference_text"]


@admin.register(ParameterQuickText)
class ParameterQuickTextAdmin(admin.ModelAdmin):
    """Admin for ParameterQuickText model."""

    list_display = ["parameter", "template_title", "language", "is_default", "active"]
    list_filter = ["language", "is_default", "active"]
    search_fields = [
        "parameter__code",
        "parameter__name",
        "template_title",
        "template_body",
    ]
