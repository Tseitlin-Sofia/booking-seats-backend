from http import HTTPStatus
from typing import List, Optional, Self, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ActionConstants
from app.core.logging import get_logger
from app.api.validators.cafe import (
    get_cafe_or_404, is_manager_from_cafe, raise_error
)
from app.crud.action import action_crud

if TYPE_CHECKING:
    from app.models.cafe import Cafe
    from app.models.user import User
    from app.schemas.action import ActionCreate

logger = get_logger()


async def get_action_or_404(session: AsyncSession, action_id: int,) -> Self:
    """Возвращает акцию по ее id и выдает 404, если она не найдена."""
    db_action = await action_crud.get(action_id, session)
    if db_action is None:
        msg = f'Акция не найдена! action_id: {action_id}'
        logger.debug(msg)
        await raise_error(msg, HTTPStatus.NOT_FOUND)
    return db_action


async def can_manager_change_action(
    new_action: ActionCreate,
    user: User
) -> None:
    """Менеджер может управлять акциями только привязанного к нему кафе."""
    new_data = new_action.model_dump(exclude_unset=True)
    if 'cafes_id' not in new_data:
        return None
    cafes_id = new_data['cafes_id']
    if len(cafes_id) > ActionConstants.MIN_LENGTH_CAFES_LIST:
        msg = (
            'Менеджер может управлять акциями только своего кафе c id '
            f'{user.cafe_id}!'
        )
        logger.warning(msg)
        await raise_error(msg, HTTPStatus.FORBIDDEN)
    await is_manager_from_cafe(cafes_id.pop(), user,)


async def is_cafes_exists(
        session: AsyncSession, new_action: ActionCreate
) -> List[Cafe]:
    new_data = new_action.model_dump(exclude_unset=True)
    if 'cafes_id' not in new_data:
        return None
    cafes = []
    for cafe_id in new_data['cafes_id']:
        cafe = await get_cafe_or_404(session, cafe_id)
        cafes.append(cafe)
    return cafes


async def is_action_already_exists(
    session: AsyncSession, new_action: ActionCreate
) -> None:
    new_data = new_action.model_dump(exclude_unset=True)
    is_exist = action_crud.is_obj_exist(
        session, attr_name='description', attr_value=new_data['description']
    )
    if is_exist:
        msg = 'Акция с таким описанием уже существует!'
        logger.warning(msg)
        await raise_error(msg)
