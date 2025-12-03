from django import forms
from django.core.exceptions import ValidationError
from nepali_datetime_field.forms import NepaliDateField
from .models import Ornament


class OrnamentForm(forms.ModelForm):
    ornament_date = NepaliDateField(required=False)

    class Meta:
        model = Ornament
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the 'code' field not required and allow blank,
        # Make the 'code' field not required and allow blank both in add and edit mode,
        # and show a placeholder indicating the code is auto-generated

        widgets = {
            'code': forms.NumberInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Code (auto-generated)'}),
        }

        if 'code' in self.fields:
            self.fields['code'].required = False
            self.fields['code'].blank = True  # for docs only, not functional on form field
            self.fields['code'].widget.attrs['placeholder'] = 'Code (auto-generated)'


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