import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.cafe import Cafe


class Action(CommonMixin, Base):
    """Модель акции."""

    description: Mapped[str] = mapped_column(String, nullable=False)
    photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)
    cafes: Mapped[List['Cafe']] = relationship(
        back_populates="action", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f'Акция с id {self.id}'
