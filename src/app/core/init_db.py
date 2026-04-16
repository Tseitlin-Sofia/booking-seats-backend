# """Инициализация базы данных."""

import argparse
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_async_session
from app.crud.user import user_crud
from app.models import User
from app.schemas.user import AdminCreate


async def create_superuser() -> None:
    """Создать суперпользователя."""
    async for session in get_async_session():
        try:
            existing = await session.execute(
                select(User).where(
                    User.username == settings.first_superuser_username,
                ),
            )
            if existing.scalar():
                print(" Пользователь уже существует")
                break

            user_in = AdminCreate(
                username=settings.first_superuser_username,
                email=settings.first_superuser_email,
                phone=settings.first_superuser_phone,
                password=settings.first_superuser_password,
            )
            await user_crud.create(session=session, user_in=user_in)
            print("Суперпользователь создан!")
        except Exception as e:
            print(f"Ошибка: {e}", err=True)
        finally:
            return


def main() -> None:
    """Парсинг аргументов и запуск соответствующей команды."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["create-superuser"])
    args = parser.parse_args()

    if args.command == "create-superuser":
        asyncio.run(create_superuser())


if __name__ == "__main__":
    main()
