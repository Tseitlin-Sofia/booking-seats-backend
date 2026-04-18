"""Модель бронирования."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.types import Enum

from app.core.constants import BookingConstants as Constants
from app.core.db import Base, CommonMixin
from app.schemas.booking import BookingStatus

# from app.models import Table, Slot, User, Cafe


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
    table_slots: Mapped[list['BookingTableSlot']] = relationship(
        back_populates='booking',
    )

    @hybrid_property
    def date(self) -> datetime:
        """Дата бронирования (первая дата из table_slots)."""
        return sorted(self.table_slots)[0].start_time.date()

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
