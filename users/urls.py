"""Маршруты приложения users."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import (
    PaymentCreateAPIView,
    PaymentListAPIView,
    PaymentStatusAPIView,
    SubscriptionToggleAPIView,
    UserViewSet,
)

app_name = "users"

router = DefaultRouter()
router.register(
    "users",
    UserViewSet,
    basename="users",
)

user_profile_view = UserViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

urlpatterns = [
    path(
        "users/<int:pk>/profile/",
        user_profile_view,
        name="user-profile",
    ),
    path(
        "payments/",
        PaymentListAPIView.as_view(),
        name="payment-list",
    ),
    path(
        "payments/create/",
        PaymentCreateAPIView.as_view(),
        name="payment-create",
    ),
    path(
        "payments/<int:pk>/status/",
        PaymentStatusAPIView.as_view(),
        name="payment-status",
    ),
    path(
        "subscriptions/toggle/",
        SubscriptionToggleAPIView.as_view(),
        name="subscription-toggle",
    ),
    path("", include(router.urls)),
]
