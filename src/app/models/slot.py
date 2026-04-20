"""Модель интервала времени бронирования столика."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, CommonMixin


class Slot(Base, CommonMixin):
    """Модель интервала времени для бронирования столика."""

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafe.id'),
        nullable=False,
<<<<<<< HEAD
    )
    booking_table_slots: Mapped[list['BookingTableSlot']] = relationship(
        'BookingTableSlot',
        back_populates='slot',
        lazy='selectin',
=======
>>>>>>> origin
    )

    def __repr__(self) -> str:
        return (
            f'Время бронирования: {self.start_time} - {self.end_time}, '
            f'кафе_id={self.cafe_id}'
        )
