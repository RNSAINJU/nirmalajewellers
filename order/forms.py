from django import forms
from django.forms import inlineformset_factory
from .models import Order, Ornament
import nepali_datetime as ndt
from nepali_datetime_field.forms import NepaliDateField
from django.core.exceptions import ValidationError

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


class OrnamentForm(forms.ModelForm):
    class Meta:
        model = Ornament
        fields = ('ornament_name', 'metal_type', 'weight', 'jarti', 'jyala', 'rate', 'size', 'stone', 'total')
        widgets = {
            'weight': forms.NumberInput(attrs={'step': '0.001'}),
            'jyala': forms.NumberInput(attrs={'step': '0.001'}),
            'rate': forms.NumberInput(attrs={'step': '0.01'}),
            'total': forms.NumberInput(attrs={'step': '0.01'}),
        }

OrnamentFormSet = inlineformset_factory(
    Order, Ornament,
    form=OrnamentForm,
    extra=1, can_delete=True, min_num=1, validate_min=True
)