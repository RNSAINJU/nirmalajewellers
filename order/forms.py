from django import forms
from django.forms import inlineformset_factory, ModelMultipleChoiceField
from django.db.models import Q
from .models import Order, OrderMetalStock
from ornament.models import Ornament
from goldsilverpurchase.models import MetalStock
from nepali_datetime_field.forms import NepaliDateField
from django.core.exceptions import ValidationError
from decimal import Decimal

class OrderForm(forms.ModelForm):
    order_date = NepaliDateField(required=False)
    deliver_date = NepaliDateField(required=False)
    
    # Allow selecting existing ornaments
    existing_ornaments = ModelMultipleChoiceField(
        queryset=Ornament.objects.filter(order__isnull=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Existing Ornaments"
    )

    # JSON payload with per-line rates/jarti/jyala/amount from the JS table
    order_lines_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    # JSON payload for multiple payments (mode + amount)
    payment_lines_json = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)

        # By default, only ornaments not attached to any order
        qs = Ornament.objects.filter(order__isnull=True)

        # When editing an order, also include ornaments already linked to it
        if instance and instance.pk:
            qs = Ornament.objects.filter(Q(order__isnull=True) | Q(order=instance))
            # Preselect ornaments already on this order (for server-side validation)
            try:
                # Get ornaments from order_ornaments through table
                self.fields["existing_ornaments"].initial = instance.order_ornaments.values_list('ornament', flat=True)
            except Exception:
                # If related name/migrations not ready, fail silently
                pass

        self.fields["existing_ornaments"].queryset = qs

    class Meta:
        model = Order
        fields = [
            'order_date', 'deliver_date', 'customer_name', 'phone_number', 'status',
            'order_type', 'description', 'amount', 'subtotal', 'discount', 'tax', 'total',
        ]
        widgets = {
            'amount': forms.HiddenInput(),
            'subtotal': forms.HiddenInput(),
            'discount': forms.HiddenInput(),
            'tax': forms.HiddenInput(),
            'total': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'order_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3, 'placeholder': 'Additional notes or description'}),
        }

    def clean_customer_name(self):
        name = self.cleaned_data.get('customer_name')
        if name and len(name) < 2:
            raise ValidationError("Customer name must be at least 2 characters long.")
        return name

    def clean_total(self):
        total = self.cleaned_data.get('total')
        if total is not None and total < Decimal('0'):
            raise ValidationError("Total amount cannot be negative.")
        return total

    def clean(self):
        cleaned = super().clean()
        payment_lines_json = cleaned.get('payment_lines_json')
        print(f"[FORM CLEAN] payment_lines_json received: {repr(payment_lines_json)}")
        print(f"[FORM CLEAN] type: {type(payment_lines_json)}, length: {len(payment_lines_json) if payment_lines_json else 0}")
        if payment_lines_json:
            try:
                import json
                data = json.loads(payment_lines_json)
                print(f"[FORM CLEAN] Parsed JSON: {data}")
            except Exception as e:
                print(f"[FORM CLEAN] Failed to parse JSON: {e}")
        return cleaned


OrnamentFormSet = inlineformset_factory(
    Order,
    Ornament,
    fields=[
        'ornament_date', 'code', 'ornament_name', 'type', 'weight',
        'diamond_weight', 'jarti', 'kaligar', 'ornament_type', 'metal_type',
    ],
    extra=1,
    can_delete=True
)


class OrderMetalStockForm(forms.ModelForm):
    """Form to add raw metal stocks to an order"""
    
    class Meta:
        model = OrderMetalStock
        fields = ['stock_type', 'metal_type', 'purity', 'quantity', 'rate_unit', 'rate_per_gram', 'remarks']
        widgets = {
            'stock_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'metal_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'purity': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
                'placeholder': 'Grams',
                'min': '0'
            }),
            'rate_unit': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'rate_per_gram': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'placeholder': 'Rate per gram',
                'min': '0'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional to allow empty forms in formset
        for field_name in self.fields:
            self.fields[field_name].required = False

    def clean(self):
        cleaned = super().clean()
        quantity = cleaned.get('quantity')
        rate_per_gram = cleaned.get('rate_per_gram')

        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        
        if rate_per_gram and rate_per_gram < 0:
            raise ValidationError("Rate per gram cannot be negative.")

        return cleaned


# Formset for multiple metal stocks in an order
MetalStockFormSet = inlineformset_factory(
    Order,
    OrderMetalStock,
    form=OrderMetalStockForm,
    extra=1,
    can_delete=True,
    fields=['stock_type', 'metal_type', 'purity', 'quantity', 'rate_unit', 'rate_per_gram', 'remarks'],
    min_num=0,
    validate_min=False
)