"""Простая проверка состояния приложения для CI/CD."""

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Возвращает состояние приложения и версию Docker-образа."""

    return JsonResponse(
        {
            "status": "ok",
            "version": settings.APP_VERSION,
        }
    )
