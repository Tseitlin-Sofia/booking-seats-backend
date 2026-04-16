"""Модуль централизованного логирования приложения.

Предоставляет единую систему логирования на базе loguru для всего проекта.
Обеспечивает:
- Структурированный вывод логов в консоль и файл с ротацией.
- Автоматическое обогащение записей контекстными данными.
- Перехват и унификацию логов от сторонних компонентов.
- Асинхронную неблокирующую запись для production-нагрузок.
"""

import contextvars
import logging
import sys

from loguru import logger
from loguru._logger import Logger

from app.core.constants import LoggingConstants

trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    'trace_id',
    default=LoggingConstants.SYSTEM_MESSAGE_NAME_ALLIAS,
)
user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    'user_id',
    default=LoggingConstants.SYSTEM_MESSAGE_NAME_ALLIAS,
)
username_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    'username',
    default=LoggingConstants.SYSTEM_MESSAGE_NAME_ALLIAS,
)


class InterceptHandler(logging.Handler):
    """Обработчик для перехвата записей из стандартной библиотеки logging.

    Необходим для интеграции логов от Uvicorn, SQLAlchemy и Alembic
    в единую систему loguru с сохранением контекста.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Обработка записи лога и перенаправление в loguru.

        Автоматически определяет правильный уровень логирования
        и вычисляет глубину стека вызовов, чтобы в логе
        указывался реальный файл-источник сообщения, а не этот модуль.

        Args:
            record: Объект записи из стандартной библиотеки logging.

        Returns:
            None

        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = (
            sys._getframe(LoggingConstants.INITIAL_STACK_FRAME_DEPTH),
            LoggingConstants.INITIAL_STACK_FRAME_DEPTH,
        )
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        extra = {
            'user_id': getattr(
                record,
                'user_id',
                LoggingConstants.SYSTEM_MESSAGE_NAME_ALLIAS,
            ),
            'username': getattr(
                record,
                'username',
                LoggingConstants.SYSTEM_MESSAGE_NAME_ALLIAS,
            ),
            'trace_id': getattr(
                record,
                'trace_id',
                LoggingConstants.SYSTEM_MESSAGE_NAME_ALLIAS,
            ),
        }
        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
            **extra,
        )


def _configure_logger(name: str, level: str) -> None:
    """Настраивает логгер.

    Служебный метод, заменяющий хендлеры на InterceptHandler
    и отключающий пропагацию.
    """
    log = logging.getLogger(name)
    log.handlers = [InterceptHandler()]
    log.propagate = False
    log.setLevel(level)


def setup_logging(env: str = 'dev', log_level: str = 'INFO') -> None:
    """Инициализация системы логирования.

    Вызывается однократно при старте приложения.
    Выполняет следующие действия:
    1. Очищает конфигурацию loguru по умолчанию.
    2. Настраивает единый формат вывода (время|уровень|пользователь|сообщение).
    3. Подключает вывод в stdout для docker и в файл с ротацией.
    4. Перехватывает логи от  Uvicorn, SQLAlchemy и перенаправляет их в loguru.

    Args:
        env: Режим окружения ('dev'/'prod'). Влияет на формат и безопасность.
        log_level: Уровень логирования ('DEBUG', 'INFO', 'WARNING' и т.д.).

    Returns:
        None

    Side Effects:
        - Создаёт директорию 'logs/' при необходимости.
        - Модифицирует глобальную конфигурацию logging.root.
        - Отключает дублирующий access-лог uvicorn.access.

    """
    logger.remove()
    LoggingConstants.LOGGING_FOLDER.mkdir(parents=True, exist_ok=True)
    if env == 'prod':
        logger.add(
            sys.stdout,
            format=LoggingConstants.LOGGING_FORMAT_STRING,
            level=log_level,
            colorize=LoggingConstants.PROD_MODE_COLORIZE_LOGS,
            enqueue=LoggingConstants.PROD_MODE_ENQUEUE_LOGS,
            backtrace=LoggingConstants.PROD_MODE_BACKTRACE_LOGS,
            diagnose=LoggingConstants.PROD_MODE_DIAGNOSE_LOGS,
        )
        logger.add(
            LoggingConstants.LOG_FILES_PATH,
            format=LoggingConstants.LOGGING_FORMAT_STRING,
            level=log_level,
            rotation=LoggingConstants.ROTATION_FILE_SIZE,
            retention=LoggingConstants.RETENTION_FILES_COUNT,
            compression=LoggingConstants.LOG_FILES_COMPRESSION_TYPE,
            enqueue=LoggingConstants.PROD_MODE_ENQUEUE_LOGS,
            backtrace=LoggingConstants.PROD_MODE_BACKTRACE_LOGS,
            diagnose=LoggingConstants.PROD_MODE_DIAGNOSE_LOGS,
        )
    else:
        logger.add(
            sys.stderr,
            format=LoggingConstants.LOGGING_FORMAT_STRING,
            level=log_level,
            colorize=LoggingConstants.DEV_MODE_COLORIZE_LOGS,
            enqueue=LoggingConstants.DEV_MODE_ENQUEUE_LOGS,
            backtrace=LoggingConstants.DEV_MODE_BACKTRACE_LOGS,
            diagnose=LoggingConstants.DEV_MODE_DIAGNOSE_LOGS,
        )
        LoggingConstants.LOGGING_FOLDER.mkdir(exist_ok=True)

        logger.add(
            LoggingConstants.LOG_FILES_PATH,
            format=LoggingConstants.LOGGING_FORMAT_STRING,
            level=log_level,
            rotation=LoggingConstants.ROTATION_FILE_SIZE,
            retention=LoggingConstants.RETENTION_FILES_COUNT,
            compression=LoggingConstants.LOG_FILES_COMPRESSION_TYPE,
            enqueue=LoggingConstants.DEV_MODE_ENQUEUE_LOGS,
            backtrace=LoggingConstants.DEV_MODE_BACKTRACE_LOGS,
            diagnose=LoggingConstants.DEV_MODE_DIAGNOSE_LOGS,
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in LoggingConstants.LOGGERS_TO_INTERCEPT:
        _configure_logger(name, log_level)

    # Access-логи отключены отдельно, поскольку они дублируют функционал
    # кастомного middleware не предоставляя при этом нужного контекста.
    logging.getLogger('uvicorn.access').handlers = []
    logging.getLogger('uvicorn.access').propagate = False


def get_logger() -> Logger:
    """Фабричная функция для получения настроенного логера.

    Возвращает экземпляр логера loguru с уже привязанным контекстом
    - trace_id: уникальный идентификатор текущего запроса
    - user_id: идентификатор пользователя (или 'SYSTEM')
    - username: имя пользователя (или 'SYSTEM')

    Благодаря contextvars, значения автоматически соответствуют текущему
    асинхронному запросу, даже при параллельной обработке.

    Returns:
        Logger: Настроенный экземпляр логера loguru, готовый к использованию.


    """
    return logger.bind(  # type: ignore[reportReturnType]
        user_id=user_id_ctx.get(),
        username=username_ctx.get(),
        trace_id=trace_id_ctx.get(),
    )
