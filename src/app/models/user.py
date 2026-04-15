from enum import StrEnum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
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
    cafe_id: Mapped[int | None] = mapped_column(
        ForeignKey('cafe.id', ondelete='RESTRICT'),
        nullable=True,
    )
    # TODO Добавить relationship для модели Cafe.

    __table_args__ = (
        CheckConstraint(
            'email is not null OR phone is not null',
            name='ch_user_email_or_phone_required',
        ),
    )

    def __str__(self) -> str:
        return self.username
