from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Post, Comment

class AccountForm(forms.ModelForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['profile_picture'].initial = self.instance.profile.profile_picture

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
            'id': 'username'
        })

    def save(self, commit=True):
        user = super(AccountForm, self).save(commit=False)
        if commit:
            user.save()
            if 'profile_picture' in self.cleaned_data:
                profile = user.profile
                profile.profile_picture = self.cleaned_data['profile_picture']
                profile.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'id': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'password'
        }),
        required=True
    )


class RegisterForm(UserCreationForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control,'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
            'id': 'username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'password1'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'id': 'password2'
        })


# FORUM MODULE

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
