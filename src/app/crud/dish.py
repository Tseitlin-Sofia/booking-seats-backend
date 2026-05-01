"""CRUD операции для блюд."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models.dish import Dish
from app.schemas.dish import DishCreate

logger = get_logger()


class CRUDDish(CRUDBase):
    """CRUD операции для модели Dish."""

    async def get_dishes_by_cafe(
        self,
        cafe_id: int,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        only_available: bool = False,
    ) -> list[Dish]:
        """Получает блюда заданного кафе."""
        stmt = select(Dish).where(Dish.cafe_id == cafe_id)
        if show_active is not None:
            stmt = stmt.where(Dish.is_active == show_active)
        if only_available:
            stmt = stmt.where(Dish.is_available.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_dish_in_cafe(
        self,
        cafe_id: int,
        dish_id: int,
        session: AsyncSession,
    ) -> Optional[Dish]:
        """Получает блюдо по ID внутри конкретного кафе."""
        result = await session.execute(
            select(Dish).where(
                Dish.id == dish_id,
                Dish.cafe_id == cafe_id,
            ),
        )
        return result.scalars().first()

    async def get_by_name_in_cafe(
        self,
        cafe_id: int,
        name: str,
        session: AsyncSession,
    ) -> Optional[Dish]:
        """Ищет блюдо по имени в указанном кафе (для проверки уникальности)."""
        result = await session.execute(
            select(Dish).where(
                Dish.cafe_id == cafe_id,
                Dish.name == name,
            ),
        )
        return result.scalars().first()

    async def create_for_cafe(
        self,
        cafe_id: int,
        obj_in: DishCreate,
        session: AsyncSession,
    ) -> Dish:
        """Создаёт блюдо, привязанное к кафе."""
        obj_data = obj_in.model_dump()
        obj_data['cafe_id'] = cafe_id
        db_obj = self.model(**obj_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        logger.info(
            'Блюдо успешно создано! | dish_id: {} | cafe_id: {} | name: {}',
            db_obj.id,
            cafe_id,
            db_obj.name,
        )
        return db_obj


dish_crud = CRUDDish(Dish)
