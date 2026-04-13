from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Address, PaymentMethod, UserProfile

User = get_user_model()


class SignUpForm(forms.ModelForm):
    username = forms.CharField(required=False, max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    accept_terms = forms.BooleanField(required=True)

    class Meta:
        model = User
        fields = ('email', 'username')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username and User.objects.filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            self.add_error('password2', 'Passwords do not match.')
        return cleaned_data

    def _build_unique_username(self, email: str) -> str:
        local_part = email.split('@', 1)[0]
        base = ''.join(ch for ch in local_part if ch.isalnum() or ch in {'_', '.'}).strip('._')
        if not base:
            base = 'user'
        base = base[:30]

        username = base
        suffix = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base}{suffix}"
            suffix += 1
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        username = self.cleaned_data.get('username') or self._build_unique_username(email)

        user.email = email
        user.username = username
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False

        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    identifier = forms.CharField(label='Email or Username', max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)
    remember_me = forms.BooleanField(required=False)


class AccountSettingsForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This email is already used by another account.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This username is already used by another account.')
        return username


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('profile_picture',)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            'label',
            'full_name',
            'line1',
            'line2',
            'city',
            'state',
            'postal_code',
            'country',
            'is_default',
        )


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = (
            'method_type',
            'provider',
            'account_name',
            'last4',
            'expiry_month',
            'expiry_year',
            'token_reference',
            'is_default',
        )

    def clean_last4(self):
        last4 = self.cleaned_data.get('last4', '').strip()
        if last4 and (not last4.isdigit() or len(last4) != 4):
            raise ValidationError('Last 4 digits must contain exactly 4 numbers.')
        return last4

    def clean(self):
        cleaned_data = super().clean()
        expiry_month = cleaned_data.get('expiry_month')
        expiry_year = cleaned_data.get('expiry_year')

        if expiry_month and (expiry_month < 1 or expiry_month > 12):
            self.add_error('expiry_month', 'Expiry month must be between 1 and 12.')

        if expiry_year and expiry_year < 2000:
            self.add_error('expiry_year', 'Expiry year is invalid.')

        return cleaned_data
