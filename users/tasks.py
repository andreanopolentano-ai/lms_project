"""Фоновые задачи приложения users."""

from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from users.models import User


@shared_task
def deactivate_inactive_users() -> int:
    """Батчем блокирует пользователей без входа более месяца."""

    month_ago = timezone.now() - timedelta(days=30)

    inactive_period = (
        Q(last_login__lt=month_ago)
        | Q(
            last_login__isnull=True,
            date_joined__lt=month_ago,
        )
    )

    return (
        User.objects.filter(
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        .filter(inactive_period)
        .update(is_active=False)
    )
