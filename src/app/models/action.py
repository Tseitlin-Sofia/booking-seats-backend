import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import UUID, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.cafe import Cafe


action_cafe = Table(
    "action_cafe",
    Base.metadata,
    Column(
        "action_id",
        ForeignKey("action.id"),
        primary_key=True,
    ),
    Column(
        "cafe_id",
        ForeignKey("cafe.id"),
        primary_key=True,
    ),
)


class Action(CommonMixin, Base):
    """Модель акции."""

    description: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )
    photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)
    cafes: Mapped[List['Cafe']] = relationship(
        secondary=action_cafe,
        back_populates="actions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f'Акция с id {self.id}'
