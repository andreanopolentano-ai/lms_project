"""Сериализаторы приложения users."""

from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers

from materials.serializers import CourseSerializer, LessonSerializer
from users.models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор платежа с вложенными данными."""

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

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )

        return email

    def validate(self, attrs):
        """Проверяет совпадение паролей."""

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": "Введенные пароли не совпадают."
                }
            )

        return attrs

    def create(self, validated_data):
        """Создает пользователя и безопасно хеширует пароль."""

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
                    "email": "Пользователь с таким email уже существует."
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
    """Полный сериализатор собственного профиля пользователя."""

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
        """Обновляет профиль и корректно хеширует новый пароль."""

        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save(update_fields=("password",))

        return instance
