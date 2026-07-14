"""Сериализаторы приложения materials."""

from rest_framework import serializers

from materials.models import Course, Lesson


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса."""

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
        )


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    class Meta:
        model = Lesson
        fields = (
            "id",
            "course",
            "title",
            "description",
            "preview",
            "video_url",
        )
