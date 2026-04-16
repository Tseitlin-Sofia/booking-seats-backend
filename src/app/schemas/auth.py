"""Схемы для аутентификации."""

from pydantic import BaseModel, field_validator


class AuthData(BaseModel):
    """Схема для входа пользователя."""

    login: str
    password: str

    @field_validator('login')
    @classmethod
    def validate_login(cls, v: str) -> str:
        """Проверяет, что логин не пустой."""
        if not v or not v.strip():
            raise ValueError('Login is required')
        return v.strip()


class AuthToken(BaseModel):
    """Схема ответа с токеном."""

    access_token: str
    token_type: str = 'bearer'
