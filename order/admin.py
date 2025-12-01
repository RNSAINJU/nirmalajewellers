from django.contrib import admin
from .models import Order, Ornament

class OrnamentInline(admin.TabularInline):
    model = Ornament
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('sn', 'customer_name', 'order_date', 'deliver_date', 'total', 'status')
    inlines = [OrnamentInline]

@admin.register(Ornament)
class OrnamentAdmin(admin.ModelAdmin):
    list_display = ('ornament_name', 'metal_type', 'weight', 'rate', 'total', 'order')
