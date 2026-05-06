import os
from logging import Logger
from typing import Any

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger

from app.core.logging import (
    get_logger,
    setup_celery_logger,
    setup_logging,
    setup_task_logger,
)

# Получение настроек из переменных окружения
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_SECURITY_KEY = os.getenv('CELERY_SECURITY_KEY')

setup_logging(
    env=os.getenv('ENVIRONMENT', 'dev'),
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
)

logger = get_logger()
logger.info('Инициализация Celery приложения')

celery_app = Celery(
    'fastapi_celery',  # Имя приложения
    broker=CELERY_BROKER_URL,  # URL брокера сообщений
    backend=CELERY_RESULT_BACKEND,  # URL бэкенда результатов
    include=['app.celery.tasks'],  # Модули с задачами
)

# Конфигурация Celery
celery_app.conf.update(
    # Настройка безопасности
    security_key=CELERY_SECURITY_KEY,
    # Настройки сериализации
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    # Настройки времени
    timezone='Europe/Moscow',
    enable_utc=True,
    # Настройки отслеживания
    task_track_started=True,
    task_ignore_result=False,
    # Настройки таймаутов
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    # Настройки воркера
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Настройки очередей
    task_default_queue='default',
    task_routes={
        'app.tasks.email_tasks.*': {'queue': 'email'},
        'app.tasks.file_tasks.*': {'queue': 'files'},
        'app.tasks.report_tasks.*': {'queue': 'reports'},
    },
    # Настройки повторных попыток
    task_acks_late=True,
    worker_disable_rate_limits=False,
    # Настройки логирования
    worker_redirect_stdouts=False,
    worker_redirect_stdouts_level='WARNING',
    worker_hijack_root_logger=False,
)


# Регистрируем сигналы для настройки логгеров Celery
@after_setup_logger.connect
def on_celery_logger_setup(
    logger_instance: Logger,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Обработчик сигнала настройки логгера Celery."""
    setup_celery_logger(logger_instance, *args, **kwargs)


@after_setup_task_logger.connect
def on_task_logger_setup(
    logger_instance: Logger,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Обработчик сигнала настройки логгера задачи Celery."""
    setup_task_logger(logger_instance, *args, **kwargs)


logger.info('Celery приложение успешно инициализировано')
