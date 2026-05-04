import re
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import UUID, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.constants import CafeConstants
from app.core.db import Base, CommonMixin
from app.models.action import action_cafe

if TYPE_CHECKING:
    from app.models.action import Action
    from app.models.booking import Booking
    from app.models.table import Table as TableModel
    from app.models.user import User


class Cafe(CommonMixin, Base):
    """Модель кафе."""

    __table_args__ = (
        UniqueConstraint(
            'name',
            'address',
            name='cafe_unique_name_and_address',
        ),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID)
    managers: Mapped[List['User']] = relationship(
        back_populates='cafe', lazy='selectin',
    )
    tables: Mapped[List['TableModel']] = relationship(
        'Table',
        back_populates='cafe',
        lazy='selectin',
    )
    bookings: Mapped[List['Booking']] = relationship(
        'Booking',
        back_populates='cafe',
        lazy='selectin',
    )
    actions: Mapped[List['Action']] = relationship(
        secondary=action_cafe,
        back_populates='cafes',
        lazy='selectin',
    )

    @validates('phone')
    def validate_phone(self, key: str, value: str) -> str:
        """Проверка, указал ли правильный формат телефона."""
        if not re.match(CafeConstants.PHONE_FORMAT, value):
            raise ValueError(CafeConstants.ERROR_PHONE)
        return value

    def __repr__(self) -> str:
        return self.name[:CafeConstants.NAME_RESTRICTION]
