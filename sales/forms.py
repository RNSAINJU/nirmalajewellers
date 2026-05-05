from django import forms
from django.core.exceptions import ValidationError
import nepali_datetime as ndt

from .models import Sale
from .models import SalesMetalStock
from django.forms import inlineformset_factory


# --- SalesMetalStockForm ---
class SalesMetalStockForm(forms.ModelForm):
    """Form to add raw metal stocks to a sale"""
    class Meta:
        model = SalesMetalStock
        fields = ['stock_type', 'metal_type', 'purity', 'quantity', 'rate_unit', 'rate_per_gram', 'remarks']
        widgets = {
            'stock_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'metal_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'purity': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
                'placeholder': 'Grams',
                'min': '0'
            }),
            'rate_unit': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'rate_per_gram': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'placeholder': 'Rate per gram',
                'min': '0'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional to allow empty forms in formset
        for field_name in self.fields:
            self.fields[field_name].required = False

    def clean(self):
        cleaned = super().clean()
        quantity = cleaned.get('quantity')
        rate_per_gram = cleaned.get('rate_per_gram')

        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        if rate_per_gram and rate_per_gram < 0:
            raise ValidationError("Rate per gram cannot be negative.")
        return cleaned


# --- SalesMetalStockFormSet ---
SalesMetalStockFormSet = inlineformset_factory(
    parent_model=SalesMetalStock._meta.get_field('sale').related_model,
    model=SalesMetalStock,
    form=SalesMetalStockForm,
    extra=1,
    can_delete=True,
    fields=['stock_type', 'metal_type', 'purity', 'quantity', 'rate_unit', 'rate_per_gram', 'remarks'],
    min_num=0,
    validate_min=False
)


class ExcelImportForm(forms.Form):
    """Form for uploading Excel files for sales import."""
    
    excel_file = forms.FileField(
        label='Upload Excel File',
        required=True,
        help_text='Upload an Excel file (.xlsx) with sales data',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control'
        })
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        
        if file:
            # Check file extension
            if not file.name.lower().endswith(('.xlsx', '.xls')):
                raise ValidationError('Only Excel files (.xlsx, .xls) are allowed.')
            
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must not exceed 10MB.')
        
        return file


class SaleUpdateForm(forms.ModelForm):
    """Form for editing sale details with explicit Nepali date input."""

    class Meta:
        model = Sale
        fields = ["bill_no", "sale_date", "pan_number", "address"]
        widgets = {
            "bill_no": forms.TextInput(attrs={"class": "form-control"}),
            "sale_date": forms.TextInput(attrs={"class": "form-control nepali-date", "placeholder": "YYYY-MM-DD (BS)"}),
            "pan_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean_sale_date(self):
        """Accept and normalize Nepali (BS) date from text input."""
        value = self.cleaned_data.get("sale_date")
        if value in (None, ""):
            return None

        # Already parsed by field/widget.
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            return value

        raw = str(value).strip()
        try:
            return ndt.date.fromisoformat(raw)
        except Exception:
            raise ValidationError("Enter a valid Nepali date in YYYY-MM-DD format.")
