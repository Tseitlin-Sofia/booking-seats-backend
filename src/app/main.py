"""Основной запускаемый файл приложения."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.routers import main_router
from app.core.config import settings
from app.core.init_db import create_first_superuser


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения."""
    await create_first_superuser()
    yield


app = FastAPI(
    title=settings.app_title,
    lifespan=lifespan,
)

app.include_router(main_router)
