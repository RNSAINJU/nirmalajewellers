from django import forms
from django.core.exceptions import ValidationError
from nepali_datetime_field.forms import NepaliDateField
from decimal import Decimal
from .models import Ornament


class OrnamentForm(forms.ModelForm):

    ornament_date = NepaliDateField(required=False)
    jarti = forms.DecimalField(
        max_digits=10,
        decimal_places=3,
        required=False
    )

    class Meta:
        model = Ornament
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Code is auto-generated
        if 'code' in self.fields:
            self.fields['code'].required = False
            self.fields['code'].widget.attrs.update({
                'class': 'form-control bg-light',
                'placeholder': 'Code (auto-generated)',
            })

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight < 0:
            raise ValidationError("Weight cannot be negative.")
        return weight

    def clean_diamond_weight(self):
        diamond_weight = self.cleaned_data.get('diamond_weight')
        if diamond_weight is not None and diamond_weight < 0:
            raise ValidationError("Stone weight cannot be negative.")
        return diamond_weight

    def clean_jarti(self):
        jarti = self.cleaned_data.get('jarti')

        if jarti in [None, ""]:
            return Decimal("0.000")

        if jarti < 0:
            raise ValidationError("Jarti cannot be negative.")

        return Decimal(jarti)
