"""Базовый класс для CRUD операций с базой данных."""

from typing import TYPE_CHECKING, Any, Optional

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.models import User

if TYPE_CHECKING:
    from pydantic import BaseModel

    from app.core.db import Base


class CRUDBase:
    """Базовый класс для CRUD операций с базой данных."""

    def __init__(self, model: type[Base]) -> None:
        """Инициализатор класса."""
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
        is_active: Optional[bool] = True,
    ) -> Optional[Base]:
        """Получает объект по его id, с учетом статуса активности."""
        stmt = select(self.model).where(
                self.model.id == obj_id,
            )
        if is_active is not None:
            stmt = stmt.where(
                self.model.is_active == is_active,
            )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        is_active: Optional[bool] = True,
    ) -> list[Base]:
        """Получает все объекты, с учетом статуса активности."""
        stmt = select(self.model)
        if is_active is not None:
            stmt = stmt.where(
                self.model.is_active == is_active,
            )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        obj_in: BaseModel,
        session: AsyncSession,
        user: Optional[User] = None,
    ) -> Base:
        """Создает новую запись в базе данных."""
        obj_in_data = obj_in.model_dump()
        if user is not None:
            obj_in_data['user_id'] = user.id
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: Base,
        obj_in: BaseModel,
        session: AsyncSession,
    ) -> Base:
        """Обновляет существующую запись в базе данных."""
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_by_attribute(
        self,
        attr_name: str,
        attr_value: Any,
        session: AsyncSession,
        is_active: Optional[bool] = True,
    ) -> Optional[Base]:
        """Получает объект по атрибуту, с учетом статуса активности."""
        attr = getattr(self.model, attr_name)
        stmt = select(self.model).where(attr == attr_value)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active == is_active)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_attribute_multi(
        self,
        attr_name: str,
        attr_value: Any,
        session: AsyncSession,
        is_active: Optional[bool] = True,
    ) -> list[Base]:
        """Получает объекты по атрибуту, с учетом статуса активности."""
        attr = getattr(self.model, attr_name)
        stmt = select(self.model).where(attr == attr_value)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active == is_active)
        result = await session.execute(stmt)
        return list(result.scalars().all())
