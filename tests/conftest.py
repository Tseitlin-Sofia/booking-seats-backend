import asyncio
import sys
from typing import AsyncGenerator

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.db import get_async_session
from app.main import app as application

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

pytest_plugins = [
    'tests.fixtures.auth',
    'tests.fixtures.database',
    'tests.fixtures.logging',
    'tests.fixtures.payloads',
]
LOG_WRITE_DELAY_SEC = 0.5

test_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope='function')
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Тестовая сессия с автоматическим откатом и очисткой."""
    async with TestSessionLocal() as test_session:
        try:
            yield test_session
        finally:
            await test_session.rollback()


@pytest.fixture(scope='function', autouse=True)
async def cleanup_engine() -> AsyncGenerator[None, None]:
    """Очищает пул соединений между тестами."""
    yield
    await test_engine.dispose()


@pytest.fixture(scope='function', autouse=True)
async def cleanup_tables(session: AsyncSession) -> AsyncGenerator[None, None]:
    """Очищает таблицы после каждого теста."""
    yield
    tables_to_clean = [
        'bookingdish',
        'bookingtableslot',
        'booking',
        'dish',
        'slot',
        '"table"',
        '"user"',
        'cafe',
    ]
    for table in tables_to_clean:
        try:
            await session.execute(text(f'DELETE FROM {table}'))
        except Exception:
            pass
    await session.commit()


@pytest.fixture(scope='function')
def app() -> FastAPI:
    """Возвращает экземпляр приложения FastAPI."""
    return application


@pytest.fixture(scope='function')
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
    ) as client:
        yield client

    await session.close()
    app.dependency_overrides.clear()
