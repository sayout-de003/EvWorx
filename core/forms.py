from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Vehicle, Brand, VehicleType, OnSiteRepairBooking, Order

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
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Electric Scooter, Electric Car'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Ola, Ather, Tesla'}),
            'model_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., S1 Pro, 450X, Model 3'}),
            'mobile_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'problem_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the problem (e.g., Battery draining fast, Motor noise)'}),
            'parts_required': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'List any parts required (optional, e.g., Brake pads, Mirror)'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your full service address'}),
        }

class AdminOnSiteRepairForm(forms.ModelForm):
    class Meta:
        model = OnSiteRepairBooking
        fields = ['full_name', 'mobile_no', 'vehicle_type', 'brand', 'model_no', 'problem_details', 'parts_required', 'address', 'status', 'admin_notes']
        widgets = {
            field: forms.TextInput(attrs={'class': 'form-control'}) for field in ['full_name', 'mobile_no', 'vehicle_type', 'brand', 'model_no']
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if not isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class AdminOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'tracking_link']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tracking_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional tracking URL'}),
        }
