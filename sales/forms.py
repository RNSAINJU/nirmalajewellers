from django import forms
from django.core.exceptions import ValidationError


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
