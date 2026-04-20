"""Настройки приложения."""

from pathlib import Path
from typing import Optional

from pydantic import EmailStr, computed_field
from pydantic.types import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_title: str = 'NAME'
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    description: str = 'DESCRIPTION'
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None
    first_superuser_username: Optional[str] = None
    first_superuser_phone: Optional[str] = None
    environment: str = 'dev'
    log_level: str = 'INFO'
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_server: str
    postgres_port: int = 5432

    # Основные параметры JWT
    jwt_secret_key: str = 'your-super-secret-key'
    jwt_algorithm: str = 'HS256'
    jwt_token_inactivity_minutes: int = 30

    @computed_field
    @property
    def database_url(self) -> str:
        """Строка подключения к PostgreSQL."""
        return (
            f'postgresql+asyncpg://{self.postgres_user}'
            f':{self.postgres_password}'
            f'@{self.postgres_server}'
            f':{self.postgres_port}'
            f'/{self.postgres_db}'
        )

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()

# Константы для обратной совместимости
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
TOKEN_INACTIVITY_MINUTES = settings.jwt_token_inactivity_minutes
