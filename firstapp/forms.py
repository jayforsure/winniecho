from django import forms 
from .models import User, Product, Order, Payment, Member, Address, ProductCategory
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError

class UserRegistrationForm(forms.Form):
    """
    Registration form for new members
    """
    name = forms.CharField(
        max_length=100,
        label='Full Name',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name', 'class': 'form-control'})
    )

    email = forms.EmailField(
        max_length=100,
        label='Email Address',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'your.email@example.com', 'class': 'form-control'})
    )

    phone = forms.CharField(
        max_length=20,
        label='Phone Number',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '+60 12-345 6789', 'class': 'form-control'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Minimum 6 characters', 'class': 'form-control'}),
        label='Password',
        required=True,
        min_length=6
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Re-enter password', 'class': 'form-control'}),
        label='Confirm Password',
        required=True
    )
    
    birthday = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Date of Birth',
        required=True
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')
        
        if User.objects.filter(email=email, type='M').exists():
            raise forms.ValidationError('This email is already registered. Please login.')
        
        return email
    
    def clean_birthday(self):
        birthday = self.cleaned_data.get('birthday')
        if not birthday:
            raise forms.ValidationError('Date of birth is required.')
        
        today = datetime.today().date()
        min_age_date = today - timedelta(days=18*365.25)
        
        if birthday > min_age_date:
            raise forms.ValidationError('You must be at least 18 years old to register.')
        
        return birthday
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class LoginForm(forms.Form):
    """Login form for members"""
    email = forms.EmailField(
        max_length=100,
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'class': 'form-control'}),
        label='Password'
    )


class AddressForm(forms.ModelForm):
    """Form for managing user address"""
    class Meta:
        model = Address
        fields = ['address', 'city', 'state', 'postal_code', 'country']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Street address', 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'}),
            'state': forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal code', 'class': 'form-control'}),
            'country': forms.TextInput(attrs={'placeholder': 'Country', 'class': 'form-control'}),
        }


class EditProfileForm(forms.Form):
    """Edit profile form for Members"""
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Your full name', 'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com', 'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Your phone number', 'class': 'form-control'})
    )
    birthday = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        self.member_instance = kwargs.pop('member_instance', None)
        super().__init__(*args, **kwargs)
        
        if self.user_instance and self.member_instance:
            self.fields['name'].initial = self.user_instance.name
            self.fields['email'].initial = self.user_instance.email
            self.fields['phone'].initial = self.user_instance.phone
            self.fields['birthday'].initial = self.member_instance.birthday
            
            # Make birthday read-only
            self.fields['birthday'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')

        existing_users = User.objects.filter(email=email, type='M')
        if self.user_instance:
            existing_users = existing_users.exclude(id=self.user_instance.id)
        
        if existing_users.exists():
            raise forms.ValidationError('This email is already registered.')
        
        return email

    def save(self):
        """Update User and Member instances"""
        if not self.user_instance or not self.member_instance:
            raise ValueError("User and Member instances must be provided")
        
        self.user_instance.name = self.cleaned_data['name']
        self.user_instance.email = self.cleaned_data['email']
        self.user_instance.phone = self.cleaned_data['phone']
        self.user_instance.save()
        
        return self.user_instance


class ChangePasswordForm(forms.Form):
    """Change password form"""
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter current password', 'class': 'form-control'}),
        required=True
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password', 'class': 'form-control'}),
        required=True
    )
    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password', 'class': 'form-control'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        self.member_instance = kwargs.pop('member_instance', None)
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        
        if not self.member_instance:
            raise forms.ValidationError("Member not found.")
        
        if not check_password(current_password, self.member_instance.password):
            raise forms.ValidationError("Current password is incorrect.")
        
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords do not match.")
            
            if len(new_password) < 6:
                raise forms.ValidationError("Password must be at least 6 characters.")
        
        return cleaned_data

    def save(self):
        """Save new password"""
        if not self.member_instance:
            raise ValueError("Member instance must be provided")
        
        new_password = self.cleaned_data['new_password']
        self.member_instance.password = make_password(new_password)
        self.member_instance.save()
        
        return self.member_instance


class PaymentForm(forms.Form):
    """Payment method selection form"""
    payment_choices = [
        ('PP', 'PayPal'),
        ('ST', 'Credit/Debit Card (Stripe)'),
        ('COD', 'Cash on Delivery')
    ]

    payment_method = forms.ChoiceField(
        choices=payment_choices,
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'}),
        label='Select Payment Method'
    )


class CheckoutForm(forms.Form):
    """Checkout form with address and optional points redemption"""
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Street address', 'class': 'form-control'}),
        required=True
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'}),
        required=True
    )
    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-control'}),
        required=True
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Postal code', 'class': 'form-control'}),
        required=True
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Country', 'class': 'form-control'}),
        initial='Malaysia',
        required=True
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Special instructions (optional)', 'class': 'form-control'}),
        required=False
    )
    use_loyalty_points = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'class': 'form-control'}),
        label='Redeem Points (1 point = RM 1)'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.max_points = kwargs.pop('max_points', 0)
        super().__init__(*args, **kwargs)
        
        # Pre-fill address if user has one
        if self.user:
            try:
                address = self.user.address
                self.fields['address'].initial = address.address
                self.fields['city'].initial = address.city
                self.fields['state'].initial = address.state
                self.fields['postal_code'].initial = address.postal_code
                self.fields['country'].initial = address.country
            except:
                pass

    def clean_use_loyalty_points(self):
        points = self.cleaned_data.get('use_loyalty_points', 0)
        if points and points > self.max_points:
            raise forms.ValidationError(f'You only have {self.max_points} points available.')
        return points or 0


class ForgotPasswordForm(forms.Form):
    """Forgot password form"""
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'})
    )


class ResetPasswordForm(forms.Form):
    """Reset password form"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New password', 'class': 'form-control'}),
        label="New Password",
        min_length=6
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password', 'class': 'form-control'}),
        label="Confirm Password"
    )

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        password_confirm = cleaned.get("password_confirm")
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Passwords do not match.")
            if len(password) < 6:
                raise forms.ValidationError("Password must be at least 6 characters.")
        
        return cleaned


class GuestCheckoutForm(forms.Form):
    """Guest checkout form (includes user info + address)"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Full name', 'class': 'form-control'}),
        required=True
    )
    email = forms.EmailField(
        max_length=100,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address', 'class': 'form-control'}),
        required=True
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number', 'class': 'form-control'}),
        required=True
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Street address', 'class': 'form-control'}),
        required=True
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'}),
        required=True
    )
    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-control'}),
        required=True
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Postal code', 'class': 'form-control'}),
        required=True
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Country', 'class': 'form-control'}),
        initial='Malaysia',
        required=True
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Special instructions (optional)', 'class': 'form-control'}),
        required=False
    )