from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm


class UserCreateForm(UserCreationForm):
    """Form for creating new users with role assignment."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Roles',
        help_text='Select one or more roles for this user'
    )
    is_staff = forms.BooleanField(
        required=False,
        label='Staff Status',
        help_text='Designates whether the user can log into this admin site.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Active',
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'groups', 'is_staff', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters.'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = self.cleaned_data.get('is_staff', False)
        user.is_active = self.cleaned_data.get('is_active', True)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data['groups'])
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Roles',
        help_text='Select one or more roles for this user'
    )
    is_staff = forms.BooleanField(
        required=False,
        label='Staff Status',
        help_text='Designates whether the user can log into this admin site.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_active = forms.BooleanField(
        required=False,
        label='Active',
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'groups', 'is_staff', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data['groups'])
        return user


class UserPasswordChangeForm(SetPasswordForm):
    """Form for changing user password."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})


class GroupForm(forms.ModelForm):
    """Form for creating and editing roles/groups."""
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Enter a unique role name (e.g., Manager, Cashier, Sales Person)'
    )

    class Meta:
        model = Group
        fields = ('name',)
