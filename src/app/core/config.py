"""Настройки приложения."""

from typing import Optional

from pydantic import (
    EmailStr,
    PostgresDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_title: str = 'NAME'
    description: str = 'DESCRIPTION'
    secret: str = 'SECRET'
    first_superuser_email: Optional[EmailStr] = None
    first_superuser_password: Optional[str] = None

    database_url: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_server: Optional[str] = None
    postgres_port: Optional[int] = None
    postgres_user: Optional[str] = None

    model_config = SettingsConfigDict(env_file='infra/.env')

    @computed_field
    @property
    def db_url(self) -> str:
        """Собираем URL для подключения к БД."""
        if self.database_url:
            return self.database_url

        if all([self.postgres_user, self.postgres_server, self.postgres_db]):
            return str(PostgresDsn.build(
                scheme='postgresql+asyncpg',
                username=self.postgres_user,
                password=self.postgres_password or '',
                host=self.postgres_server,
                port=self.postgres_port or 5432,
                path=self.postgres_db,
            ))

        raise ValueError(
            "Необходимо указать либо DATABASE_URL, "
            "либо все параметры: POSTGRES_USER, POSTGRES_SERVER, POSTGRES_DB",
        )


settings = Settings()
