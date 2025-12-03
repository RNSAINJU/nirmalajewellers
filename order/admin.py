from django.contrib import admin
from .models import Order
from ornament.models import Ornament


class OrnamentInline(admin.TabularInline):
    model = Ornament
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('sn', 'customer_name', 'order_date', 'deliver_date', 'total', 'status')
    inlines = [OrnamentInline]
