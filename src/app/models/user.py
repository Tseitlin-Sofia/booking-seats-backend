from enum import StrEnum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import UserConstants
from app.core.db import Base, CommonMixin


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
    email: Mapped[str] = mapped_column(
        String(UserConstants.MAX_EMAIL_LENGTH),
        unique=True,
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(UserConstants.MAX_PHONE_LENGTH),
        unique=True,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
        ),
        default='user',
    )
