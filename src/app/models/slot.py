"""Модель интервала времени бронирования столика."""

from datetime import time

from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

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
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    tables_slots = relationship(
        'BookingTableSlot',
        back_populates='slot',
        lazy='selectin',
    )

    @validates("start_time")
    def _validate_start_time(self, key: str, value: time) -> time:
        """Проверяем start_time."""
        if self.end_time is not None and value >= self.end_time:
            raise ValueError(
                "Время начала должно быть строго меньше времени окончания "
                f"(получено start={value}, end={self.end_time})",
            )
        return value

    @validates("end_time")
    def _validate_end_time(self, key: str, value: time) -> time:
        """Проверяем end_time."""
        if self.start_time is not None and self.start_time >= value:
            raise ValueError(
                "Время окончания должно быть строго больше времени начала "
                f"(получено start={self.start_time}, end={value})",
            )
        return value

    def __repr__(self) -> str:
        return (
            f'Время бронирования: {self.start_time} - {self.end_time}, '
            f'кафе_id={self.cafe_id}'
        )
