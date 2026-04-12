from pathlib import Path


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
    INITIAL_STACK_FRAME_DEPTH: int = 6
    ROTATION_FILE_SIZE: str = '5 MB'
    RETENTION_FILES_COUNT: int = 3
    LOG_FILES_COMPRESSION_TYPE: str = 'zip'
    LOGGERS_TO_INTERCEPT: list = [
        'uvicorn',
        'uvicorn.error',
        'sqlalchemy',
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
