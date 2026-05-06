"""Основной запускаемый файл приложения."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError

from app.api.routers import main_router
from app.core.config import settings
from app.core.exception_handlers import (
    http_exception_handler,
    server_exception_handler,
    validation_exception_handler,
)
from app.core.logging import get_logger, setup_logging
from app.core.middleware import LoggingMiddleware

setup_logging(env=settings.environment, log_level=settings.log_level)

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения."""
    logger.info(
        'Инициализация запуска приложения.',
    )
    if settings.environment != 'prod':
        logger.warning(
            'Запуск в режиме разработки, '
            + 'не используйте режим разработки на продакшен сервере!',
        )

    logger.info('Инициализация приложения завершена.')
    yield
    logger.complete()
    logger.info('Приложение остановлено.')


app = FastAPI(
    title=settings.app_title,
    lifespan=lifespan,
)
app.add_middleware(LoggingMiddleware)
if settings.environment != 'prod':
    from fastapi_sqlalchemy_profiler import (
        SQLProfilerMiddleware,
        profiler_router,
    )

    app.add_middleware(SQLProfilerMiddleware, enabled=True)
    app.include_router(profiler_router)

app.include_router(main_router)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, server_exception_handler)

# uvicorn app.main:app --reload
