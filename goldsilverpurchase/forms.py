from django import forms
from .models import GoldSilverPurchase
from nepali_datetime_field.forms import NepaliDateField
from django.core.exceptions import ValidationError
import nepali_datetime as ndt
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

class PurchaseForm(forms.ModelForm):
    bill_date = NepaliDateField(required=False)         # BS date input widget
    # If you need datetime input, use Django's DateTimeField or create a custom widget/field.

    class Meta:
        model = GoldSilverPurchase
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
