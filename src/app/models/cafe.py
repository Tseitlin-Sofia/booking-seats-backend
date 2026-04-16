from typing import List, Optional

# import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,  # Временно для заглушки до создания модели Media.
    String,
    Table as MtM_Model,
    UniqueConstraint
    # UUID
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.api.validators.cafe import is_correct_phone
from app.core.constants import CafeConstants
from app.core.db import Base, CommonMixin
from app.models import Table as TableModel, User


TEMPORARY_ID = 1  # Временно для заглушки.


cafe_managers = MtM_Model(
    "cafe_managers",
    Base.metadata,
    Column(
        "cafe_id",
        ForeignKey("cafe.id"),
        primary_key=True,
    ),
    Column(
        "user_id",
        ForeignKey("user.id"),
        primary_key=True,
    ),
)


class Cafe(CommonMixin, Base):
    """Модель кафе."""

    __table_args__ = (
        UniqueConstraint(
            "name",
            "address",
            name="cafe_unique_name_and_address"
        ),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    # photo: Mapped[Optional[uuid.UUID]] =
    # mapped_column(UUID, ForeignKey('media.id'))
    photo_id: Mapped[Optional[Integer]] = mapped_column(
        Integer, default=TEMPORARY_ID,  # Заглушка.
    )
    managers_id: Mapped[List[User]] = relationship(
        secondary=cafe_managers,
        back_populates="cafe",
        lazy="selectin",
    )
    tables: Mapped[List[TableModel]] = relationship(
        TableModel,
        back_populates="cafe",
        lazy="selectin",
    )

    @validates("phone")
    def validate_phone(self, key, value: str) -> str:
        return is_correct_phone(value)

    def __repr__(self) -> str:
        return self.name[:CafeConstants.NAME_RESTRICTION]
