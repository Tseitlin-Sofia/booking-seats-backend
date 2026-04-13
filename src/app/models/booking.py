"""Модель бронирования."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Mapped, String
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.types import Enum

from app.core import Base, CommonMixin
from app.core.constants import BookingConstants as Constants
from app.schemas import BookingStatus


class BookingTableSlot(Base, CommonMixin):
    """Модель бронирования стола по слоту времени."""

    table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('tables.id', name='fk_booking_table_slot_table_id_table'),
    )
    slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('slots.id', name='fk_booking_table_slot_slot_id_slot'),
    )
    booking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            'bookings.id',
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
        ForeignKey('cafes.id', name='fk_booking_cafe_id_cafe'),
    )
    guest_number: Mapped[int] = mapped_column(
        Integer,
        validate=(
            lambda value: (
                value >= Constants.MIN_GUESTS
                and value <= Constants.MAX_GUESTS
            ),
        ),
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
