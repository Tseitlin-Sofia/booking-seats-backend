"""Базовый класс для CRUD операций с базой данных."""

from typing import Any, Iterable, Optional, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.core.logging import get_logger
from app.models import User

Model = TypeVar('Model', bound=Base)
logger = get_logger()


class CRUDBase:
    """Базовый класс для CRUD операций с базой данных."""

    def __init__(self, model: type[Model]) -> None:
        """Инициализатор класса."""
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
        is_active: Optional[bool] = None,
        eager_options: Optional[list] = None,
    ) -> Optional[Model]:
        """Получает объект по его id, с учетом статуса активности."""
        stmt = select(self.model).where(
            self.model.id == obj_id,
        )
        if is_active is not None:
            stmt = stmt.where(
                self.model.is_active == is_active,
            )
        if eager_options:
            stmt = stmt.options(*eager_options)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        is_active: Optional[bool] = None,
    ) -> list[Model]:
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
        obj_in: Union[BaseModel, dict],
        session: AsyncSession,
        user: Optional[User] = None,
    ) -> Model:
        """Создает новую запись в базе данных."""
        if isinstance(obj_in, BaseModel):
            obj_in_data = obj_in.model_dump()
        else:
            obj_in_data = obj_in.copy()
        if user is not None:
            obj_in_data['user_id'] = user.id
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        logger.debug(
            f'Создан объект {self.model.__name__} с id={db_obj.id}',
        )
        return db_obj

    async def update(
        self,
        db_obj: Model,
        obj_in: BaseModel,
        session: AsyncSession,
    ) -> Model:
        """Обновляет существующую запись в базе данных."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        logger.debug(
            f'Обновлён объект {self.model.__name__}'
            + f' с id={db_obj.id}. Изменены поля: {list(update_data.keys())}',
        )
        return db_obj

    async def get_by_attribute(
        self,
        attr_name: str,
        attr_value: Any,
        session: AsyncSession,
        is_active: Optional[bool] = True,
    ) -> Optional[Model]:
        """Получает объект по атрибуту, с учетом статуса активности."""
        if not hasattr(self.model, attr_name):
            raise AttributeError(
                f'У модели {self.model.__name__} нет атрибута {attr_name}.',
            )
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
    ) -> list[Model]:
        """Получает объекты по атрибуту, с учетом статуса активности."""
        attr = getattr(self.model, attr_name)
        stmt = select(self.model).where(attr == attr_value)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active == is_active)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_list_of_id(
        self,
        session: AsyncSession,
        sequence_id: Iterable[int],
    ) -> Iterable[Model]:
        """Возвращает кафе по последовательности из id."""
        result = await session.execute(
            select(self.model).where(self.model.id.in_(sequence_id)),
        )
        return result.scalars().all()

    async def deactivate(
        self,
        session: AsyncSession,
        db_obj: Model,
    ) -> Model:
        """Деактивирует объект."""
        db_obj.is_active = False
        await session.commit()
        await session.refresh(db_obj)
        logger.info(
            'Деактивирован объект %s с id=%d',
            self.model.__name__,
            db_obj.id,
        )
        return db_obj

    async def deactivate_multi(
        self,
        session: AsyncSession,
        db_objs: list[Model],
        *,
        reverse: bool = False,
    ) -> list[Model]:
        """Деактивирует несколько объектов. Может активировать их обратно."""
        for db_obj in db_objs:
            db_obj.is_active = reverse
        await session.commit()
        for db_obj in db_objs:
            await session.refresh(db_obj)
        logger.info(
            f'Деактивировано {len(db_objs)} объектов {self.model.__name__}',
        )
        return db_objs

    async def is_obj_exist(
        self,
        session: AsyncSession,
        obj_id: Optional[int] = None,
        attr_name: Optional[str] = None,
        attr_value: Optional[Any] = None,
    ) -> bool:
        """Проверка наличия объекта в бд (также по атрибуту)."""
        stmt = exists().select_from(self.model)
        if attr_name is not None and attr_value is not None:
            attr = getattr(self.model, attr_name)
            stmt = stmt.where(attr == attr_value)
        elif obj_id is not None:
            stmt = stmt.where(self.model.id == obj_id)
        result = await session.execute(select(stmt))
        return result.scalar_one()
