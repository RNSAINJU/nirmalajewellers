from django import forms
from .models import GoldSilverPurchase, Party, CustomerPurchase, MetalStock, MetalStockType
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


class MetalStockForm(forms.ModelForm):
    stock_type = forms.ModelChoiceField(
        queryset=MetalStockType.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = MetalStock
        fields = [
            'metal_type', 'stock_type', 'purity', 'quantity', 
            'unit_cost', 'location', 'remarks'
        ]
        widgets = {
            'metal_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'purity': forms.Select(attrs={
                'class': 'form-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'Enter quantity in grams'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Cost per gram'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Safe, Almirah, etc.'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this stock'
            }),
        }

    def clean(self):
        cleaned = super().clean()
        quantity = cleaned.get('quantity')
        unit_cost = cleaned.get('unit_cost')

        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        
        if unit_cost and unit_cost < 0:
            raise ValidationError("Unit cost cannot be negative.")

        return cleaned