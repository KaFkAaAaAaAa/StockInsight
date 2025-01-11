from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings

class AccountForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['profile_picture'].initial = self.instance.profile.profile_picture

    def save(self, commit=True):
        user = super(AccountForm, self).save(commit=False)
        if commit:
            user.save()
            profile = user.profile
            if 'profile_picture' in self.cleaned_data and self.cleaned_data['profile_picture']:
                profile.profile_picture = self.cleaned_data['profile_picture']
            else:
                profile.profile_picture = 'profile_pictures/default_user_picture.png'
            profile.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

class RegisterForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'profile_picture']