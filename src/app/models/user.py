from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.constants import UserConstants
from app.core.db import Base, CommonMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.cafe import Cafe


class UserRole(StrEnum):
    """Роли пользователей в системе."""

    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'


class User(CommonMixin, Base):
    """Модель пользователя."""

    username: Mapped[str] = mapped_column(
        String(UserConstants.MAX_USERNAME_LENGTH),
        unique=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(UserConstants.MAX_PASSWORD_LENGTH),
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(
        String(UserConstants.MAX_EMAIL_LENGTH),
        unique=True,
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(UserConstants.MAX_PHONE_LENGTH),
        unique=True,
        nullable=True,
    )
    tg_id: Mapped[str | None] = mapped_column(
        String(UserConstants.MAX_TG_ID_LENGTH),
        unique=True,
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
        ),
        default=UserConstants.DEFAULT_USER_ROLE,
    )
    cafes: Mapped[list["Cafe"]] = relationship(
        "Cafe",
        secondary="cafe_managers",
        back_populates="managers_id",
        lazy="selectin",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="user",
        lazy="selectin",
    )

    @property
    def is_admin(self) -> bool:
        """Является ли пользователь администратором."""
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self) -> bool:
        """Является ли пользователь менеджером."""
        return self.role == UserRole.MANAGER

    @property
    def is_user(self) -> bool:
        """Является ли пользователем."""
        return self.role == UserRole.USER

    __table_args__ = (
        CheckConstraint(
            'email is not null OR phone is not null',
            name='ch_user_email_or_phone_required',
        ),
    )

    @validates("cafe_id")
    def validate_manager(self, key: int, value: int) -> int:
        """Проверка, что только менеджер может быть привязан к кафе."""
        if value is not None and not self.is_manager:
            raise ValueError("К кафе можно привязать только менеджера!")
        return value

    def __str__(self) -> str:
        return self.username
