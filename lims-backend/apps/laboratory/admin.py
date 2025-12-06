from django.contrib import admin
from .models import TestCategory, Test, TestParameter, TestPanel


class TestParameterInline(admin.TabularInline):
    model = TestParameter
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
