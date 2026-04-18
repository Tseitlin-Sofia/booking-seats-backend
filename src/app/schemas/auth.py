"""Схемы для аутентификации."""

from pydantic import BaseModel, field_validator

from app.schemas.validators.auth import validate_login_not_empty


class AuthData(BaseModel):
    """Схема для входа пользователя."""

    login: str
    password: str

    @field_validator('login')
    @classmethod
    def validate_login(cls, v: str) -> str:
        """Проверяет, что логин не пустой."""
        return validate_login_not_empty(v)


class AuthToken(BaseModel):
    """Схема ответа с токеном."""

    access_token: str
    token_type: str = 'bearer'
