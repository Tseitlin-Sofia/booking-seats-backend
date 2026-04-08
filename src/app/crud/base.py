"""Базовый класс для CRUD операций с базой данных."""

from typing import Optional, Self, Mapping, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class CRUDBase:
    """Базовый класс для CRUD операций с базой данных."""

    def __init__(self, model: type[Self]) -> None:
        """Инициализатор класса."""
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> Optional[Self]:
        """Получает объект по его id."""
        db_obj = await session.execute(
            select(self.model).where(
                self.model.id == obj_id,
            ),
        )
        return db_obj.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
    ) -> list[Self]:
        """Получает все объекты заданной модели."""
        db_objs = await session.execute(select(self.model))
        return db_objs.scalars().all()

    async def create(
        self,
        obj_in: Mapping[str, Any],
        session: AsyncSession,
        user: Optional[User] = None,
    ) -> Self:
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
        db_obj: Self,
        obj_in: Mapping[str, Any],
        session: AsyncSession,
    ) -> Self:
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

    # async def remove(
    #     self,
    #     db_obj,
    #     session: AsyncSession,
    # ):
    #     await session.delete(db_obj)
    #     await session.commit()
    #     return db_obj

    # async def get_by_attribute(
    #     self,
    #     attr_name: str,
    #     attr_value: str,
    #     session: AsyncSession,
    # ):
    #     attr = getattr(self.model, attr_name)
    #     db_obj = await session.execute(
    #         select(self.model).where(attr == attr_value)
    #     )
    #     return db_obj.scalars().first()
