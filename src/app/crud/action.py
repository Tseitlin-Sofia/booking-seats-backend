from typing import List, Optional, Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models.action import Action
from app.models.cafe import Cafe
from app.schemas.action import ActionCreate, ActionUpdate

logger = get_logger()


class CRUDAction(CRUDBase):
    """CRUD для объектов модели акций."""

    async def create_new_action(
        self,
        session: AsyncSession,
        new_action: ActionCreate,
        cafes: List[Cafe],
    ) -> Self:
        """Создает новую акцию в базе данных."""
        db_action = self.model(
            **new_action.model_dump(
                exclude={'cafes_id'},
                exclude_unset=True,
                exclude_none=True,
            ),
        )
        db_action.cafes = cafes
        session.add(db_action)
        await session.commit()
        await session.refresh(db_action)
        logger.info(
            f'Акция успешно создана! action_id={db_action.id},'
            + f' cafes_count={len(cafes)}',
        )
        return db_action

    async def update_db_action(
        self,
        session: AsyncSession,
        db_action: Action,
        new_action: ActionUpdate,
        cafes: Optional[List[Cafe]] = None,
    ) -> Self:
        """Обновляет существующее кафе в базе данных."""
        new_data = new_action.model_dump(exclude_unset=True, exclude_none=True)
        for key in new_data.keys():
            if key == 'cafes_id':
                db_action.cafes = cafes
                continue
            setattr(db_action, key, new_data[key])
        session.add(db_action)
        logger.info(
            f'Акция успешно обновлена! action_id={db_action.id},'
            + f' updated_fields={list(new_data.keys())}',
        )
        await session.commit()
        await session.refresh(db_action)
        return db_action


action_crud = CRUDAction(Action)
