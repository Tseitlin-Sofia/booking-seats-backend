"""Основной запускаемый файл приложения."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.routers import main_router
from app.core.config import settings
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
    logger.info('Приложение остановлено.')


app = FastAPI(
    title=settings.app_title,
    lifespan=lifespan,
)
app.add_middleware(LoggingMiddleware)
app.include_router(main_router)
