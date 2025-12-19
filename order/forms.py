from django import forms
from django.forms import inlineformset_factory, ModelMultipleChoiceField
from django.db.models import Q
from .models import Order
from ornament.models import Ornament
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
                self.fields["existing_ornaments"].initial = instance.ornaments.all()
            except Exception:
                # If related name/migrations not ready, fail silently
                pass

        self.fields["existing_ornaments"].queryset = qs

    class Meta:
        model = Order
        fields = [
            'order_date', 'deliver_date', 'customer_name', 'phone_number',
            'amount', 'subtotal', 'discount', 'tax', 'total', 'payment_mode', 'payment_amount',
        ]
        widgets = {
            'amount': forms.HiddenInput(),
            'subtotal': forms.HiddenInput(),
            'discount': forms.HiddenInput(),
            'tax': forms.HiddenInput(),
            'total': forms.HiddenInput(),
        }

    def clean_customer_name(self):
        name = self.cleaned_data.get('customer_name')
        if name and len(name) < 2:
            raise ValidationError("Customer name must be at least 2 characters long.")
        return name

    def clean_payment_amount(self):
        amount = self.cleaned_data.get('payment_amount')
        total = self.cleaned_data.get('total')
        if amount and total and amount > total:
            raise ValidationError("Payment amount cannot exceed total order amount.")
        return amount

    def clean_total(self):
        total = self.cleaned_data.get('total')
        if total is not None and total < Decimal('0'):
            raise ValidationError("Total amount cannot be negative.")
        return total


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