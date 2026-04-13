"""Модель стола в кафе."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.cafe import Cafe


class Table(CommonMixin, Base):
    """Стол для бронирования в кафе."""

    __tablename__ = "table"

    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cafe.id"),
        nullable=False,
    )
    seat_number: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint(
            'seat_number > 0', name='ck_table_seat_number_positive'
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    cafe: Mapped[Cafe] = relationship(
        "Cafe",
        back_populates="tables",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Строковое представление стола."""
        return (
            f"<Table {self.id}: {self.seat_number} seats, "
            f"cafe={self.cafe_id}>"
        )
