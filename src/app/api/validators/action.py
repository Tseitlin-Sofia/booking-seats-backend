from http import HTTPStatus
from typing import Optional, Self, Sequence, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators.cafe import (
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


async def can_manager_change_cafes(cafes_id: Sequence, user: User) -> None:
    """Проверка, что менеджер редактирует только свое кафе."""
    if len(cafes_id) > ActionConstants.MIN_LENGTH_CAFES_LIST:
        msg = (
            'Менеджер может управлять акциями только привязанного к нему кафе!'
        )
        logger.warning(
            msg + f'user_id: {user.id }  | user.cafe_id: {user.cafe_id}!',
        )
        await raise_error(msg, HTTPStatus.FORBIDDEN)
    await is_manager_from_cafe(cafes_id.pop(), user)


async def get_action_or_404(session: AsyncSession, action_id: int) -> Self:
    """Возвращает акцию по ее id и выдает 404, если она не найдена."""
    db_action = await action_crud.get(action_id, session)
    if db_action is None:
        msg = 'Акция не найдена!'
        logger.debug(msg + f'action_id: {action_id}')
        await raise_error(msg, HTTPStatus.NOT_FOUND)
    return db_action


async def can_manager_change_action(
    session: AsyncSession,
    new_action: Union[ActionCreate, ActionUpdate],
    user: User,
    db_action: Optional[Action] = None,
) -> None:
    """Менеджер может управлять акциями только привязанного к нему кафе."""
    new_data = new_action.model_dump(exclude_unset=True, exclude_none=True)
    if db_action is not None and db_action.is_active is False:
        msg = 'Менеджер может редактировать только активные акции!'
        logger.warning((
            msg + f'manager_id: {user.id} | '
            f'db_action.id: {db_action.id} | '
            f'db_action.is_active: {db_action.is_active}'
        ))
        await raise_error(msg, HTTPStatus.FORBIDDEN)
    if db_action is not None:
        cafes_id = await cafe_crud.get_cafes_by_action(session, db_action.id)
        await can_manager_change_cafes(cafes_id, user)
    if 'cafes_id' in new_data:
        await can_manager_change_cafes(new_data['cafes_id'], user)


async def is_cafes_exists(
        session: AsyncSession, new_action: Union[ActionCreate, ActionUpdate],
) -> Optional[Sequence[Cafe]]:
    """Проверка, существуют ли кафе из списка id в бд."""
    new_data = new_action.model_dump(exclude_unset=True, exclude_none=True)
    if 'cafes_id' not in new_data:
        return None
    cafes_id = set(new_data['cafes_id'])
    cafes = await cafe_crud.get_by_list_of_id(session, cafes_id)
    if len(cafes_id) != len(cafes):
        db_cafes_id = set(cafe.id for cafe in cafes)
        missing_ids = cafes_id - db_cafes_id
        logger.warning(f'Есть несуществующие кафе! missing_id: {missing_ids}')
        await raise_error('Некоторые указанные кафе не найдены!')
    return cafes


async def is_action_already_exists(
        session: AsyncSession, new_action: Union[ActionCreate, ActionUpdate],
) -> None:
    """Проверка на наличие акции в бд с тем же описанием."""
    new_data = new_action.model_dump(exclude_unset=True, exclude_none=True)
    if 'description' not in new_data:
        return
    is_exist = await action_crud.is_obj_exist(
        session, attr_name='description', attr_value=new_data['description'],
    )
    if is_exist:
        msg = 'Акция с таким описанием уже существует!'
        logger.warning(msg)
        await raise_error(msg)


async def can_actions_be_attached_to_cafe(
        session: AsyncSession,
        new_action: ActionUpdate,
        db_action: Action,
        cafes: Sequence[Cafe],
) -> None:
    """К активированному кафе можно привязать только активированные акции."""
    if cafes is None:
        return
    for cafe in cafes:
        if cafe.is_active is True and db_action.is_active is False:
            msg = (
                'Дезактивированные акции нельзя привязть к активиронному кафе!'
            )
            logger.warning((
                msg + f'action.is_active: {db_action.is_active} | '
                f'cafe_id: {cafe.id}, cafe.is_active: {cafe.is_active}!'
            ))
            await raise_error(msg)
