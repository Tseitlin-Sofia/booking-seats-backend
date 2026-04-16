from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.user import User, UserRole
from app.schemas.users import UserCreate, UserUpdate
from app.core.user import AuthService


class CRUDUser(CRUDBase):
    """CRUD для объектов модели пользователя."""

    async def get_by_email(
        self,
        email: str,
        session: AsyncSession,
    ) -> Optional[User]:
        """Получает пользователя по email."""
        result = await session.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalars().first()

    async def get_by_phone(
        self,
        phone: str,
        session: AsyncSession,
    ) -> Optional[User]:
        """Получает пользователя по телефону."""
        result = await session.execute(
            select(self.model).where(self.model.phone == phone)
        )
        return result.scalars().first()

    async def get_by_username(
        self,
        username: str,
        session: AsyncSession,
    ) -> Optional[User]:
        """Получает пользователя по username."""
        result = await session.execute(
            select(self.model).where(self.model.username == username)
        )
        return result.scalars().first()

    async def create_user(
        self,
        user_in: UserCreate,
        session: AsyncSession,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Создает нового пользователя в базе данных."""
        # Хэшируем пароль
        password_hash = AuthService.hash_password(user_in.password)
        # Подготавливаем данные
        user_data = user_in.model_dump(exclude={"password"})
        user_data["password_hash"] = password_hash
        user_data["role"] = role

        db_user = self.model(**user_data)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

    async def update_user(
        self,
        db_user: User,
        user_in: UserUpdate,
        session: AsyncSession,
    ) -> User:
        """Обновляет существующего пользователя в базе данных."""
        update_data = user_in.model_dump(exclude_unset=True)
        # Если обновляется пароль, нужно его хэшировать
        if "password" in update_data:
            update_data["password_hash"] = AuthService.hash_password(
                update_data.pop("password")
            )

        for key, value in update_data.items():
            setattr(db_user, key, value)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

    async def get_multi_by_role(
        self,
        role: UserRole,
        session: AsyncSession,
    ) -> list[User]:
        """Получает всех пользователей с указанной ролью."""
        result = await session.execute(
            select(self.model).where(self.model.role == role)
        )
        return result.scalars().all()


user_crud = CRUDUser(User)
