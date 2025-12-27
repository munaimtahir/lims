from django.contrib import admin
from .models import LabTerminal


@admin.register(LabTerminal)
class LabTerminalAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'offline_range_start', 'offline_range_end', 'offline_current', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['offline_current', 'created_at', 'updated_at']

