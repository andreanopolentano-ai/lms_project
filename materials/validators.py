"""Валидаторы приложения materials."""

from urllib.parse import urlparse

from rest_framework import serializers


ALLOWED_VIDEO_DOMAIN = "youtube.com"


def validate_youtube_url(value: str) -> str:
    """Разрешает только ссылки на youtube.com и его поддомены."""

    if not value:
        return value

    hostname = (urlparse(value).hostname or "").lower().rstrip(".")

    domain_is_allowed = (
        hostname == ALLOWED_VIDEO_DOMAIN
        or hostname.endswith(f".{ALLOWED_VIDEO_DOMAIN}")
    )

    if not domain_is_allowed:
        raise serializers.ValidationError(
            "Разрешены только ссылки на youtube.com."
        )

    return value
