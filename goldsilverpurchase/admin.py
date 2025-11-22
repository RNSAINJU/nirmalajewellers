from django.contrib import admin
from .models import GoldSilverPurchase

@admin.register(GoldSilverPurchase)
class GoldSilverPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'bill_no', 'bill_date', 'party_name', 'panno',
        'gold_quantity', 'silver_quantity',
        'rate', 'wages', 'amount', 'payment_mode'
    )
    list_filter = ('payment_mode', 'bill_date')
    search_fields = ('bill_no', 'party_name', 'particular', '=panno')  # exact match for numeric field
