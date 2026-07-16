"""Контроллеры приложения users."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView

from users.models import Payment, User
from users.serializers import PaymentSerializer, UserSerializer


class UserProfileAPIView(RetrieveUpdateAPIView):
    """Получение и редактирование профиля пользователя."""

    queryset = User.objects.prefetch_related(
        "payments__paid_course__lessons",
        "payments__paid_lesson",
    )
    serializer_class = UserSerializer


class PaymentListAPIView(ListAPIView):
    """Получение списка платежей с фильтрацией и сортировкой."""

    queryset = Payment.objects.select_related(
        "user",
        "paid_course",
        "paid_lesson",
        "paid_lesson__course",
    ).prefetch_related(
        "paid_course__lessons",
    )
    serializer_class = PaymentSerializer

    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_fields = (
        "paid_course",
        "paid_lesson",
        "payment_method",
    )
    ordering_fields = (
        "payment_date",
    )
    ordering = (
        "-payment_date",
    )
