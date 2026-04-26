from typing import List, Optional, Self, Sequence

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models import Cafe, User
from app.models.action import action_cafe
from app.schemas.cafe import CafeCreate, CafeUpdate

logger = get_logger()


class CRUDCafe(CRUDBase):
    """CRUD для объектов модели кафе."""

    async def get_cafes_by_action(
        self,
        session: AsyncSession,
        action_id: int,
    ) -> Sequence[Cafe]:
        result = await session.execute(
            select(action_cafe.c.cafe_id)
            .where(action_cafe.c.action_id == action_id)
        )
        return result.scalars().all()

    async def create_new_cafe(
        self,
        session: AsyncSession,
        new_cafe: CafeCreate,
        managers: List[User],
    ) -> Self:
        """Создает новое кафе в базе данных."""
        db_cafe = self.model(**new_cafe.model_dump(
            exclude={"managers_id"}, exclude_unset=True),
        )
        db_cafe.managers = managers
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
        session: AsyncSession,
        db_cafe: Cafe,
        new_cafe: CafeUpdate,
        managers: Optional[List[User]] = None,
    ) -> Self:
        """Обновляет существующее кафе в базе данных."""
        new_data = new_cafe.model_dump(exclude_unset=True)
        for key in new_data.keys():
            if key == 'managers_id':
                db_cafe.managers = managers
                continue
            setattr(db_cafe, key, new_data[key])
        session.add(db_cafe)
        logger.info(
            'Кафе успешно обновлено!',
            f' | updated_fields: {list(new_data.keys())}',
        )
        await session.commit()
        await session.refresh(db_cafe)
        return db_cafe

    async def is_unique_name_address(
        self,
        session: AsyncSession,
        db_cafe: Optional[Cafe] = None,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> bool:
        """Проверяет, есть ли в бд кафе с тем же названием-адресом."""
        if db_cafe is None:
            stmt = and_(Cafe.name == name, Cafe.address == address)
        else:
            name = name or db_cafe.name
            address = address or db_cafe.address
            stmt = and_(
                Cafe.name == name,
                Cafe.address == address,
                Cafe.id != db_cafe.id,
            )
        result = await session.scalar(select(exists().where(stmt)))
        return bool(result)


cafe_crud = CRUDCafe(Cafe)
