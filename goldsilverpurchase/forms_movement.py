from django import forms
from .models import MetalStockMovement
from nepali_datetime_field.forms import NepaliDateField

class MetalStockMovementForm(forms.ModelForm):
    movement_date = NepaliDateField(required=False)
    rate = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False, label="Rate (per unit)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter rate for this transaction'})
    )
    class Meta:
        model = MetalStockMovement
        fields = ['movement_type', 'quantity', 'rate', 'notes', 'movement_date']
        widgets = {
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'Quantity in grams'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes for this transaction'}),
        }
