import os

from celery import Celery

from app.core.logging import setup_logging

# Получение настроек из переменных окружения
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_SECURITY_KEY = os.getenv("CELERY_SECURITY_KEY")

setup_logging(
    env=os.getenv("ENVIRONMENT", "dev"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)
# Создаём экземпляр Celery
celery_app = Celery(
    "fastapi_celery",  # Имя приложения
    broker=CELERY_BROKER_URL,  # URL брокера сообщений
    backend=CELERY_RESULT_BACKEND,  # URL бэкенда результатов
    include=["app.celery.tasks"],  # Модули с задачами
)

# Конфигурация Celery
celery_app.conf.update(
    # Настройка безопасности
    security_key=CELERY_SECURITY_KEY,

    # Настройки сериализации
    task_serializer="json",  # Формат сериализации задач
    accept_content=["json"],  # Принимаемые форматы данных
    result_serializer="json",  # Формат сериализации результатов

    # Настройки времени
    timezone="Europe/Moscow",  # Часовой пояс
    enable_utc=True,  # Использовать UTC для внутренних операций

    # Настройки отслеживания
    task_track_started=True,  # Отслеживать начало выполнения задач
    task_ignore_result=False,  # Сохранять результаты задач

    # Настройки таймаутов
    task_time_limit=30 * 60,  # Максимальное время выполнения задачи (30 минут)
    task_soft_time_limit=25 * 60,  # Мягкий таймаут (25 минут)

    # Настройки воркера
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

    # Настройки очередей
    task_default_queue="default",  # Очередь по умолчанию
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.file_tasks.*": {"queue": "files"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },

    # Настройки повторных попыток
    # Подтверждать выполнение задачи только после успешного завершения
    task_acks_late=True,
    worker_disable_rate_limits=False,  # Не отключать ограничения скорости

    # Настройки логирования
    worker_log_format="""
        [%(asctime)s: %(levelname)s/%(processName)s] %(message)s
    """,
    worker_task_log_format="""
        [%(asctime)s: %(levelname)s/%(processName)s] \
        [%(task_name)s(%(task_id)s)] %(message)s
    """,
)
