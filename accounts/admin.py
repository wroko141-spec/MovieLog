from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PasswordResetToken, User


@admin.register(User)
class MovieLogUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (('MovieLog', {'fields': ('role',)}),)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'used_at')
    readonly_fields = ('token_hash',)
