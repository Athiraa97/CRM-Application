from django import forms
from .models import Customer
from django.contrib.auth.models import User


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'city', 'state', 'country', 'image']

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()



class UserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text='Leave blank to keep existing'
    )

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('team_lead', 'Team Lead'),
        ('user', 'User'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
