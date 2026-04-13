"""Модуль с константами приложения."""


class BookingConstants:
    """Класс с константами для бронирования."""

    MAX_GUESTS = 1000
    MIN_GUESTS = 1


class UserConstants:
    """Класс с константами для пользователей."""

    MAX_USERNAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 255
    MAX_PHONE_LENGTH = 20
    MAX_PASSWORD_LENGTH = 255
    MAX_TG_ID_LENGTH = 100
    DEFAULT_USER_ROLE = 'user'