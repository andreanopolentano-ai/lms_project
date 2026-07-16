"""Модели приложения materials."""

from django.conf import settings
from django.db import models


class Course(models.Model):
    """Модель курса."""

    title = models.CharField(
        max_length=200,
        verbose_name="Название",
    )
    preview = models.ImageField(
        upload_to="courses/previews/",
        blank=True,
        null=True,
        verbose_name="Превью",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_courses",
        blank=True,
        null=True,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "курс"
        verbose_name_plural = "курсы"

    def __str__(self) -> str:
        """Возвращает строковое представление курса."""
        return self.title


class Lesson(models.Model):
    """Модель урока."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Курс",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
    )
    preview = models.ImageField(
        upload_to="lessons/previews/",
        blank=True,
        null=True,
        verbose_name="Превью",
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ссылка на видео",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_lessons",
        blank=True,
        null=True,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "урок"
        verbose_name_plural = "уроки"

    def __str__(self) -> str:
        """Возвращает строковое представление урока."""
        return self.title
