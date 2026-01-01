from django import forms
from .models import Stock


class StockForm(forms.ModelForm):
    """Form for adding/editing stock details manually."""
    
    class Meta:
        model = Stock
        fields = [
            'year',
            'diamond',
            'gold',
            'silver',
            'jardi',
            'wages',
            'diamond_rate',
            'gold_rate',
            'silver_rate',
        ]
        widgets = {
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2082',
                'min': 2000,
                'max': 2100,
            }),
            'diamond': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'in grams (e.g., 100.000)',
                'step': '0.001',
            }),
            'gold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'in grams (e.g., 500.000)',
                'step': '0.001',
            }),
            'silver': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'in grams (e.g., 1000.000)',
                'step': '0.001',
            }),
            'jardi': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'in currency (e.g., 50000.00)',
                'step': '0.01',
            }),
            'wages': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'in currency (e.g., 10000.00)',
                'step': '0.01',
            }),
            'diamond_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'per gram (e.g., 5000.00)',
                'step': '0.01',
            }),
            'gold_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'per gram (e.g., 8000.00)',
                'step': '0.01',
            }),
            'silver_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'per gram (e.g., 1000.00)',
                'step': '0.01',
            }),
        }
        labels = {
            'year': 'Fiscal Year',
            'diamond': 'Diamond Stock (grams)',
            'gold': 'Gold Stock (grams)',
            'silver': 'Silver Stock (grams)',
            'jardi': 'Jardi (रू)',
            'wages': 'Wages (रू)',
            'diamond_rate': 'Diamond Rate (per gram) (रू)',
            'gold_rate': 'Gold Rate (per gram) (रू)',
            'silver_rate': 'Silver Rate (per gram) (रू)',
        }
