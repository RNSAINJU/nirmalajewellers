from django import forms
from .models import GoldSilverPurchase, Party, CustomerPurchase
from nepali_datetime_field.forms import NepaliDateField
from django.core.exceptions import ValidationError
from decimal import Decimal
import nepali_datetime as ndt

class PurchaseForm(forms.ModelForm):
    bill_date = NepaliDateField(required=False)         # BS date input widget
    # If you need datetime input, use Django's DateTimeField or create a custom widget/field.

    class Meta:
        model = GoldSilverPurchase
        fields = '__all__'


class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = '__all__'


class CustomerPurchaseForm(forms.ModelForm):
    purchase_date = NepaliDateField(required=False)

    class Meta:
        model = CustomerPurchase
        fields = [
            'sn', 'purchase_date', 'customer_name', 'location',
            'phone_no', 'metal_type', 'ornament_name', 'weight', 'percentage', 'final_weight', 'refined_weight', 'rate', 'amount'
        ]

    def clean(self):
        cleaned = super().clean()
        weight = cleaned.get('weight') or Decimal('0')
        rate = cleaned.get('rate') or Decimal('0')
        amount = cleaned.get('amount')

        if amount in (None, ''):
            cleaned['amount'] = (weight * rate).quantize(Decimal('0.01')) if weight and rate else Decimal('0.00')

        return cleaned