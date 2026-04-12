"""Базовый класс для CRUD операций с базой данных."""

from http import HTTPStatus
from typing import Any, Mapping, Optional, Self

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from app.models import User


class CRUDBase:
    """Базовый класс для CRUD операций с базой данных."""

    def __init__(self, model: type[Self]) -> None:
        """Инициализатор класса."""
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> Self:
        """Получает объект по его id."""
        result = await session.execute(
            select(self.model)
            .where(self.model.id == obj_id),
        )
        db_obj = result.scalars().first()
        # NOTE: предлагаю здесь сделать проверку на наличие объекта в БД,
        # чтобы не дублировать код.
        if db_obj is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Объект не найден!',
            )
        return db_obj

    async def get_multi(
        self,
        session: AsyncSession,
    ) -> list[Self]:
        """Получает все объекты заданной модели."""
        # NOTE: предлагаю здесь потом сделать фильтр по show_active, чтобы в
        # зависимости от прав доступа вовзвращалась разная выборка объектов.
        db_objs = await session.execute(select(self.model))
        return db_objs.scalars().all()

    async def create(
        self,
        obj_in: Mapping[str, Any],
        session: AsyncSession,
        user: Optional[Any] = None,
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
