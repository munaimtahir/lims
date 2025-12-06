from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_id",
        "patient",
        "status",
        "total_amount",
        "is_paid",
        "created_at",
    )
    list_filter = ("status", "is_paid", "created_at")
    search_fields = ("order_id", "patient__first_name", "patient__last_name")
    inlines = [OrderItemInline]
    readonly_fields = ("order_id", "total_amount", "net_amount")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "test", "panel", "price", "status")
    list_filter = ("status",)
    search_fields = ("order__order_id",)
