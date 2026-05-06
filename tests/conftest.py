import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.core.config import settings
from app.core.db import create_async_engine, get_async_session
from app.core.logging import get_logger
from app.main import app as application
from tests.sql import sql

logger = get_logger()

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

pytest_plugins = [
    'tests.fixtures.auth',
    'tests.fixtures.database',
    'tests.fixtures.logging',
    'tests.fixtures.payloads',
    'tests.fixtures.celery',
]
LOG_WRITE_DELAY_SEC = 0.5
SQL_DIR = Path(__file__).parent / 'sql'
DATABASE_URL = (
    f'postgresql+asyncpg://{settings.postgres_user}'
    f':{settings.postgres_password.get_secret_value()}'
    f'@localhost:5432/{settings.postgres_db}'
)


@pytest.fixture(autouse=True)
def celery_eager_mode() -> Generator:
    """Celery задачи выполняются синхронно, без Redis."""
    from app.celery.celery_app import celery_app

    celery_app.conf.update(task_always_eager=True)
    yield
    celery_app.conf.update(task_always_eager=False)


@pytest_asyncio.fixture(scope='function')
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Фикстура движка базы данных."""
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope='function')
async def cleanup_engine(engine) -> AsyncGenerator[None, None]:
    """Очищает пул соединений между тестами."""
    yield
    await engine.dispose()


@pytest_asyncio.fixture(scope='function', autouse=True)
async def setup_test_environment(engine) -> AsyncGenerator[None, None]:
    """Однократная настройка тестового окружения."""
    async with engine.begin() as conn:
        result = await conn.execute(text(sql.check_schema_exists))
        schema_exists = result.fetchone() is not None

        if not schema_exists:
            await conn.execute(text(sql.create_test_schema))
            logger.info('Тестовое пространство БД инициализированно.')
        else:
            result = await conn.execute(text(sql.check_tables_exist))
            has_tables = result.scalar()
            if not has_tables:
                await conn.execute(text(sql.create_test_schema))
                logger.info(
                    'Структура таблиц скопирована в тестовое пространство.',
                )
            else:
                logger.info('Тестовое пространство имен уже существует.')

    yield

    logger.info('Очистка тестовой среды...')
    async with engine.begin() as conn:
        await conn.execute(text(sql.reset_search_path))
        await conn.execute(text(sql.drop_test_schema))
        logger.info('Тестовое пространство имен удалено.')
    logger.info('Тестовая среда успешно очищена!')


@pytest_asyncio.fixture(scope='function')
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Тестовая сессия с search_path = test."""
    async with engine.connect() as conn:
        await conn.execute(text(sql.set_search_path))
        await conn.commit()

    async with async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )() as test_session:
        try:
            yield test_session
        finally:
            await test_session.rollback()


@pytest.fixture(scope='function')
def app() -> FastAPI:
    """Возвращает экземпляр приложения FastAPI."""
    return application


@pytest_asyncio.fixture(scope='function')
async def async_client(
    app: FastAPI,
    session: AsyncSession,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Асинхронный клиент для тестов."""

    async def override_get_async_session() -> AsyncGenerator[
        AsyncSession,
        None,
    ]:
        yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url='http://test',
        timeout=httpx.Timeout(30.0),
    ) as client:
        yield client

    app.dependency_overrides.clear()
