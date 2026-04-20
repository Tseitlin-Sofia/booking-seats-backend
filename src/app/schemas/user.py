from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.core.constants import UserConstants
from app.models.user import UserRole


class UserBase(BaseModel):
    """Базовая схема пользователя с общими полями."""

    username: str = Field(
        ...,
        max_length=UserConstants.MAX_USERNAME_LENGTH,
    )
    email: EmailStr | None = Field(
        None,
        max_length=UserConstants.MAX_EMAIL_LENGTH,
    )
    phone: str | None = Field(
        None,
        max_length=UserConstants.MAX_PHONE_LENGTH,
    )
    tg_id: str | None = Field(
        None,
        max_length=UserConstants.MAX_TG_ID_LENGTH,
    )

    @field_validator('phone')
    @classmethod
    def validate_email(cls, phone: str | None) -> str | None:
        """Проверяет корректность ввода телефона."""
        if phone is not None:
            if not UserConstants.PHONE_REGEX.match(phone):
                raise ValueError(
                    'Телефон должен начинаться +7 и содержать 10 цифр.',
                )
        return phone


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    password: str = Field(
        ...,
        max_length=UserConstants.MAX_PASSWORD_LENGTH,
    )

    @model_validator(mode='after')
    def validate_email_or_phone_required(self) -> 'UserCreate':
        """Валидатор проверяет, что задано хотя бы одно из полей.

        Проверяет, что email или phone не пустые.
        """
        if not self.email and not self.phone:
            raise ValueError(
                'Хотя бы одно из следующих полей '
                'должно быть заполнено: email, phone',
            )
        return self


class UserUpdate(UserBase):
    """Схема для обновления данных пользователя."""

    username: str | None = Field(
        None, max_length=UserConstants.MAX_USERNAME_LENGTH,
    )
    role: UserRole | None = Field(None)
    password: str | None = Field(
        None, max_length=UserConstants.MAX_PASSWORD_LENGTH,
    )
    is_active: bool | None = Field(None)


class UserInfo(UserBase):
    """Схема для предоставления всех данных о пользователе."""

    id: int = Field(...)
    role: UserRole = Field(...)
    is_active: bool = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)


class UserShortInfo(UserBase):
    """Схема для предоставления данных о пользователе."""

    id: int = Field(...)

    model_config = ConfigDict(from_attributes=True)


class AdminCreate(UserCreate):
    """Схема для создания суперпользователя."""

    role: UserRole = Field(UserRole.ADMIN, frozen=True)
