"""Модуль для работы с базой данных."""

from typing import Self

# from sqlalchemy import Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import (
    AsyncSession,
    DeclarativeBase,
    # Mapped,
    # mapped_column,
    declared_attr,
)

from app.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""


class CommonMixin:
    """Миксин для общих полей моделей."""

    @declared_attr
    @classmethod
    def __tablename__(cls: type[Self]) -> str:
        return cls.__name__.lower()

    # id: Mapped[int] = mapped_column(Integer, primary_key=True)  # TODO: uuid?


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncSession:
    """Асинхронный генератор сессий."""
    async with AsyncSessionLocal() as async_session:
        yield async_session
