"""Контроллеры приложения users."""

from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
import stripe

from users.models import Payment, Subscription, User
from users.permissions import IsSelf
from users.serializers import (
    ErrorResponseSerializer,
    PaymentCreateSerializer,
    PaymentSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    SubscriptionToggleResponseSerializer,
    SubscriptionToggleSerializer,
    UserSerializer,
)
from users.services import (
    create_stripe_checkout_session,
    create_stripe_price,
    create_stripe_product,
    retrieve_stripe_checkout_session,
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
        """Выбирает сериализатор для действия."""

        if self.action == "create":
            return RegisterSerializer

        if self.action == "list":
            return PublicUserSerializer

        return UserSerializer

    def get_permissions(self):
        """Настраивает права доступа."""

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
        """Возвращает полный свой или сокращённый чужой профиль."""

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
    """Список платежей текущего пользователя."""

    queryset = Payment.objects.none()
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
        "payment_status",
        "session_status",
    )
    ordering_fields = (
        "payment_date",
        "amount",
    )
    ordering = ("-payment_date",)

    def get_queryset(self):
        """Возвращает только платежи текущего пользователя."""

        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()

        return (
            Payment.objects
            .filter(user=self.request.user)
            .select_related(
                "user",
                "paid_course",
                "paid_lesson",
                "paid_lesson__course",
            )
            .prefetch_related(
                "paid_course__lessons",
            )
            .order_by("-payment_date")
        )

    @extend_schema(
        summary="Получить список своих платежей",
        description=(
            "Возвращает платежи текущего пользователя. "
            "Поддерживает фильтрацию и сортировку."
        ),
        tags=["Платежи"],
        responses={
            200: PaymentSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Пользователь не авторизован.",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        """Возвращает список платежей."""

        return super().get(
            request,
            *args,
            **kwargs,
        )


class PaymentCreateAPIView(APIView):
    """Создаёт оплату курса через Stripe."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Создать оплату курса",
        description=(
            "Создаёт локальный платёж, продукт Stripe, "
            "цену Stripe и Checkout Session. "
            "Возвращает данные платежа и ссылку на оплату."
        ),
        tags=["Платежи"],
        request=PaymentCreateSerializer,
        responses={
            201: PaymentSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Некорректный курс или сумма.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Пользователь не авторизован.",
            ),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Ошибка обращения к Stripe.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Ключ Stripe не настроен.",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Создаёт платёж и возвращает ссылку Stripe."""

        input_serializer = PaymentCreateSerializer(
            data=request.data,
        )
        input_serializer.is_valid(
            raise_exception=True,
        )

        course = input_serializer.validated_data["course"]
        amount = input_serializer.validated_data["amount"]

        payment = Payment.objects.create(
            user=request.user,
            paid_course=course,
            amount=amount,
            payment_method=Payment.PaymentMethod.CARD,
        )

        try:
            product_data = create_stripe_product(
                payment,
            )

            payment.stripe_product_id = product_data["id"]
            payment.save(
                update_fields=("stripe_product_id",),
            )

            price_data = create_stripe_price(
                payment=payment,
                product_id=product_data["id"],
            )

            payment.stripe_price_id = price_data["id"]
            payment.save(
                update_fields=("stripe_price_id",),
            )

            session_data = create_stripe_checkout_session(
                payment=payment,
                price_id=price_data["id"],
            )

            payment.stripe_session_id = session_data["id"]
            payment.payment_url = session_data["url"]
            payment.payment_status = session_data[
                "payment_status"
            ]
            payment.session_status = session_data["status"]

            payment.save(
                update_fields=(
                    "stripe_session_id",
                    "payment_url",
                    "payment_status",
                    "session_status",
                )
            )

        except ImproperlyConfigured as error:
            payment.delete()

            return Response(
                {
                    "detail": str(error),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except stripe.StripeError as error:
            payment.payment_status = "error"
            payment.session_status = "error"
            payment.save(
                update_fields=(
                    "payment_status",
                    "session_status",
                )
            )

            return Response(
                {
                    "detail": (
                        "Stripe не смог создать оплату: "
                        f"{error}"
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        output_serializer = PaymentSerializer(
            payment,
            context={
                "request": request,
            },
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PaymentStatusAPIView(APIView):
    """Проверяет состояние Checkout Session."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Проверить статус оплаты",
        description=(
            "Получает Checkout Session из Stripe "
            "и синхронизирует статусы локального платежа."
        ),
        tags=["Платежи"],
        responses={
            200: PaymentSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "У платежа отсутствует ID "
                    "платёжной сессии."
                ),
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Пользователь не авторизован.",
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Платёж не найден.",
            ),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Ошибка обращения к Stripe.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Ключ Stripe не настроен.",
            ),
        },
    )
    def get(self, request, pk, *args, **kwargs):
        """Получает и сохраняет актуальные статусы."""

        payment = get_object_or_404(
            Payment,
            pk=pk,
            user=request.user,
        )

        if not payment.stripe_session_id:
            return Response(
                {
                    "detail": (
                        "У платежа отсутствует "
                        "Stripe Session ID."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session_data = retrieve_stripe_checkout_session(
                payment.stripe_session_id,
            )

        except ImproperlyConfigured as error:
            return Response(
                {
                    "detail": str(error),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except stripe.StripeError as error:
            return Response(
                {
                    "detail": (
                        "Не удалось получить статус Stripe: "
                        f"{error}"
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment.payment_status = session_data[
            "payment_status"
        ]
        payment.session_status = session_data["status"]

        if session_data.get("url"):
            payment.payment_url = session_data["url"]

        payment.save(
            update_fields=(
                "payment_status",
                "session_status",
                "payment_url",
            )
        )

        output_serializer = PaymentSerializer(
            payment,
            context={
                "request": request,
            },
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_200_OK,
        )


class SubscriptionToggleAPIView(APIView):
    """Добавляет или удаляет подписку пользователя на курс."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Добавить или удалить подписку на курс",
        description=(
            "Если подписки на указанный курс нет, "
            "она создаётся. Если подписка уже существует, "
            "она удаляется."
        ),
        tags=["Подписки"],
        request=SubscriptionToggleSerializer,
        responses={
            200: SubscriptionToggleResponseSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "Передан отсутствующий или "
                    "некорректный идентификатор курса."
                ),
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Пользователь не авторизован.",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Переключает состояние подписки на курс."""

        serializer = SubscriptionToggleSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        course = serializer.validated_data["course"]

        subscription, created = (
            Subscription.objects.get_or_create(
                user=request.user,
                course=course,
            )
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
