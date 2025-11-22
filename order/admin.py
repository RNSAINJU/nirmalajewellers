from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('sn', 'customer_name', 'order_date', 'deliver_date', 'total', 'payment_mode', 'metal_type', 'status')
    list_filter = ('status', 'payment_mode', 'metal_type')
    search_fields = ('customer_name', 'ornament_name')
