"""Админка приложения users."""

from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройки отображения пользователей в админке."""

    list_display = ("id", "email", "phone", "city", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "city")
    search_fields = ("email", "phone", "city")
    ordering = ("email",)
