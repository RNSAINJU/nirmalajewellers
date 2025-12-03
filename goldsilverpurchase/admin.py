from django.contrib import admin
from .models import GoldSilverPurchase
from .forms import PurchaseForm

@admin.register(GoldSilverPurchase)
class GoldSilverPurchaseAdmin(admin.ModelAdmin):
    form = PurchaseForm

    list_display = ('bill_no', 'bill_date', 'party_name', 'panno',
                    'metal_type', 'quantity', 'rate', 'wages', 'amount', 'payment_mode')

