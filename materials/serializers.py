"""Сериализаторы приложения materials."""

from rest_framework import serializers

from materials.models import Course, Lesson
from materials.validators import validate_youtube_url
from users.models import Subscription


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    video_url = serializers.URLField(
        max_length=500,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_youtube_url],
    )

    class Meta:
        model = Lesson
        fields = (
            "id",
            "course",
            "title",
            "description",
            "preview",
            "video_url",
            "owner",
        )


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса с уроками и признаком подписки."""

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
            "owner",
            "lessons_count",
            "lessons",
            "is_subscribed",
        )

    def get_lessons_count(self, obj: Course) -> int:
        """Возвращает количество уроков курса."""

        return obj.lessons.count()

    def get_is_subscribed(self, obj: Course) -> bool:
        """Проверяет подписку текущего пользователя на курс."""

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return Subscription.objects.filter(
            user=request.user,
            course=obj,
        ).exists()
