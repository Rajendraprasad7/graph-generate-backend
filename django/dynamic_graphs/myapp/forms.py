from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'organization']
    password1 = forms.CharField(widget=forms.HiddenInput(), required=False)
    password2 = forms.CharField(widget=forms.HiddenInput(), required=False)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password('defaultpassword')  # Set a default or empty password
        if commit:
            user.save()
        return user
# class LoginForm(AuthenticationForm):
#     username = forms.CharField(widget=forms.TextInput())
#     password = forms.CharField(widget=forms.PasswordInput())
