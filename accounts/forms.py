from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email', max_length=150)

    class Meta:
        model = User
        fields = ('username', 'email')
        labels = {'username': 'Логин'}

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин или email', max_length=150)

    def clean(self):
        # разрешаем входить и по email
        login = (self.cleaned_data.get('username') or '').strip()
        if '@' in login:
            user = User.objects.filter(email__iexact=login).first()
            if user:
                self.cleaned_data['username'] = user.username
        return super().clean()


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Email, указанный при регистрации', max_length=150)


class NewPasswordForm(SetPasswordForm):
    pass
