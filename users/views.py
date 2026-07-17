"""Контроллеры приложения users."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from users.models import Payment, Subscription, User
from users.permissions import IsSelf
from users.serializers import (
    PaymentSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    SubscriptionToggleSerializer,
    UserSerializer,
)


class UserViewSet(ModelViewSet):
    """CRUD пользователей и регистрация."""

    queryset = User.objects.all()

    def get_queryset(self):
        """Возвращает пользователей с историей платежей."""

        return User.objects.prefetch_related(
            "payments__paid_course__lessons",
            "payments__paid_lesson",
        )

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""

        if self.action == "create":
            return RegisterSerializer

        if self.action == "list":
            return PublicUserSerializer

        return UserSerializer

    def get_permissions(self):
        """Открывает регистрацию и защищает остальные действия."""

        if self.action == "create":
            permission_classes = (AllowAny,)
        elif self.action in (
            "update",
            "partial_update",
            "destroy",
        ):
            permission_classes = (
                IsAuthenticated,
                IsSelf,
            )
        else:
            permission_classes = (IsAuthenticated,)

        return [
            permission()
            for permission in permission_classes
        ]

    def retrieve(self, request, *args, **kwargs):
        """Возвращает полный свой профиль и сокращённый чужой."""

        user = self.get_object()

        if user.pk == request.user.pk:
            serializer_class = UserSerializer
        else:
            serializer_class = PublicUserSerializer

        serializer = serializer_class(
            user,
            context=self.get_serializer_context(),
        )

        return Response(serializer.data)


class PaymentListAPIView(ListAPIView):
    """Список платежей с фильтрацией и сортировкой."""

    queryset = Payment.objects.select_related(
        "user",
        "paid_course",
        "paid_lesson",
        "paid_lesson__course",
    ).prefetch_related(
        "paid_course__lessons",
    )
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_fields = (
        "paid_course",
        "paid_lesson",
        "payment_method",
    )
    ordering_fields = ("payment_date",)
    ordering = ("-payment_date",)


class SubscriptionToggleAPIView(APIView):
    """Добавляет или удаляет подписку пользователя на курс."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """Переключает состояние подписки на курс."""

        serializer = SubscriptionToggleSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        course = serializer.validated_data["course"]

        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            course=course,
        )

        if created:
            message = "Подписка добавлена."
        else:
            subscription.delete()
            message = "Подписка удалена."

        return Response(
            {
                "message": message,
                "is_subscribed": created,
            },
            status=status.HTTP_200_OK,
        )
