from django import forms
from .models import GoldSilverPurchase, Party, CustomerPurchase, MetalStock, MetalStockType
from nepali_datetime_field.forms import NepaliDateField
from django.core.exceptions import ValidationError
from decimal import Decimal
import nepali_datetime as ndt

class PurchaseForm(forms.ModelForm):
    bill_date = NepaliDateField(required=False)
    purity = forms.ChoiceField(
        choices=GoldSilverPurchase.Purity.choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=True
    )
    rate_unit = forms.ChoiceField(
        choices=GoldSilverPurchase.RATE_UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=True,
        initial='tola'
    )

    class Meta:
        model = GoldSilverPurchase
        fields = '__all__'
        widgets = {
            'metal_type': forms.Select(attrs={'class': 'form-control'}),
            'purity': forms.Select(attrs={'class': 'form-control'}),
            'rate_unit': forms.Select(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
        }


class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = '__all__'


class CustomerPurchaseForm(forms.ModelForm):
    purchase_date = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'YYYY-MM-DD (e.g., 2082-09-30)'
        }),
        help_text='Optional: Date in Nepali calendar format'
    )

    class Meta:
        model = CustomerPurchase
        fields = [
            'purchase_date', 'customer_name', 'location',
            'phone_no', 'metal_type', 'ornament_name', 'purity', 'weight', 'percentage', 'final_weight', 'refined_status', 'refined_weight', 'rate', 'rate_unit', 'amount', 'profit_weight', 'profit'
        ]
    
    def clean_purchase_date(self):
        """Parse and validate purchase date - lenient since it's optional"""
        date_str = self.cleaned_data.get('purchase_date')
        
        if not date_str:
            return None
        
        # Accept any YYYY-MM-DD format string without strict validation
        # since field is optional and Nepali calendar has varying month lengths
        return str(date_str).strip()

    def clean(self):
        cleaned = super().clean()
        weight = cleaned.get('weight') or Decimal('0')
        percentage = cleaned.get('percentage') or Decimal('0')
        refined_weight = cleaned.get('refined_weight') or Decimal('0')
        rate = cleaned.get('rate') or Decimal('0')
        rate_unit = cleaned.get('rate_unit') or 'tola'

        # Only calculate final_weight if not already set (i.e., on create)
        if not cleaned.get('final_weight'):
            final_weight = weight - (weight * percentage / Decimal('100'))
            cleaned['final_weight'] = final_weight
        else:
            final_weight = cleaned.get('final_weight')

        # Only calculate amount if not already set (i.e., on create)
        if not cleaned.get('amount'):
            TOLA_TO_GRAM = Decimal('11.6643')
            if rate_unit == 'gram':
                calc_amount = final_weight * rate
            elif rate_unit == '10gram':
                calc_amount = (final_weight / Decimal('10')) * rate
            elif rate_unit == 'tola':
                calc_amount = (final_weight / TOLA_TO_GRAM) * rate
            else:
                calc_amount = Decimal('0.00')
            cleaned['amount'] = calc_amount.quantize(Decimal('0.01')) if calc_amount else Decimal('0.00')

        return cleaned


class MetalStockForm(forms.ModelForm):
    stock_type = forms.ModelChoiceField(
        queryset=MetalStockType.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    # Remove quantity from form fields for manual add, use movement instead
    class Meta:
        model = MetalStock
        fields = [
            'metal_type', 'stock_type', 'purity', 'rate_unit', 'unit_cost', 'location', 'remarks'
        ]
        widgets = {
            'metal_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'purity': forms.Select(attrs={
                'class': 'form-select',
            }),
            'rate_unit': forms.Select(attrs={
                'class': 'form-select',
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

    # Custom field for movement
    add_quantity = forms.DecimalField(
        max_digits=12, decimal_places=3, required=False, label="Add Quantity (grams)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'Enter quantity to add'}),
        initial=None
    )
    movement_notes = forms.CharField(
        required=False, label="Movement Notes",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes for this stock movement'}),
        initial=None
    )

    def clean(self):
        cleaned = super().clean()
        unit_cost = cleaned.get('unit_cost')
        add_quantity = cleaned.get('add_quantity')
        # Only validate add_quantity if provided and not blank
        if add_quantity not in (None, ''):
            if add_quantity < 0:
                raise ValidationError("Add quantity must be zero or positive.")
        if unit_cost not in (None, '') and unit_cost < 0:
            raise ValidationError("Unit cost cannot be negative.")
        return cleaned