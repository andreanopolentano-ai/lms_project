"""Тесты Celery-уведомлений о курсах."""

from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Course, Lesson
from materials.tasks import send_course_update_notification
from users.models import Subscription, User


class CourseNotificationTaskTestCase(APITestCase):
    """Проверяет задачу отправки писем подписчикам."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner-celery@test.com",
            password="OwnerPassword2026!",
        )
        self.subscriber = User.objects.create_user(
            email="subscriber@test.com",
            password="SubscriberPassword2026!",
        )
        self.inactive_subscriber = User.objects.create_user(
            email="inactive-subscriber@test.com",
            password="SubscriberPassword2026!",
            is_active=False,
        )
        self.course = Course.objects.create(
            title="Курс Celery",
            owner=self.owner,
        )
        Subscription.objects.create(
            user=self.subscriber,
            course=self.course,
        )
        Subscription.objects.create(
            user=self.inactive_subscriber,
            course=self.course,
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_task_sends_email_only_to_active_subscribers(self):
        sent_count = send_course_update_notification(self.course.pk)

        self.assertEqual(sent_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to,
            [self.subscriber.email],
        )
        self.assertIn(
            self.course.title,
            mail.outbox[0].subject,
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_task_returns_zero_for_course_without_subscribers(self):
        Subscription.objects.all().delete()

        sent_count = send_course_update_notification(self.course.pk)

        self.assertEqual(sent_count, 0)
        self.assertEqual(len(mail.outbox), 0)


class CourseNotificationTriggerTestCase(APITestCase):
    """Проверяет запуск задачи после успешного обновления."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="trigger-owner@test.com",
            password="OwnerPassword2026!",
        )
        self.course = Course.objects.create(
            title="Курс для обновления",
            owner=self.owner,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Урок для обновления",
            owner=self.owner,
        )
        self.course_url = reverse(
            "materials:courses-detail",
            kwargs={"pk": self.course.pk},
        )
        self.lesson_url = reverse(
            "materials:lesson-detail",
            kwargs={"pk": self.lesson.pk},
        )
        self.client.force_authenticate(user=self.owner)

    @patch(
        "materials.views."
        "send_course_update_notification.delay"
    )
    def test_course_update_enqueues_task_after_four_hours(
        self,
        delay_mock,
    ):
        old_time = timezone.now() - timedelta(hours=5)
        Course.objects.filter(pk=self.course.pk).update(
            updated_at=old_time,
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                self.course_url,
                {"title": "Обновлённый курс"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delay_mock.assert_called_once_with(self.course.pk)

    @patch(
        "materials.views."
        "send_course_update_notification.delay"
    )
    def test_course_update_does_not_enqueue_before_four_hours(
        self,
        delay_mock,
    ):
        recent_time = timezone.now() - timedelta(hours=2)
        Course.objects.filter(pk=self.course.pk).update(
            updated_at=recent_time,
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                self.course_url,
                {"title": "Ещё одно название"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delay_mock.assert_not_called()

    @patch(
        "materials.views."
        "send_course_update_notification.delay"
    )
    def test_lesson_update_enqueues_course_task(
        self,
        delay_mock,
    ):
        old_time = timezone.now() - timedelta(hours=5)
        Course.objects.filter(pk=self.course.pk).update(
            updated_at=old_time,
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                self.lesson_url,
                {"title": "Обновлённый урок"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delay_mock.assert_called_once_with(self.course.pk)

        self.course.refresh_from_db()
        self.assertGreater(self.course.updated_at, old_time)
