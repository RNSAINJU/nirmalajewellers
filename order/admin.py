from django.contrib import admin
from .models import Order, OrderOrnament


class OrderOrnamentInline(admin.TabularInline):
    model = OrderOrnament
    extra = 0
    fields = (
        'ornament',
        'gold_rate', 'diamond_rate', 'zircon_rate', 'stone_rate',
        'jarti', 'jyala', 'line_amount',
    )
    readonly_fields = ('line_amount',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('sn', 'customer_name', 'order_date', 'deliver_date', 'total', 'status')
    inlines = [OrderOrnamentInline]


@admin.register(OrderOrnament)
class OrderOrnamentAdmin(admin.ModelAdmin):
    list_display = (
        'order', 'ornament',
        'gold_rate', 'diamond_rate', 'zircon_rate', 'stone_rate',
        'jarti', 'jyala', 'line_amount',
    )
    search_fields = (
        'order__sn', 'order__customer_name',
        'ornament__ornament_name', 'ornament__code',
    )
    list_filter = ('order__status', 'ornament__metal_type')