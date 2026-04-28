"""Модель блюда в меню кафе."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.booking import BookingDish


class Dish(CommonMixin, Base):
    """Модель блюда в меню кафе."""

    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey('cafe.id'))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    booking_dishes: Mapped[list['BookingDish']] = relationship(
        back_populates='dish',
    )
