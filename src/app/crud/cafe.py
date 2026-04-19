from typing import List, Optional, Self, Sequence

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models import Cafe, User
from app.schemas.cafe import CafeCreate, CafeUpdate

logger = get_logger()


class CRUDCafe(CRUDBase):
    """CRUD для объектов модели кафе."""

    async def get_all_cafes(
        self,
        session: AsyncSession,
        show_active: Optional[bool],
    ) -> Sequence[Cafe]:
        """
        Возвращает список кафе в соответствии с правами доступа
        и установленным менеджером/админом show_active.
        """
        stmt = select(Cafe)
        if show_active is True:
            stmt = stmt.where(Cafe.is_active)
        elif show_active is not None:
            stmt = stmt.where(Cafe.is_active == show_active)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_obj_by_id(
        self,
        session: AsyncSession,
        obj_id: int
    ) -> Optional[Self]:
        """До фикса базового круда."""
        result = await session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalars().first()

    async def create_new_cafe(
        self,
        session: AsyncSession,
        new_cafe: CafeCreate,
        managers: List[User]
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
        session: AsyncSession,
        db_cafe: Cafe,
        new_data_cafe: CafeUpdate,
        managers: Optional[List[User]],
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

    async def is_unique_name_address(
        self,
        session: AsyncSession,
        db_cafe: Optional[Cafe] = None,
        name: Optional[str] = None,
        address: Optional[str] = None
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
                Cafe.id != db_cafe.id
            )
        result = await session.scalar(select(exists().where(stmt)))
        return bool(result)


cafe_crud = CRUDCafe(Cafe)
