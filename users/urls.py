"""Маршруты приложения users."""

from django.urls import path

from users.views import UserProfileAPIView

app_name = "users"

urlpatterns = [
    path("users/<int:pk>/profile/", UserProfileAPIView.as_view(), name="user-profile"),
]
