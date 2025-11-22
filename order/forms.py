from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'deliver_date': forms.DateInput(attrs={'type': 'date'}),
        }