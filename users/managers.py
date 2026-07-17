"""Менеджер кастомной модели пользователя."""

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Менеджер пользователя с авторизацией по email."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        """Создает пользователя с email и паролем."""
        if not email:
            raise ValueError("Email должен быть указан.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Создает обычного пользователя."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        """Создает суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
