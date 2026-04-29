"""Модель бронирования."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.types import Enum

from app.core.constants import BookingConstants as Constants
from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.cafe import Cafe
    from app.models.dish import Dish
    from app.models.user import User


class BookingStatus(StrEnum):
    """Статус бронирования."""

    BOOKING = 'BOOKING'
    CANCELED = 'CANCELED'
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'


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
    booking = relationship('Booking', back_populates='tables_slots')


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
    tables_slots: Mapped[list['BookingTableSlot']] = relationship(
        'BookingTableSlot',
        back_populates='booking',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    user: Mapped['User'] = relationship(
        'User',
        back_populates='bookings',
        lazy='selectin',
    )
    cafe: Mapped['Cafe'] = relationship(
        'Cafe',
        back_populates='bookings',
        lazy='selectin',
    )
    pre_order_items: Mapped[list['BookingDish']] = relationship(
        'BookingDish',
        back_populates='booking',
        lazy='selectin',
    )

    @validates('guest_number')
    def validate_guest_number(self, key: str, value: int) -> int:
        """Валидация количества гостей."""
        if value >= Constants.MIN_GUESTS and value <= Constants.MAX_GUESTS:
            return value
        raise ValueError(
            Constants.GUEST_NUMBER_ERROR.format(
                Constants.MIN_GUESTS,
                Constants.MAX_GUESTS,
            ),
        )

    @validates('booking_date')
    def validate_booking_date(self, key: str, value: date) -> date:
        """Валидация даты бронирования (нельзя бронировать в прошлом)."""
        if value >= date.today():
            return value
        raise ValueError(Constants.DATE_ERROR)

    def __repr__(self) -> str:
        return Constants.REPR_FORMAT.format(
            self.id,
            self.status,
            self.user_id,
        )

    # TODO: возможно стоит добавить property для статусов (
    # in_active, in_booked, in_canceled, in_completed)


class BookingDish(CommonMixin, Base):
    """Позиция предзаказа, привязанная к бронированию."""

    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey('booking.id'))
    dish_id: Mapped[int] = mapped_column(Integer, ForeignKey('dish.id'))
    quantity: Mapped[int] = mapped_column(Integer)
    price_at_order: Mapped[float] = mapped_column(Float)
    booking: Mapped['Booking'] = relationship(
        'Booking',
        back_populates='pre_order_items',
    )
    dish: Mapped['Dish'] = relationship(
        'Dish',
        back_populates='booking_dishes',
    )
