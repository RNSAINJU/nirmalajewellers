from django.contrib import admin
from .models import Stock, DailyRate, CustomerCampaignContact, CampaignMessageLog

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


@admin.register(CustomerCampaignContact)
class CustomerCampaignContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'birthday', 'is_active', 'whatsapp_opt_in', 'sms_opt_in', 'source']
    list_filter = ['is_active', 'whatsapp_opt_in', 'sms_opt_in', 'source']
    search_fields = ['name', 'phone_number']


@admin.register(CampaignMessageLog)
class CampaignMessageLogAdmin(admin.ModelAdmin):
    list_display = ['campaign_type', 'channel', 'recipient_phone', 'status', 'created_at', 'sent_at']
    list_filter = ['campaign_type', 'channel', 'status', 'created_at']
    search_fields = ['recipient_phone', 'recipient_name', 'provider_message_id']
    readonly_fields = ['campaign_type', 'channel', 'recipient_name', 'recipient_phone', 'message_body', 'status', 'provider_message_id', 'error_message', 'related_order', 'created_at', 'sent_at']
