"""Модуль для работы с базой данных."""

import datetime
from typing import Self

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)

from app.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""


class CommonMixin:
    """Миксин для общих полей моделей.

    Каждая таблица обязательно содержит:
    id, created_at, updated_at, is_active.
    """

    @declared_attr
    @classmethod
    def __tablename__(cls: type[Self]) -> str:
        """Имя таблицы = имя класса в lowercase."""
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default='true',
        nullable=False,
    )


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:
    """Асинхронный генератор сессий."""
    async with AsyncSessionLocal() as async_session:
        yield async_session
