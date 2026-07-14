"""Контроллеры приложения users."""

from rest_framework.generics import RetrieveUpdateAPIView

from users.models import User
from users.serializers import UserSerializer


class UserProfileAPIView(RetrieveUpdateAPIView):
    """Получение и редактирование профиля пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
