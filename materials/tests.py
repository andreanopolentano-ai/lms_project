"""Тесты приложения materials."""

from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Course, Lesson
from users.models import Subscription, User


class MaterialsAPITestCase(APITestCase):
    """Тесты уроков, подписок, пагинации и прав доступа."""

    def setUp(self):
        """Создает пользователей, группу, курс и урок."""

        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="OwnerPassword2026!",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="OtherPassword2026!",
        )
        self.moderator = User.objects.create_user(
            email="moderator@test.com",
            password="ModeratorPassword2026!",
        )

        moderator_group = Group.objects.create(
            name="Модераторы",
        )
        self.moderator.groups.add(moderator_group)

        self.course = Course.objects.create(
            title="Тестовый курс",
            description="Описание тестового курса",
            owner=self.owner,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Тестовый урок",
            description="Описание тестового урока",
            video_url="https://www.youtube.com/watch?v=test",
            owner=self.owner,
        )

        self.course_list_url = reverse(
            "materials:courses-list",
        )
        self.course_detail_url = reverse(
            "materials:courses-detail",
            kwargs={"pk": self.course.pk},
        )
        self.lesson_list_url = reverse(
            "materials:lesson-list-create",
        )
        self.lesson_detail_url = reverse(
            "materials:lesson-detail",
            kwargs={"pk": self.lesson.pk},
        )
        self.subscription_url = reverse(
            "users:subscription-toggle",
        )

    def test_unauthenticated_user_has_no_access(self):
        """Неавторизованный пользователь не получает материалы."""

        course_response = self.client.get(
            self.course_list_url,
        )
        lesson_response = self.client.get(
            self.lesson_list_url,
        )

        self.assertEqual(
            course_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            lesson_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_owner_can_create_lesson(self):
        """Владелец может создать урок."""

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            self.lesson_list_url,
            {
                "course": self.course.pk,
                "title": "Новый урок",
                "description": "Описание нового урока",
                "video_url": (
                    "https://www.youtube.com/watch?v=new"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            response.data["owner"],
            self.owner.pk,
        )
        self.assertTrue(
            Lesson.objects.filter(
                title="Новый урок",
                owner=self.owner,
            ).exists()
        )

    def test_owner_can_retrieve_lesson(self):
        """Владелец может получить свой урок."""

        self.client.force_authenticate(user=self.owner)

        response = self.client.get(
            self.lesson_detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            self.lesson.pk,
        )

    def test_owner_can_update_lesson(self):
        """Владелец может изменить свой урок."""

        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            self.lesson_detail_url,
            {"title": "Обновленный урок"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.lesson.refresh_from_db()

        self.assertEqual(
            self.lesson.title,
            "Обновленный урок",
        )

    def test_owner_can_delete_lesson(self):
        """Владелец может удалить свой урок."""

        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(
            self.lesson_detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            Lesson.objects.filter(
                pk=self.lesson.pk,
            ).exists()
        )

    def test_external_video_url_is_rejected(self):
        """Ссылка не на YouTube возвращает понятную ошибку."""

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            self.lesson_list_url,
            {
                "course": self.course.pk,
                "title": "Урок с неправильной ссылкой",
                "video_url": "https://example.com/video",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "video_url",
            response.data,
        )
        self.assertIn(
            "Разрешены только ссылки на youtube.com.",
            str(response.data["video_url"]),
        )

    def test_youtube_url_is_allowed(self):
        """Ссылка на YouTube проходит валидацию."""

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            self.lesson_list_url,
            {
                "course": self.course.pk,
                "title": "Урок с YouTube",
                "video_url": (
                    "https://youtube.com/watch?v=allowed"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_other_user_cannot_access_foreign_lesson(self):
        """Обычный пользователь не работает с чужим уроком."""

        self.client.force_authenticate(
            user=self.other_user,
        )

        get_response = self.client.get(
            self.lesson_detail_url,
        )
        patch_response = self.client.patch(
            self.lesson_detail_url,
            {"title": "Чужое изменение"},
            format="json",
        )
        delete_response = self.client.delete(
            self.lesson_detail_url,
        )

        self.assertEqual(
            get_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            patch_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_moderator_permissions_for_lessons(self):
        """Модератор читает и меняет, но не создает и не удаляет."""

        self.client.force_authenticate(
            user=self.moderator,
        )

        get_response = self.client.get(
            self.lesson_detail_url,
        )
        patch_response = self.client.patch(
            self.lesson_detail_url,
            {"title": "Изменено модератором"},
            format="json",
        )
        create_response = self.client.post(
            self.lesson_list_url,
            {
                "course": self.course.pk,
                "title": "Урок модератора",
                "video_url": (
                    "https://youtube.com/watch?v=moderator"
                ),
            },
            format="json",
        )
        delete_response = self.client.delete(
            self.lesson_detail_url,
        )

        self.assertEqual(
            get_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            patch_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            create_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_subscription_is_created_and_deleted(self):
        """Повторный запрос переключает подписку."""

        self.client.force_authenticate(user=self.owner)

        create_response = self.client.post(
            self.subscription_url,
            {"course": self.course.pk},
            format="json",
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            create_response.data["message"],
            "Подписка добавлена.",
        )
        self.assertTrue(
            Subscription.objects.filter(
                user=self.owner,
                course=self.course,
            ).exists()
        )

        delete_response = self.client.post(
            self.subscription_url,
            {"course": self.course.pk},
            format="json",
        )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            delete_response.data["message"],
            "Подписка удалена.",
        )
        self.assertFalse(
            Subscription.objects.filter(
                user=self.owner,
                course=self.course,
            ).exists()
        )

    def test_subscription_invalid_course_returns_error(self):
        """Несуществующий курс возвращает ошибку."""

        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            self.subscription_url,
            {"course": 999999},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "course",
            response.data,
        )

    def test_subscription_pair_is_unique(self):
        """Нельзя создать две одинаковые подписки."""

        Subscription.objects.create(
            user=self.owner,
            course=self.course,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Subscription.objects.create(
                    user=self.owner,
                    course=self.course,
                )

    def test_course_contains_subscription_status(self):
        """Курс возвращает признак подписки пользователя."""

        self.client.force_authenticate(user=self.owner)

        response_before = self.client.get(
            self.course_detail_url,
        )

        self.assertFalse(
            response_before.data["is_subscribed"]
        )

        Subscription.objects.create(
            user=self.owner,
            course=self.course,
        )

        response_after = self.client.get(
            self.course_detail_url,
        )

        self.assertTrue(
            response_after.data["is_subscribed"]
        )

    def test_courses_are_paginated(self):
        """Список курсов возвращается постранично."""

        for number in range(6):
            Course.objects.create(
                title=f"Курс {number}",
                owner=self.owner,
            )

        self.client.force_authenticate(user=self.owner)

        response = self.client.get(
            self.course_list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(
            len(response.data["results"]),
            5,
        )

    def test_lessons_are_paginated(self):
        """Список уроков возвращается постранично."""

        for number in range(5):
            Lesson.objects.create(
                course=self.course,
                title=f"Урок {number}",
                video_url=(
                    f"https://youtube.com/watch?v={number}"
                ),
                owner=self.owner,
            )

        self.client.force_authenticate(user=self.owner)

        response = self.client.get(
            self.lesson_list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(
            len(response.data["results"]),
            5,
        )
