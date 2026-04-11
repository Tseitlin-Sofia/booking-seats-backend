"""Настройки приложения."""

from typing import Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_title: str = 'NAME'
    version: str = '0.0.1'
    description: str = 'DESCRIPTION'
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None
    environment: str = 'dev'
    log_level: str = 'INFO'
    database_url: Optional[str] = None

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
