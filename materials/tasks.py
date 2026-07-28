"""Фоновые задачи приложения materials."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mass_mail

from materials.models import Course
from users.models import Subscription


@shared_task
def send_course_update_notification(course_id: int) -> int:
    """Отправляет подписчикам письма об обновлении курса."""

    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return 0

    subscriber_emails = list(
        Subscription.objects.filter(
            course_id=course_id,
            user__is_active=True,
        )
        .exclude(user__email="")
        .values_list("user__email", flat=True)
        .distinct()
    )

    if not subscriber_emails:
        return 0

    subject = f'Обновление курса «{course.title}»'
    message = (
        f'Материалы курса «{course.title}» были обновлены. '
        "Откройте курс, чтобы посмотреть изменения."
    )

    messages = tuple(
        (
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        for email in subscriber_emails
    )

    return send_mass_mail(
        messages,
        fail_silently=False,
    )
