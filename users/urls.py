"""Маршруты приложения users."""

from django.urls import path

from users.views import PaymentListAPIView, UserProfileAPIView

app_name = "users"

urlpatterns = [
    path(
        "users/<int:pk>/profile/",
        UserProfileAPIView.as_view(),
        name="user-profile",
    ),
    path(
        "payments/",
        PaymentListAPIView.as_view(),
        name="payment-list",
    ),
]
