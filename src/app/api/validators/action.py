from http import HTTPStatus
from typing import List, Optional, Self, Sequence, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators.cafe import (
    get_cafe_or_404,
    is_manager_from_cafe,
    raise_error,
)
from app.core.constants import ActionConstants
from app.core.logging import get_logger
from app.crud.action import action_crud
from app.crud.cafe import cafe_crud
from app.models.action import Action
from app.models.cafe import Cafe
from app.models.user import User
from app.schemas.action import ActionCreate, ActionUpdate

logger = get_logger()


async def check_cafe_list(cafes_id: Sequence, user: User) -> None:
    """Проверка, является ли юзер менеджером кафе."""
    if len(cafes_id) > ActionConstants.MIN_LENGTH_CAFES_LIST:
        msg = (
            'Менеджер может управлять акциями только своего кафе c id '
            f'{user.cafe_id}!'
        )
        logger.warning(msg)
        await raise_error(msg, HTTPStatus.FORBIDDEN)
    await is_manager_from_cafe(cafes_id.pop(), user)


async def get_action_or_404(session: AsyncSession, action_id: int) -> Self:
    """Возвращает акцию по ее id и выдает 404, если она не найдена."""
    db_action = await action_crud.get(action_id, session)
    if db_action is None:
        msg = f'Акция не найдена! action_id: {action_id}'
        logger.debug(msg)
        await raise_error(msg, HTTPStatus.NOT_FOUND)
    return db_action


async def can_manager_change_action(
    session: AsyncSession,
    new_action: Union[ActionCreate, ActionUpdate],
    user: User,
    db_action: Optional[Action] = None,
) -> None:
    """Менеджер может управлять акциями только привязанного к нему кафе."""
    new_data = new_action.model_dump(exclude_unset=True)
    if db_action is not None:
        cafes_id = await cafe_crud.get_cafes_by_action(session, db_action.id)
        await check_cafe_list(cafes_id, user)
    if 'cafes_id' in new_data:
        await check_cafe_list(new_data['cafes_id'], user)


async def is_cafes_exists(
        session: AsyncSession, new_action: Union[ActionCreate, ActionUpdate],
) -> Optional[Sequence[Cafe]]:
    """Проверка, существуют ли кафе из списка в бд."""
    new_data = new_action.model_dump(exclude_unset=True)
    if 'cafes_id' not in new_data:
        return None
    cafes_id = set(new_data['cafes_id'])
    cafes = await cafe_crud.get_by_list_of_id(session, cafes_id)
    if len(cafes_id) != len(cafes):
        db_cafes_id = set(cafe.id for cafe in cafes)
        missing_ids = cafes_id - db_cafes_id
        logger.warning(f'Кафе с id {missing_ids} не существуют!')
        await raise_error(f'Кафе с id {missing_ids} не существуют!')
    return cafes


async def is_action_already_exists(
        session: AsyncSession, new_action: Union[ActionCreate, ActionUpdate],
) -> None:
    """Проверка на наличие акции в бд с тем же описанием."""
    new_data = new_action.model_dump(exclude_unset=True)
    if 'description' not in new_data:
        return
    is_exist = await action_crud.is_obj_exist(
        session, attr_name='description', attr_value=new_data['description'],
    )
    if is_exist:
        msg = 'Акция с таким описанием уже существует!'
        logger.warning(msg)
        await raise_error(msg)
