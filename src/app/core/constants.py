"""Модуль с константами приложения."""

import re
from datetime import datetime, timedelta
from pathlib import Path


class BookingConstants:
    """Класс с константами для бронирования."""

    REPR_FORMAT = 'Бронирование id:{} status:{} user_id:{}'
    MAX_GUESTS = 1000  # TODO: возможно стоит вычислять по вместимости столов.
    MIN_GUESTS = 1

    DATE_ERROR = 'Дата бронирования не может быть в прошлом.'
    GUEST_NUMBER_ERROR = 'Количество гостей должно быть между {} и {}'
    SLOT_ALREADY_BOOKED = (
        'Попытка забронировать уже забронированный слот {} на стол {}.'
    )
    USER_DOES_NOT_EXIST = 'Пользователь c id {} не существует.'
    CAFE_DOES_NOT_EXIST = 'Кафе c id {} не существует.'
    USER_RIGHTS_ERROR = 'У вас нет прав для просмотра чужих бронирований.'
    BOOKING_NOT_FOUND = 'Бронирование c id {} не найдено.'
    USER_NOT_AUTHENTICATED = 'Пользователь не авторизован'
    SLOTS_UNAVAILABLE = 'Выбранные временные слоты уже забронированы'
    LIST_SLOTS_ERROR = 'Список временных слотов не может быть пустым.'
    DISH_NOT_FOUND = 'Некоторые блюда из предзаказа не найдены в меню.'
    DISH_UNAVAILABLE = 'Выбранные блюда временно недоступны.'
    DISH_CAFE_MISMATCH = 'Блюда не принадлежат выбранному кафе.'
    TABLE_OR_SLOT_ERROR = 'Ошибка валидации слотов бронирования.'
    ID_LIST_NEEDED = 'Необходимо передать список идентификаторов.'
    INVALID_START_TIME_ERROR = (
        'Время начала бронирования не может быть в прошлом.'
    )
    DUBLICATE_SLOTS = 'Список слотов содержит дубликаты.'
    SLOTS_OR_TABLES_NOT_IN_CAFE = (
        'Выбранные слоты или столы не принадлежат выбранному кафе.'
    )


class MediaConstants:
    """Класс констант для работы с media."""

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MEDIA_DIR = BASE_DIR / 'media'
    IMAGE_EXTENSION = 'jpg'
    CHUNK_SIZE_1MB = 1024 * 1024
    MAX_PHOTO_SIZE_5MB = CHUNK_SIZE_1MB * 5
    VALID_TYPES = ['image/png', 'image/jpeg']


class CafeConstants:
    """Класс с константами для модели кафе."""

    ERROR_PHONE = (
        'Номер телефона должен начинаться с +7 и содержать 10 цифр после!'
    )
    NAME_RESTRICTION = 20
    MIN_LENGTH_ADDRESS = 10
    MIN_LENGTH_DESCRIPTION = 10
    MIN_LENGTH_MANAGERS_LIST = 1
    MIN_LENGTH_NAME = 2
    PHONE_FORMAT = r'^\+7\d{10}$'


class ActionConstants:
    """Класс с константами для модели акций."""

    MIN_DESCRIPTION = 10
    MIN_LENGTH_CAFES_LIST = 1


class DishConstants:
    """Класс с константами для модели блюд."""

    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 255
    DISH_NOT_FOUND_IN_CAFE = (
        'Блюдо с id={dish_id} в кафе с id={cafe_id} не найдено.'
    )
    DISH_NAME_DUPLICATE = (
        'Блюдо с названием "{name}" уже существует в кафе с id={cafe_id}.'
    )


class UserConstants:
    """Класс с константами для пользователей."""

    MAX_USERNAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 255
    MAX_PHONE_LENGTH = 20
    MAX_PASSWORD_LENGTH = 255
    MAX_TG_ID_LENGTH = 100
    MIN_PASSWORD_LENGTH = 5
    DEFAULT_USER_ROLE = 'user'
    PHONE_REGEX = re.compile(r'^(\+7|8)\d{10}$')
    PASSWORD_REGEX = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).+$')


class LoggingConstants:
    """Класс для хранения константных значений модуля логгирования."""

    # Общие настройки модуля логгирования
    SYSTEM_MESSAGE_NAME_ALLIAS: str = 'SYSTEM'
    LOGGING_FORMAT_STRING = (
        '{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | '
        'trace_id={extra[trace_id]} | '
        'user_id={extra[user_id]} username={extra[username]} | '
        '{message}'
    )
    LOGGING_FOLDER: Path = Path('logs')
    LOG_FILES_PATH: Path = LOGGING_FOLDER / 'app.log'
    NOISE_ENDPOINTS: set[str] = {'/health', '/docs', '/openapi.json'}
    INITIAL_STACK_FRAME_DEPTH: int = 6
    ROTATION_FILE_SIZE: str = '5 MB'
    RETENTION_FILES_COUNT: int = 3
    LOG_FILES_COMPRESSION_TYPE: str = 'zip'
    LOGGERS_TO_INTERCEPT: list[str] = [
        'uvicorn',
        'uvicorn.error',
        'alembic',
    ]

    # Настройки специфичные для dev среды
    DEV_MODE_COLORIZE_LOGS: bool = True
    DEV_MODE_ENQUEUE_LOGS: bool = True
    DEV_MODE_BACKTRACE_LOGS: bool = True
    DEV_MODE_DIAGNOSE_LOGS: bool = True

    # Настройки специфичные для prod среды
    PROD_MODE_COLORIZE_LOGS: bool = False
    PROD_MODE_ENQUEUE_LOGS: bool = True
    PROD_MODE_BACKTRACE_LOGS: bool = False
    PROD_MODE_DIAGNOSE_LOGS: bool = False


class SlotConstants:
    """Класс для констант модели интервала времени бронирования столика."""

    BASE_TIME = datetime.now() + timedelta(minutes=10)
    FROM_TIME = BASE_TIME.strftime('%H:%M')
    TO_TIME = (BASE_TIME + timedelta(hours=1)).strftime('%H:%M')


class NotificationConstants:
    """Класс констант для уведомлений и напоминаний о бронировании."""

    ADMIN_EMAIL = 'test@mail.ru'
