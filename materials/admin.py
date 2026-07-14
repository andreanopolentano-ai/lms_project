"""Админка приложения materials."""

from django.contrib import admin

from materials.models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Настройки отображения курсов в админке."""

    list_display = ("id", "title")
    search_fields = ("title", "description")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Настройки отображения уроков в админке."""

    list_display = ("id", "title", "course", "video_url")
    list_filter = ("course",)
    search_fields = ("title", "description")
