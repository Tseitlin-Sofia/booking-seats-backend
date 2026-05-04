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
from app.core.exceptions import UserValidationError
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
        example='user@yandex.ru',
    )
    phone: str | None = Field(
        None,
        max_length=UserConstants.MAX_PHONE_LENGTH,
        example='+71234567890',
    )
    tg_id: str | None = Field(
        None,
        max_length=UserConstants.MAX_TG_ID_LENGTH,
    )

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, phone: str | None) -> str | None:
        """Проверяет корректность ввода телефона."""
        if phone is not None:
            if not UserConstants.PHONE_REGEX.match(phone):
                raise UserValidationError(
                    'Телефон должен начинаться +7 и содержать 10 цифр.',
                )
        return phone


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    password: str = Field(
        ...,
        max_length=UserConstants.MAX_PASSWORD_LENGTH,
        min_length=UserConstants.MIN_PASSWORD_LENGTH,
        example='qwer1',
    )

    @model_validator(mode='after')
    def validate_email_or_phone_required(self) -> 'UserCreate':
        """Валидатор проверяет, что задано хотя бы одно из полей.

        Проверяет, что email или phone не пустые.
        """
        if not self.email and not self.phone:
            raise UserValidationError(
                'Хотя бы одно из следующих полей '
                'должно быть заполнено: email, phone',
            )
        return self

    @field_validator('password')
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Проверяет пароль на соответствие заданным условиям."""
        if (
            (len(password) < UserConstants.MIN_PASSWORD_LENGTH)
            or (len(password) > UserConstants.MAX_PASSWORD_LENGTH)
        ):
            raise UserValidationError(
                'Пароль должен '
                f'содержать минимум {UserConstants.MIN_PASSWORD_LENGTH} '
                f'и не более {UserConstants.MAX_PASSWORD_LENGTH}.',
            )

        if not UserConstants.PASSWORD_REGEX.match(password):
            raise UserValidationError(
                'Пароль должен содержать хотя бы одну букву и одну цифру.',
            )
        return password

    @field_validator('username')
    @classmethod
    def validate_username_not_empty(cls, username: str | None) -> str | None:
        """Username не может быть пустым или null при обновлении."""
        if username is not None and not username.strip():
            raise UserValidationError('Имя пользователя не может быть пустым')
        return username


class UserUpdate(UserBase):
    """Схема для обновления данных пользователя."""

    username: str | None = Field(
        None, max_length=UserConstants.MAX_USERNAME_LENGTH,
    )
    role: UserRole | None = Field(None, example='user')
    password: str | None = Field(
        None, max_length=UserConstants.MAX_PASSWORD_LENGTH, example='qwer1',
    )
    is_active: bool | None = Field(None)

    @field_validator('password')
    @classmethod
    def validate_password(cls, password: str | None) -> str | None:
        """Проверяет пароль на соответствие заданным условиям."""
        if password is None:
            return password

        if (
            (len(password) < UserConstants.MIN_PASSWORD_LENGTH)
            or (len(password) > UserConstants.MAX_PASSWORD_LENGTH)
        ):
            raise UserValidationError(
                'Пароль должен '
                f'содержать минимум {UserConstants.MIN_PASSWORD_LENGTH} '
                f'и не более {UserConstants.MAX_PASSWORD_LENGTH}.',
            )

        if not UserConstants.PASSWORD_REGEX.match(password):
            raise UserValidationError(
                'Пароль должен содержать хотя бы одну букву и одну цифру.',
            )
        return password

    @field_validator('username')
    @classmethod
    def validate_username_not_empty(cls, username: str | None) -> str | None:
        """Username не может быть пустым или null при обновлении."""
        if (
            (username is not None and not username.strip()) or username is None
        ):
            raise UserValidationError('Имя пользователя не может быть пустым')
        return username

    @field_validator('role')
    @classmethod
    def validate_role_not_null(cls, role: UserRole | None) -> UserRole | None:
        """Роль не может быть явно установлена в None."""
        if role is None:
            raise UserValidationError('Роль не может быть пустой')
        return role

    @field_validator('is_active')
    @classmethod
    def validate_is_active_not_null(
        cls, is_active: bool | None,
    ) -> bool | None:
        """is_active не может быть явно установлен в None."""
        if is_active is None:
            raise UserValidationError('Статус активности не может быть пустым')
        return is_active


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
