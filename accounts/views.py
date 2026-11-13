from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import ForgotPasswordForm, LoginForm, NewPasswordForm, RegisterForm
from .models import TOKEN_TTL_MINUTES, PasswordResetToken, User


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('diary')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Добро пожаловать в MovieLog! Найдите фильм в каталоге и добавьте его в дневник.')
        return redirect('catalog')
    return render(request, 'accounts/register.html', {'form': form})


class MovieLogLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


@require_http_methods(['GET', 'POST'])
def forgot_password(request):
    form = ForgotPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            raw_token = PasswordResetToken.create_for(user)
            link = request.build_absolute_uri(reverse('reset_password', args=[raw_token]))
            send_mail(
                'MovieLog: восстановление пароля',
                f'Здравствуйте, {user.username}!\n\n'
                f'Чтобы задать новый пароль, перейдите по ссылке:\n{link}\n\n'
                f'Ссылка действует {TOKEN_TTL_MINUTES} минут и работает один раз.\n'
                'Если вы не запрашивали смену пароля, просто проигнорируйте это письмо.',
                None,
                [user.email],
            )
        # одинаковый ответ, чтобы нельзя было узнать, есть ли такой email в системе
        return render(request, 'accounts/forgot_done.html', {'minutes': TOKEN_TTL_MINUTES})
    return render(request, 'accounts/forgot.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def reset_password(request, token):
    reset = PasswordResetToken.find(token)
    if reset is None or not reset.is_valid():
        return render(request, 'accounts/reset_invalid.html', status=400)
    form = NewPasswordForm(reset.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()  # пароль сохраняется только как хеш
        reset.mark_used()
        messages.success(request, 'Пароль изменён. Теперь войдите с новым паролем.')
        return redirect('login')
    return render(request, 'accounts/reset.html', {'form': form})
