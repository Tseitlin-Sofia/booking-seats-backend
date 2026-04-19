"""Модель интервала времени бронирования столика."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin
from app.models.booking import BookingTableSlot


class Slot(Base, CommonMixin):
    """Модель интервала времени для бронирования столика."""

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafe.id'),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f'Время бронирования: {self.start_time} - {self.end_time}, '
            f'кафе_id={self.cafe_id}'
        )
