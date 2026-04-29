"""Модель интервала времени бронирования столика."""

from datetime import time

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, CommonMixin


class Slot(Base, CommonMixin):
    """Модель интервала времени для бронирования столика."""

    start_time: Mapped[time] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[time] = mapped_column(DateTime, nullable=False)
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafe.id'),
        nullable=False,
    )
    table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('table.id'),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f'Время бронирования: {self.start_time} - {self.end_time}, '
            f'кафе_id={self.cafe_id}, столик_id={self.table_id}'
        )
