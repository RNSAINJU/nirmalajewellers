from django import forms
from .models import Stock, DailyRate


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
            'gold_silver_rate_unit',
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
            'gold_silver_rate_unit': forms.Select(attrs={
                'class': 'form-control',
            }),
            'gold_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 8000.00',
                'step': '0.01',
            }),
            'silver_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1000.00',
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
            'gold_silver_rate_unit': 'Gold & Silver Rate Unit',
            'gold_rate': 'Gold Rate (रू)',
            'silver_rate': 'Silver Rate (रू)',
        }

class DailyRateForm(forms.ModelForm):
    """Form for entering today's gold and silver rates."""
    
    class Meta:
        model = DailyRate
        fields = ['bs_date', 'gold_rate', 'silver_rate']
        widgets = {
            'bs_date': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Nepali date (e.g., 29 Poush 2082)',
                'required': False,
            }),
            'gold_rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Gold rate per tola (रू)',
                'step': '0.01',
                'required': True,
            }),
            'silver_rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Silver rate per tola (रू)',
                'step': '0.01',
                'required': True,
            }),
        }
        labels = {
            'bs_date': 'Nepali Date',
            'gold_rate': 'Gold Rate (per Tola)',
            'silver_rate': 'Silver Rate (per Tola)',
        }