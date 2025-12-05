from django.contrib import admin
from .models import GoldSilverPurchase, Party
from .forms import PurchaseForm, PartyForm

@admin.register(GoldSilverPurchase)
class GoldSilverPurchaseAdmin(admin.ModelAdmin):
    form = PurchaseForm
    
    list_display = ('bill_no', 'party', 'metal_type', 'quantity', 'amount', 'bill_date')
    list_filter = ('metal_type', 'party', 'bill_date')

    fields = (
        'bill_no',
        'bill_date',
        'party',    # <-- add here
        'particular',
        'metal_type',
        'quantity',
        'rate',
        'wages',
        'discount',
        'amount',
        'payment_mode'
    )

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    form = PartyForm

    list_display = ('party_name', 'panno')