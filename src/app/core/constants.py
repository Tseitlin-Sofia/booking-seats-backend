"""Модуль с константами приложения."""
from pathlib import Path


class BookingConstants:
    """Класс с константами для бронирования."""

    MAX_GUESTS = 1000
    MIN_GUESTS = 1


class MediaConstants:
    """Класс констант для работы с media"""

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MEDIA_DIR = BASE_DIR / "media"
    IMAGE_EXTENSION = "jpg"
    CHUNK_SIZE_1MB = 1024 * 1024
    MAX_PHOTO_SIZE_5MB = CHUNK_SIZE_1MB * 5
    VALID_TYPES = ["image/png", "image/jpeg"]
