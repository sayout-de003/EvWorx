from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Vehicle, Brand, VehicleType, OnSiteRepairBooking

class SignupForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False)
    is_technician = forms.BooleanField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'phone_number', 'is_technician')

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['model', 'year']

class CartAddForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, initial=1, required=False)
    next = forms.CharField(widget=forms.HiddenInput(), required=False)

class OnSiteRepairBookingForm(forms.ModelForm):
    class Meta:
        model = OnSiteRepairBooking
        fields = [
            'full_name', 'vehicle_type', 'brand', 'model_no', 
            'mobile_no', 'problem_details', 'parts_required', 'address'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Car, Bike'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Tesla, Honda'}),
            'model_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter model number'}),
            'mobile_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'problem_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the problem in detail'}),
            'parts_required': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'List any parts required (optional)'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your full address'}),
        }
