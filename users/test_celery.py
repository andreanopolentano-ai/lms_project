"""Тесты периодической задачи пользователей."""

from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from users.models import User
from users.tasks import deactivate_inactive_users


class DeactivateInactiveUsersTaskTestCase(TestCase):
    """Проверяет батчевую блокировку неактивных пользователей."""

    def setUp(self):
        now = timezone.now()

        self.old_user = User.objects.create_user(
            email="old-login@test.com",
            password="Password2026!",
            last_login=now - timedelta(days=31),
        )
        self.recent_user = User.objects.create_user(
            email="recent-login@test.com",
            password="Password2026!",
            last_login=now - timedelta(days=10),
        )
        self.never_logged_in_old_user = User.objects.create_user(
            email="never-login@test.com",
            password="Password2026!",
            last_login=None,
            date_joined=now - timedelta(days=31),
        )
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="Password2026!",
            last_login=now - timedelta(days=60),
            is_staff=True,
        )

    def test_task_deactivates_only_inactive_regular_users(self):
        updated_count = deactivate_inactive_users()

        self.old_user.refresh_from_db()
        self.recent_user.refresh_from_db()
        self.never_logged_in_old_user.refresh_from_db()
        self.staff_user.refresh_from_db()

        self.assertEqual(updated_count, 2)
        self.assertFalse(self.old_user.is_active)
        self.assertTrue(self.recent_user.is_active)
        self.assertFalse(self.never_logged_in_old_user.is_active)
        self.assertTrue(self.staff_user.is_active)

    def test_celery_timezone_matches_django_timezone(self):
        self.assertEqual(
            settings.CELERY_TIMEZONE,
            settings.TIME_ZONE,
        )

    def test_periodic_task_is_present_in_beat_schedule(self):
        schedule = settings.CELERY_BEAT_SCHEDULE[
            "deactivate-inactive-users-daily"
        ]

        self.assertEqual(
            schedule["task"],
            "users.tasks.deactivate_inactive_users",
        )
