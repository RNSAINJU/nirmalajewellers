from django import forms
from .models import MetalStockMovement
from nepali_datetime_field.forms import NepaliDateField

class MetalStockMovementForm(forms.ModelForm):
    movement_date = NepaliDateField(required=False)
    rate = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False, label="Rate (per unit)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter rate for this transaction'})
    )
    kaligar = forms.ModelChoiceField(
        queryset=MetalStockMovement._meta.get_field('kaligar').related_model.objects.all(),
        required=False,
        label="Kaligar (optional)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Kaligar involved in this transaction (if any)"
    )
    class Meta:
        model = MetalStockMovement
        fields = ['movement_type', 'quantity', 'rate', 'kaligar', 'notes', 'movement_date']
        widgets = {
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'Quantity in grams'}),
            'kaligar': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes for this transaction'}),
        }
