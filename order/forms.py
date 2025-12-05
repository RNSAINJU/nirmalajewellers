from django import forms
from django.forms import inlineformset_factory
from .models import Order
from ornament.models import Ornament
import nepali_datetime as ndt
from nepali_datetime_field.forms import NepaliDateField
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

class OrderForm(forms.ModelForm):
    
    bill_date = NepaliDateField(required=False) 
    class Meta:
        model = Order
        fields = '__all__'

    def clean_bill_date(self):
        v = self.cleaned_data.get('bill_date')
        if not v:
            return v
        try:
            ndt.date.from_datetime_date(v)  # check range
        except (OverflowError, ValueError):
            raise ValidationError("Selected date is outside supported Nepali range.")
        return v


OrnamentFormSet = modelformset_factory(
    Ornament,
    fields=[
        'ornament_date', 'code', 'ornament_name', 'type', 'weight',
        'diamond_weight', 'jarti', 'kaligar', 'ornament_type', 'customer_name'
    ],
    extra=1,
    can_delete=True
)