from django.contrib import admin

from .models import Ornament


@admin.register(Ornament)
class OrnamentAdmin(admin.ModelAdmin):
    list_display = ('code', 'ornament_name', 'type', 'weight', 'diamond_weight', 'ornament_type', 'customer_name', 'ornament_date')
    list_filter = ('type', 'ornament_type')
    search_fields = ('code', 'ornament_name', 'customer_name')
    ordering = ('-ornament_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')

