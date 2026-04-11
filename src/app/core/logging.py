# src/app/core/logging.py
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
from pathlib import Path

from loguru import logger
from loguru._logger import Logger

trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    'trace_id',
    default='SYSTEM',
)
user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    'user_id',
    default='SYSTEM',
)
username_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    'username',
    default='SYSTEM',
)


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

    log_format = (
        '{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | '
        'user_id={extra[user_id]} username={extra[username]} | '
        '{message}'
    )

    if env == 'prod':
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=False,
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )

    else:
        logger.add(
            sys.stderr,
            format=log_format,
            level=log_level,
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        log_folder = Path('logs')
        log_folder.mkdir(exist_ok=True)

        logger.add(
            log_folder / 'app.log',
            format=log_format,
            level=log_level,
            rotation='5 MB',
            retention=3,
            compression='zip',
            enqueue=True,
            backtrace=True,
            diagnose=True,
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

            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            extra_for_loguru = {
                'user_id': getattr(record, 'user_id', 'SYSTEM'),
                'username': getattr(record, 'username', 'SYSTEM'),
                'trace_id': getattr(record, 'trace_id', 'system'),
            }
            extra_for_loguru.update(getattr(record, 'extra', {}))

            logger.opt(depth=depth, exception=record.exc_info).log(
                level,
                record.getMessage(),
                **extra_for_loguru,
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    uvicorn_access = logging.getLogger('uvicorn.access')
    uvicorn_access.handlers = []
    uvicorn_access.propagate = False

    for name in [
        'uvicorn',
        'uvicorn.access',
        'uvicorn.error',
        'sqlalchemy',
        'alembic',
    ]:
        log = logging.getLogger(name)
        log.handlers = [InterceptHandler()]  # Заменяем хендлеры на наш
        log.propagate = False  # Отключаем дублирование в root-логгер
        log.setLevel(log_level)  # Устанавливаем уровень


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
