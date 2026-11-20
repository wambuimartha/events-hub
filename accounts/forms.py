from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Profile


class SignUpForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="Full Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Martha Wanjiku',
            'class': 'clean-input',
            'autocomplete': 'name',
        })
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'e.g. student@gmail.com',
            'class': 'clean-input',
            'autocomplete': 'email',
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Phone Number (M-Pesa)",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 0712345678',
            'class': 'clean-input',
            'autocomplete': 'tel',
        })
    )

    class Meta:
        model = User
        fields = ('full_name', 'username', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style the default fields
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({
                'class': 'clean-input',
                'placeholder': 'e.g. martha_w',
            })
            self.fields['username'].help_text = 'Letters, digits and @/./+/-/_ only.'

        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'clean-input',
                'placeholder': 'Create password',
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'clean-input',
                'placeholder': 'Confirm password',
            })

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip().replace(' ', '').replace('-', '')
        if len(phone) < 9:
            raise ValidationError("Please provide a valid active phone number.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '').strip()
        parts = full_name.split()
        user.first_name = parts[0] if parts else ''
        user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        user.email = self.cleaned_data.get('email', '').strip().lower()

        if commit:
            user.save()
            phone = self.cleaned_data.get('phone_number', '').strip()
            profile, _ = Profile.objects.update_or_create(user=user, defaults={'phone_number': phone})
            user.profile = profile

        return user
