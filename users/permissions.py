"""Права доступа к профилям пользователей."""

from rest_framework.permissions import BasePermission


class IsSelf(BasePermission):
    """Разрешает изменение или удаление только своего профиля."""

    message = "Редактировать или удалять можно только собственный профиль."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.pk == request.user.pk
