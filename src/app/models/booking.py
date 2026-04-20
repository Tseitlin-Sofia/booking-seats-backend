"""Модель бронирования."""

from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, Integer, String, Date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.types import Enum

from app.core.constants import BookingConstants as Constants
from app.core.db import Base, CommonMixin
from app.models.slot import Slot
from app.models.table import Table
from app.schemas.booking import BookingStatus


class BookingTableSlot(Base, CommonMixin):
    """Модель бронирования стола по слоту времени."""

    table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('table.id', name='fk_booking_table_slot_table_id_table'),
    )
    slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('slot.id', name='fk_booking_table_slot_slot_id_slot'),
    )
    booking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            'booking.id',
            name='fk_booking_table_slot_booking_id_booking',
        ),
    )
    booking: Mapped['Booking'] = relationship(
        'Booking',
        back_populates='table_slots',
    )
    slot: Mapped['Slot'] = relationship(
        'Slot',
        back_populates='booking_table_slots',
        lazy='selectin',
    )
    table: Mapped['Table'] = relationship(
        'Table',
        lazy='selectin',
    )
    # TODO: validate unique according to is_active


class Booking(Base, CommonMixin):
    """Модель бронирования."""

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        default=BookingStatus.BOOKING,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('user.id', name='fk_booking_user_id_user'),
    )
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafe.id', name='fk_booking_cafe_id_cafe'),
    )
    guest_number: Mapped[int] = mapped_column(
        Integer,
    )
    note: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )
    booking_date: Mapped['date'] = mapped_column(
        Date,
    )
    # TODO: Рассмотреть создание промежуточной таблицы в императивном стиле,
    # дабы избежать значения в виде списка
    table_slots: Mapped[list['BookingTableSlot']] = relationship(
        'BookingTableSlot',
        back_populates='booking',
    )


    @validates('guest_number')
    def validate_guest_number(self, key: str, value: int) -> int:
        """Валидация количества гостей."""
        if (
            value >= Constants.MIN_GUESTS
            and value <= Constants.MAX_GUESTS
        ):
            return value
        raise ValueError(Constants.GUEST_NUMBER_ERROR.format(
            Constants.MIN_GUESTS, Constants.MAX_GUESTS,
        ))

    def __repr__(self) -> str:
        return (
            Constants.REPR_FORMAT.format(
                self.id, self.status, self.user_id,
            )
        )
    # TODO: возможно стоит добавить property для статусов (
    # in_active, in_booked, in_canceled, in_completed)
