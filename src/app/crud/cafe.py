from typing import List, Optional, Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models import Cafe, User
from app.schemas.cafe import CafeCreate, CafeUpdate

logger = get_logger()


class CRUDCafe(CRUDBase):
    """CRUD для объектов модели кафе."""

    async def create_new_cafe(
        self,
        new_cafe: CafeCreate,
        managers: List[User],
        session: AsyncSession,
    ) -> Self:
        """Создает новое кафе в базе данных."""
        db_cafe = self.model(**new_cafe.model_dump())
        db_cafe.managers_id = managers  # NOTE: связываем менеджеров с кафе.
        session.add(db_cafe)
        await session.commit()
        await session.refresh(db_cafe)
        logger.info(
            'Кафе успешно создано!',
            f' | cafe_id: {db_cafe.id} | cafe_name: {db_cafe.name}'
            + f' | количество менеджеров: {len(managers) if managers else 0}',
        )
        return db_cafe

    async def update_db_cafe(
        self,
        db_cafe: Self,
        new_data_cafe: CafeUpdate,
        managers: Optional[List[User]],
        session: AsyncSession,
    ) -> Self:
        """Обновляет существующее кафе в базе данных."""
        update_data = new_data_cafe.model_dump(exclude_unset=True)
        for key in update_data.keys():
            new_value = update_data[key]
            if key == 'managers_id':
                new_value = managers
            setattr(db_cafe, key, new_value)
        session.add(db_cafe)
        logger.info(
            'Кафе успешно обновлено!',
            f' | updated_fields: {list(update_data.keys())}',
        )
        await session.commit()
        await session.refresh(db_cafe)
        return db_cafe


cafe_crud = CRUDCafe(Cafe)
