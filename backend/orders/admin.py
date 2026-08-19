from django.contrib import admin

from .models import Order, OrderItem, OrderItemModifierRemoval


class OrderItemModifierRemovalInline(admin.TabularInline):
    model = OrderItemModifierRemoval
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["menu_item", "quantity", "unit_price", "note"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "table", "status", "opened_by", "opened_at", "total"]
    list_filter = ["status"]
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "menu_item", "quantity", "unit_price"]
    inlines = [OrderItemModifierRemovalInline]
