"""Модель кафе."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.table import Table

from app.core.db import Base, CommonMixin


class Cafe(CommonMixin, Base):
    """Кафе, в котором можно бронировать столы."""

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    photo_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    tables: Mapped[list[Table]] = relationship(
        "Table",
        back_populates="cafe",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Строковое представление кафе."""
        return f"<Cafe {self.id}: {self.name}>"
