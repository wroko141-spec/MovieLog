import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Пользователь сайта. Пароль хранится только в виде хеша (поле password)."""

    ROLE_USER = 'user'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_USER, 'Пользователь'),
        (ROLE_ADMIN, 'Администратор'),
    ]

    email = models.EmailField('Email', max_length=150, unique=True)
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=['user', 'admin']),
                name='ck_users_role',
            ),
        ]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def save(self, *args, **kwargs):
        # администратор получает доступ к панели управления Django
        if self.role == self.ROLE_ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)


TOKEN_TTL_MINUTES = 30


class PasswordResetToken(models.Model):
    """Одноразовый токен для восстановления пароля по email."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reset_tokens',
        verbose_name='Пользователь',
    )
    token_hash = models.CharField('Хеш токена', max_length=64, unique=True)
    expires_at = models.DateTimeField('Действует до')
    used_at = models.DateTimeField('Использован', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'password_reset_token'
        indexes = [models.Index(fields=['expires_at'], name='idx_prt_expires')]

    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])

    @staticmethod
    def make_hash(raw_token):
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @classmethod
    def create_for(cls, user):
        """Создаёт токен и возвращает его в открытом виде (уходит в письмо, в базе не хранится)."""
        raw_token = secrets.token_urlsafe(32)
        # старые неиспользованные ссылки этого пользователя перестают работать
        cls.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
        cls.objects.create(
            user=user,
            token_hash=cls.make_hash(raw_token),
            expires_at=timezone.now() + timedelta(minutes=TOKEN_TTL_MINUTES),
        )
        return raw_token

    @classmethod
    def find(cls, raw_token):
        return cls.objects.filter(token_hash=cls.make_hash(raw_token)).first()
