"""Сериализаторы приложения users."""

from decimal import Decimal

from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers

from materials.models import Course
from materials.serializers import CourseSerializer, LessonSerializer
from users.models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор платежа с данными Stripe."""

    paid_course = CourseSerializer(read_only=True)
    paid_lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "user",
            "payment_date",
            "paid_course",
            "paid_lesson",
            "amount",
            "payment_method",
            "stripe_product_id",
            "stripe_price_id",
            "stripe_session_id",
            "payment_url",
            "payment_status",
            "session_status",
        )
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    """Входные данные для создания оплаты курса."""

    course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        help_text="Идентификатор оплачиваемого курса.",
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.50"),
        help_text="Стоимость курса в рублях.",
    )


class SubscriptionToggleSerializer(serializers.Serializer):
    """Проверяет данные для добавления или удаления подписки."""

    course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
    )


class SubscriptionToggleResponseSerializer(
    serializers.Serializer,
):
    """Ответ после добавления или удаления подписки."""

    message = serializers.CharField(
        help_text="Результат изменения подписки.",
    )
    is_subscribed = serializers.BooleanField(
        help_text="Текущее состояние подписки.",
    )


class ErrorResponseSerializer(serializers.Serializer):
    """Стандартный ответ с описанием ошибки."""

    detail = serializers.CharField(
        help_text="Описание ошибки.",
    )


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации пользователя."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=(validate_password,),
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
        )
        read_only_fields = ("id",)

    def validate_email(self, value: str) -> str:
        """Проверяет отсутствие пользователя с таким email."""

        email = User.objects.normalize_email(value)

        if User.objects.filter(
            email__iexact=email,
        ).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )

        return email

    def validate(self, attrs):
        """Проверяет совпадение паролей."""

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "Введённые пароли не совпадают."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        """Создаёт пользователя и хеширует пароль."""

        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        try:
            with transaction.atomic():
                user = User(**validated_data)
                user.set_password(password)
                user.save()
        except IntegrityError as error:
            raise serializers.ValidationError(
                {
                    "email": (
                        "Пользователь с таким email "
                        "уже существует."
                    )
                }
            ) from error

        return user


class PublicUserSerializer(serializers.ModelSerializer):
    """Общая информация о чужом профиле."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "phone",
            "city",
            "avatar",
        )


class UserSerializer(serializers.ModelSerializer):
    """Полный сериализатор профиля пользователя."""

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        validators=(validate_password,),
    )
    payments = PaymentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "date_joined",
            "payments",
        )
        read_only_fields = (
            "id",
            "date_joined",
            "payments",
        )

    def update(self, instance, validated_data):
        """Обновляет профиль и хеширует новый пароль."""

        password = validated_data.pop(
            "password",
            None,
        )

        instance = super().update(
            instance,
            validated_data,
        )

        if password:
            instance.set_password(password)
            instance.save(
                update_fields=("password",),
            )

        return instance
