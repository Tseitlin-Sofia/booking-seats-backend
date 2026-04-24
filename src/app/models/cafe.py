import re
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import String, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.constants import CafeConstants
from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.table import Table as TableModel
    from app.models.user import User


class Cafe(CommonMixin, Base):
    """Модель кафе."""

    __table_args__ = (
        UniqueConstraint(
            "name",
            "address",
            name="cafe_unique_name_and_address",
        ),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID)
    managers_id: Mapped[List['User']] = relationship(
        back_populates="cafe", lazy="selectin",
    )
    tables: Mapped[List['TableModel']] = relationship(
        'Table',
        back_populates="cafe",
        lazy="selectin",
    )
    bookings: Mapped[List['Booking']] = relationship(
        'Booking',
        back_populates="cafe",
        lazy="selectin",
    )

    @validates("phone")
    def validate_phone(self, key: str, value: str) -> str:
        """Проверка, указал ли правильный формат телефона."""
        if not re.match(CafeConstants.PHONE_FORMAT, value):
            raise ValueError(CafeConstants.ERROR_PHONE)
        return value

    def __repr__(self) -> str:
        return self.name[:CafeConstants.NAME_RESTRICTION]
