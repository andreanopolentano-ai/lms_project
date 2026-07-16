"""Сериализаторы приложения materials."""

from rest_framework import serializers

from materials.models import Course, Lesson


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


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса с количеством и списком уроков."""

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
            "lessons_count",
            "lessons",
        )

    def get_lessons_count(self, obj: Course) -> int:
        """Возвращает количество уроков курса."""
        return obj.lessons.count()
