"""Модель интервала времени бронирования столика."""

from datetime import time

from sqlalchemy import ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin


class Slot(Base, CommonMixin):
    """Модель интервала времени для бронирования столика.

    Слот описывает только временной интервал в рамках конкретного кафе.
    Связь "стол ↔ слот ↔ бронирование" хранится в таблице BookingTableSlot
    и устанавливается в момент бронирования.
    """

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafe.id'),
        nullable=False,
    )
    tables_slots = relationship(
        'BookingTableSlot',
        back_populates='slot',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'Время бронирования: {self.start_time} - {self.end_time}, '
            f'кафе_id={self.cafe_id}'
        )
