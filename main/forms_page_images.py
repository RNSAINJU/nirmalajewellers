from django import forms

from .models import CustomerPageImage


class CustomerPageImageForm(forms.ModelForm):
    class Meta:
        model = CustomerPageImage
        fields = [
            'image',
            'tagline',
            'title',
            'button_text',
            'is_active',
        ]
        widgets = {
            'tagline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'The Eternal Sparkle',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Antique Gold Collections',
            }),
            'button_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shop Collection',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.is_logo_slot:
            for field_name in ('tagline', 'title', 'button_text'):
                self.fields.pop(field_name, None)
            self.fields['image'].help_text = 'PNG with transparent background works best. Recommended height: 80–120 px.'
