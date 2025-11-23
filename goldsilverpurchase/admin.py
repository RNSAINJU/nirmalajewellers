from django.contrib import admin
from .models import GoldSilverPurchase
from .forms import PurchaseForm
from common.nepali_utils import ad_to_bs_date_str, ad_to_bs_datetime_str

@admin.register(GoldSilverPurchase)
class GoldSilverPurchaseAdmin(admin.ModelAdmin):
    form = PurchaseForm

    list_display = ('bill_no', 'bill_date_bs', 'party_name', 'panno',
                    'metal_type', 'quantity', 'rate', 'wages', 'amount', 'payment_mode')

    def bill_date_bs(self, obj):
        return ad_to_bs_date_str(obj.bill_date)
    bill_date_bs.short_description = 'Bill Date (BS)'
