from django import forms
from .models import GoldSilverPurchase
from nepali_datetime_field.forms import NepaliDateField
from django.core.exceptions import ValidationError
import nepali_datetime as ndt

class PurchaseForm(forms.ModelForm):
    bill_date = NepaliDateField(required=False)         # BS date input widget
    # If you need datetime input, use Django's DateTimeField or create a custom widget/field.

    class Meta:
        model = GoldSilverPurchase
        fields = '__all__'


