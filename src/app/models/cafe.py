from typing import List, Optional

# import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,  # Временно для заглушки до создания модели Media.
    String,
    Table,
    # UUID
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CafeConstants
from app.core.db import Base, CommonMixin
from app.models.user import User

TEMPORARY_ID = 1  # Временно для заглушки.


cafe_managers = Table(
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

    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    # photo: Mapped[Optional[uuid.UUID]] =
    # mapped_column(UUID, ForeignKey('media.id'))
    photo_id: Mapped[Optional[Integer]] = mapped_column(
        Integer, default=TEMPORARY_ID,  # Заглушка.
    )
    managers_id: Mapped[List[User]] = relationship(secondary=cafe_managers)
    tables: Mapped[List["Table"]] = relationship(
        "Table",
        back_populates="cafe",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return self.name[:CafeConstants.NAME_RESTRICTION]
