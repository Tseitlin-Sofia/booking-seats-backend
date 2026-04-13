"""Модуль для работы с базой данных."""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Boolean, DateTime, Integer
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
from sqlalchemy.sql import func

from app.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""


class CommonMixin:
    """Миксин для общих полей моделей."""

    @declared_attr
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий."""
    async with AsyncSessionLocal() as async_session:
        try:
            yield async_session
        except Exception:
            await async_session.rollback()
            raise
