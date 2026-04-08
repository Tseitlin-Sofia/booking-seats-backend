"""Настройки приложения."""

from typing import Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_title: str = 'NAME'
    description: str = 'DESCRIPTION'
    database_url: str | None = 'postgresql+asyncpg://user:pass@host/db'
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()
