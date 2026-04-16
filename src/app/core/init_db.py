"""Инициализация базы данных."""

import argparse
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_async_session
from app.crud.user import user_crud
from app.schemas.user import AdminCreate
from app.models import User


async def create_superuser():
    """Создать суперпользователя."""
    async for session in get_async_session():
        try:
            existing = await session.execute(
                select(User).where(
                    User.username == settings.first_superuser_username
                )
            )
            if existing.scalar():
                print(f" Пользователь уже существует")
                break

            user_in = AdminCreate(
                username=settings.first_superuser_username,
                email=settings.first_superuser_email,
                phone=settings.first_superuser_phone,
                password=settings.first_superuser_password,
            )
            await user_crud.create(session=session, user_in=user_in)
            print(f"Суперпользователь создан!")
        except Exception as e:
            print(f"Ошибка: {e}", err=True)
        finally:
            return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["create-superuser"])
    args = parser.parse_args()
    
    if args.command == "create-superuser":
        asyncio.run(create_superuser())


if __name__ == "__main__":
    main()
