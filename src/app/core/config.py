"""Настройки приложения."""

from typing import Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_title: str = 'NAME'
    description: str = 'DESCRIPTION'
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None

    database_url: Optional[str] = None

    model_config = SettingsConfigDict(env_file='infra/.env')


settings = Settings()
