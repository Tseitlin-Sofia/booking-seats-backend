"""Модель бронирования."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum

if TYPE_CHECKING:
    from app.models.slot import Slot  # noqa: F401
    from app.models.table import Table  # noqa: F401

from app.core.constants import BookingConstants as Constants
from app.core.db import Base, CommonMixin
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
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
        # метод validate ломает запуск проекта, нужно разобраться
        # validate=(
        #    lambda value: (
        #        value >= Constants.MIN_GUESTS
        #        and value <= Constants.MAX_GUESTS
        #    ),
        # ),
    )
    note: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )
    table_slots: Mapped[list['BookingTableSlot']] = relationship(
        back_populates='booking',
    )
    #  TODO:
        #  TableSlots backref check
        #  computed date (from 1st table_slot)
        #  Нужна валидация консистентности is_active на статусы BOOKING, ACTIVE
        #  is_active = True
        #  Остальные статусы (CANCELLED, COMPLETED) должны иметь
        #  is_active = False

    def __repr__(self) -> str:
        return (
            Constants.REPR_FORMAT.format(
                self.id, self.status, self.user_id,
            )
        )
