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
from materials.serializers import (
    CourseSerializer,
    LessonSerializer,
)


class CourseViewSet(ModelViewSet):
    """CRUD курсов."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CourseLessonPagination

    def get_queryset(self):
        """Возвращает курсы владельца или все курсы модератору."""

        queryset = (
            Course.objects
            .select_related("owner")
            .prefetch_related(
                "lessons",
                "subscriptions",
            )
            .order_by("pk")
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(
            owner=self.request.user,
        )

    def get_permissions(self):
        """Настраивает права для действий с курсами."""

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
        """Устанавливает владельца курса."""

        serializer.save(
            owner=self.request.user,
        )


class LessonListCreateAPIView(ListCreateAPIView):
    """Получение списка и создание уроков."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = CourseLessonPagination

    def get_queryset(self):
        """Возвращает уроки владельца или все уроки модератору."""

        queryset = (
            Lesson.objects
            .select_related(
                "course",
                "owner",
            )
            .order_by("pk")
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(
            owner=self.request.user,
        )

    def get_permissions(self):
        """Настраивает права для списка и создания уроков."""

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
        """Устанавливает владельца урока."""

        serializer.save(
            owner=self.request.user,
        )


class LessonRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPIView,
):
    """Просмотр, изменение и удаление урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        """Возвращает уроки владельца или все уроки модератору."""

        queryset = (
            Lesson.objects
            .select_related(
                "course",
                "owner",
            )
            .order_by("pk")
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(
            owner=self.request.user,
        )

    def get_permissions(self):
        """Настраивает права для отдельного урока."""

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
