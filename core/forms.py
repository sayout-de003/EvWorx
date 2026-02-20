from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Vehicle, Brand, VehicleType

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
    quantity = forms.IntegerField(min_value=1, initial=1)
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
