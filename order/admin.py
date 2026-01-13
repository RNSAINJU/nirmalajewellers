from django.contrib import admin
from .models import Order, OrderOrnament, OrderPayment, OrderMetalStock


class OrderOrnamentInline(admin.TabularInline):
    model = OrderOrnament
    extra = 0
    fields = (
        'ornament',
        'gold_rate', 'diamond_rate', 'zircon_rate', 'stone_rate',
        'jarti', 'jyala', 'line_amount',
    )
    readonly_fields = ('line_amount',)


class OrderMetalStockInline(admin.TabularInline):
    model = OrderMetalStock
    extra = 0
    fields = (
        'metal_type', 'purity', 'quantity', 'rate_per_gram', 'line_amount', 'remarks'
    )
    readonly_fields = ('line_amount',)


class OrderPaymentInline(admin.TabularInline):
    model = OrderPayment
    extra = 1
    fields = ('payment_mode', 'amount')
    can_delete = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('sn', 'customer_name', 'order_type', 'order_date', 'deliver_date', 'total', 'status')
    list_filter = ('status', 'order_type', 'order_date')
    search_fields = ('sn', 'customer_name', 'phone_number')
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer_name', 'phone_number', 'order_date', 'deliver_date', 'status', 'order_type')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Amounts', {
            'fields': ('amount', 'discount', 'subtotal', 'tax', 'total', 'remaining_amount')
        }),
    )
    inlines = [OrderOrnamentInline, OrderMetalStockInline, OrderPaymentInline]
    readonly_fields = ('amount', 'subtotal', 'total', 'remaining_amount')


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


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_mode', 'amount', 'created_at')
    list_filter = ('payment_mode', 'order__status')
    search_fields = ('order__sn', 'order__customer_name')


@admin.register(OrderMetalStock)
class OrderMetalStockAdmin(admin.ModelAdmin):
    list_display = ('order', 'metal_type', 'purity', 'quantity', 'rate_per_gram', 'line_amount')
    list_filter = ('metal_type', 'purity', 'order__status')
    search_fields = ('order__sn', 'order__customer_name')
    readonly_fields = ('line_amount',)