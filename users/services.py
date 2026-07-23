"""Сервисные функции для взаимодействия со Stripe."""

from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from users.models import Payment


def configure_stripe() -> None:
    """Проверяет наличие ключа и настраивает Stripe."""

    if not settings.STRIPE_API_KEY:
        raise ImproperlyConfigured(
            "Переменная STRIPE_API_KEY не задана."
        )

    stripe.api_key = settings.STRIPE_API_KEY


def create_stripe_product(payment: Payment) -> dict:
    """Создаёт продукт Stripe для оплачиваемого курса."""

    configure_stripe()

    course = payment.paid_course

    product_data = {
        "name": course.title,
        "metadata": {
            "payment_id": str(payment.pk),
            "course_id": str(course.pk),
            "user_id": str(payment.user_id),
        },
    }

    if course.description:
        product_data["description"] = course.description

    product = stripe.Product.create(**product_data)

    return {
        "id": product.id,
        "name": product.name,
    }


def create_stripe_price(
    payment: Payment,
    product_id: str,
) -> dict:
    """Создаёт цену Stripe в копейках."""

    configure_stripe()

    unit_amount = int(
        (
            payment.amount * Decimal("100")
        ).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )

    price = stripe.Price.create(
        product=product_id,
        currency=settings.STRIPE_CURRENCY,
        unit_amount=unit_amount,
    )

    return {
        "id": price.id,
        "product": price.product,
        "currency": price.currency,
        "unit_amount": price.unit_amount,
    }


def create_stripe_checkout_session(
    payment: Payment,
    price_id: str,
) -> dict:
    """Создаёт Checkout Session и возвращает ссылку."""

    configure_stripe()

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=str(payment.pk),
        metadata={
            "payment_id": str(payment.pk),
            "course_id": str(payment.paid_course_id),
            "user_id": str(payment.user_id),
        },
    )

    return {
        "id": session.id,
        "url": session.url,
        "payment_status": session.payment_status,
        "status": session.status,
    }


def retrieve_stripe_checkout_session(
    session_id: str,
) -> dict:
    """Получает состояние Checkout Session."""

    configure_stripe()

    session = stripe.checkout.Session.retrieve(
        session_id,
    )

    return {
        "id": session.id,
        "url": session.url,
        "payment_status": session.payment_status,
        "status": session.status,
    }
