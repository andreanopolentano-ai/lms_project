"""Права доступа к курсам и урокам."""

from rest_framework.permissions import BasePermission

MODERATOR_GROUP_NAME = "Модераторы"


def user_is_moderator(user) -> bool:
    """Проверяет, входит ли пользователь в группу модераторов."""

    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name=MODERATOR_GROUP_NAME).exists()
    )


class IsModerator(BasePermission):
    """Разрешает доступ только модераторам."""

    message = "Доступ разрешен только модераторам."

    def has_permission(self, request, view) -> bool:
        return user_is_moderator(request.user)

    def has_object_permission(self, request, view, obj) -> bool:
        return user_is_moderator(request.user)


class IsNotModerator(BasePermission):
    """Запрещает создание и удаление объектов модераторам."""

    message = "Модераторы не могут создавать и удалять курсы или уроки."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and not user_is_moderator(request.user)
        )


class IsOwner(BasePermission):
    """Разрешает работу только владельцу объекта."""

    message = "Вы не являетесь владельцем этого объекта."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.owner_id == request.user.id


class IsModeratorOrOwner(BasePermission):
    """Разрешает доступ модератору или владельцу объекта."""

    message = "Доступ разрешен только владельцу объекта или модератору."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        return (
            user_is_moderator(request.user)
            or obj.owner_id == request.user.id
        )
