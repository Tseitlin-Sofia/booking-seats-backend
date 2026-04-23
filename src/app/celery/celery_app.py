from celery import Celery
import os

# Получение настроек из переменных окружения
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Создаём экземпляр Celery
celery_app = Celery(
    "fastapi_celery",  # Имя приложения
    broker=CELERY_BROKER_URL,  # URL брокера сообщений
    backend=CELERY_RESULT_BACKEND,  # URL бэкенда результатов
    include=["app.celery.tasks"]  # Модули с задачами для автоматического импорта
)

# Конфигурация Celery
celery_app.conf.update(
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
    worker_prefetch_multiplier=1,  # Количество задач, которые воркер берёт одновременно
    worker_max_tasks_per_child=1000,  # Максимальное количество задач на дочерний процесс
    
    # Настройки очередей
    task_default_queue="default",  # Очередь по умолчанию
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.file_tasks.*": {"queue": "files"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },
    
    # Настройки повторных попыток
    task_acks_late=True,  # Подтверждать выполнение задачи только после успешного завершения
    worker_disable_rate_limits=False,  # Не отключать ограничения скорости
    
    # Настройки логирования
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

# Опционально: настройка для продакшена
# celery_app.conf.update(
#     broker_url="redis://:password@redis-host:6379/0",
#     result_backend="redis://:password@redis-host:6379/0",
#     security_key="your-security-key",
#     task_serializer="json",
#     result_serializer="json",
#     accept_content=["json"],
#     enable_utc=True,
#     timezone="Europe/Moscow",
# )