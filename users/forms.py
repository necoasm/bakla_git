from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Kullanıcı adı',
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded'})
    )
    password = forms.CharField(
        label='Şifre',
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded'})
    )
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('profile_picture', 'bio', 'first_name', 'last_name')
