"""Контроллеры приложения materials."""

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from materials.models import Course, Lesson
from materials.paginators import CourseLessonPagination
from materials.permissions import (
    IsModeratorOrOwner,
    IsNotModerator,
    IsOwner,
    user_is_moderator,
)
from materials.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(ModelViewSet):
    """CRUD курсов с разграничением прав доступа."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CourseLessonPagination

    def get_queryset(self):
        """Возвращает модератору все курсы, пользователю — только его курсы."""

        queryset = Course.objects.select_related(
            "owner",
        ).prefetch_related(
            "lessons",
            "subscriptions",
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(owner=self.request.user)

    def get_permissions(self):
        """Назначает разрешения в зависимости от действия."""

        if self.action == "create":
            permission_classes = (
                IsAuthenticated,
                IsNotModerator,
            )

        elif self.action == "destroy":
            permission_classes = (
                IsAuthenticated,
                IsNotModerator,
                IsOwner,
            )

        elif self.action in (
            "retrieve",
            "update",
            "partial_update",
        ):
            permission_classes = (
                IsAuthenticated,
                IsModeratorOrOwner,
            )

        else:
            permission_classes = (IsAuthenticated,)

        return [
            permission()
            for permission in permission_classes
        ]

    def perform_create(self, serializer):
        """Назначает владельцем курса текущего пользователя."""

        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(ListCreateAPIView):
    """Получение списка уроков и создание нового урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = CourseLessonPagination

    def get_queryset(self):
        """Возвращает модератору все уроки, пользователю — только его уроки."""

        queryset = Lesson.objects.select_related(
            "course",
            "owner",
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(owner=self.request.user)

    def get_permissions(self):
        """Запрещает модератору создавать уроки."""

        if self.request.method == "POST":
            permission_classes = (
                IsAuthenticated,
                IsNotModerator,
            )
        else:
            permission_classes = (IsAuthenticated,)

        return [
            permission()
            for permission in permission_classes
        ]

    def perform_create(self, serializer):
        """Назначает владельцем урока текущего пользователя."""

        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPIView,
):
    """Получение, обновление и удаление отдельного урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        """Ограничивает доступ к урокам в зависимости от роли пользователя."""

        queryset = Lesson.objects.select_related(
            "course",
            "owner",
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(owner=self.request.user)

    def get_permissions(self):
        """Назначает разрешения в зависимости от HTTP-метода."""

        if self.request.method == "DELETE":
            permission_classes = (
                IsAuthenticated,
                IsNotModerator,
                IsOwner,
            )
        else:
            permission_classes = (
                IsAuthenticated,
                IsModeratorOrOwner,
            )

        return [
            permission()
            for permission in permission_classes
        ]
