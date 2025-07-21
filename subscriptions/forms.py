from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from .models import Subscription, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm


class SubscriptionForm(forms.ModelForm):
    """Form for creating and updating subscriptions."""
    
    class Meta:
        model = Subscription
        fields = ['service_name', 'price', 'billing_cycle', 'renewal_date']
        widgets = {
            'service_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter service name (e.g., Netflix, Spotify)'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'billing_cycle': forms.Select(attrs={
                'class': 'form-control'
            }),
            'renewal_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
    
    def clean_renewal_date(self):
        """Validate that renewal date is not in the past."""
        renewal_date = self.cleaned_data.get('renewal_date')
        if renewal_date and renewal_date < date.today():
            raise ValidationError("Renewal date cannot be in the past.")
        return renewal_date
    
    def clean_price(self):
        """Validate that price is positive."""
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise ValidationError("Price must be greater than zero.")
        return price
    
    def clean(self):
        """Additional validation logic."""
        cleaned_data = super().clean()
        service_name = cleaned_data.get('service_name')
        
        # Check for duplicate service names for the same user
        if service_name and self.instance.pk is None:  # Only for new subscriptions
            user = getattr(self, 'user', None)
            if user and Subscription.objects.filter(
                user=user, 
                service_name__iexact=service_name
            ).exists():
                raise ValidationError(
                    f"You already have a subscription for '{service_name}'."
                )
        
        return cleaned_data 


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user 


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['reminder_days']
        widgets = {
            'reminder_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
        } 


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        } 