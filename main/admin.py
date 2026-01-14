from django.contrib import admin
from .models import Stock, DailyRate

@admin.register(DailyRate)
class DailyRateAdmin(admin.ModelAdmin):
    list_display = ['bs_date', 'gold_rate', 'gold_rate_10g', 'silver_rate', 'silver_rate_10g', 'get_created_at']
    list_filter = ['bs_date', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Date', {
            'fields': ('bs_date',)
        }),
        ('Rates (per tola)', {
            'fields': ('gold_rate', 'silver_rate')
        }),
        ('Rates (per 10g)', {
            'fields': ('gold_rate_10g', 'silver_rate_10g')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_created_at(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    get_created_at.short_description = 'Created'


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['year', 'diamond', 'gold', 'silver', 'jardi', 'wages', 'get_updated_at']
    fieldsets = (
        ('Fiscal Year', {
            'fields': ('year',)
        }),
        ('Stock Quantities (grams)', {
            'fields': ('diamond', 'gold', 'silver')
        }),
        ('Stock Amounts (currency)', {
            'fields': ('jardi', 'wages')
        }),
        ('Rates (per gram)', {
            'fields': ('diamond_rate', 'gold_rate', 'silver_rate'),
            'description': 'Enter rates to calculate opening stock amounts'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_updated_at(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M')
    get_updated_at.short_description = 'Last Updated'
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of Stock records."""
        return True
