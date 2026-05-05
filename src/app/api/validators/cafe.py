from http import HTTPStatus
from typing import List, Optional, Self, Union

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.cafe import cafe_crud
from app.crud.user import user_crud
from app.models.cafe import Cafe
from app.models.user import User
from app.schemas.cafe import CafeCreate, CafeUpdate

logger = get_logger()


async def raise_error(
        msg: str,
        status: HTTPStatus = HTTPStatus.UNPROCESSABLE_ENTITY,
) -> None:
    """Выбрасывает исключение с выбранным статусом и сообщением."""
    raise HTTPException(status_code=status, detail=msg)


async def get_cafe_or_404(
        session: AsyncSession,
        cafe_id: int,
        *,
        is_exist: Optional[bool] = False,
) -> Self:
    """Возвращает кафе по его id и выдает 404, если оно не найдено."""
    if is_exist:
        db_cafe = await cafe_crud.is_obj_exist(session, cafe_id)
    else:
        db_cafe = await cafe_crud.get(cafe_id, session)
    if db_cafe is False or db_cafe is None:
        msg = 'Кафе не найдено!'
        logger.debug(msg + f' cafe_id: {cafe_id}')
        await raise_error(msg, HTTPStatus.NOT_FOUND)
    return db_cafe


async def check_name_address(
    session: AsyncSession,
    new_cafe: Union[CafeCreate, CafeUpdate],
    db_cafe: Optional[Cafe] = None,
) -> None:
    """Проверка, существует ли кафе с одинаковой парой name-address."""
    new_data = new_cafe.model_dump(exclude_unset=True, exclude_none=True)
    name = new_data['name'] if 'name' in new_data else None
    address = new_data['address'] if 'address' in new_data else None
    is_exist = await cafe_crud.is_unique_name_address(
        session, db_cafe, name, address,
    )
    if is_exist:
        msg = (
            f"Кафе с названием '{name}' и адресом '{address}' уже существует! "
        )
        logger.warning(msg)
        await raise_error(msg + "Введите другое название или адрес!")


async def is_managers_id(
    session: AsyncSession,
    new_cafe: Union[CafeCreate, CafeUpdate],
    db_cafe: Optional[Cafe] = None,
) -> Optional[List[User]]:
    """Проверка, указаны ли реальные менеджеры."""
    new_data = new_cafe.model_dump(exclude_unset=True, exclude_none=True)
    if 'managers_id' not in new_data:
        return None
    users_id = set(new_data['managers_id'])
    db_users = await user_crud.get_by_list_of_id(session, users_id)
    if len(users_id) != len(db_users):
        db_users_id = set(user.id for user in db_users)
        missing_id = users_id - db_users_id
        logger.warning(f'Несуществующие user_id: {missing_id}')
        await raise_error('Некоторые указанные менеджеры не найдены!')
    for user in db_users:
        if not user.is_manager:
            msg = 'К кафе можно привязать только менеджера!'
            logger.warning(
                msg + f'user_id: {user.id} | user_role: {user.role}!',
            )
            await raise_error(
                f"'{user.username}' не является менеджером! " + msg,
            )
        if db_cafe and (not user.is_active and db_cafe.is_active is True):
            msg = 'К кафе можно привязать только активированных менеджеров!'
            logger.warning(
                msg + f'user_id: {user.id} | is_active: {user.is_active}',
            )
            await raise_error(
                f"Пользователь '{user.username}' дезактивирован! " + msg,
            )
        elif not user.is_active:
            msg = 'Кафе можно создать только с активированными менеджерами!'
            logger.warning(
                msg + f'user_id: {user.id} | is_active: {user.is_active}',
            )
            await raise_error(
                f"Пользователь '{user.username}' дезактивирован! " + msg,
            )
        if (
            user.cafe_id is not None
            and db_cafe is not None
            and user.cafe_id != db_cafe.id
        ):
            """При обновлении кафе нельзя назначить занятого менджера."""
            user_cafe = await get_cafe_or_404(session, user.cafe_id)
            msg = 'К кафе нельзя назначить занятого менеджера!'
            logger.warning(
                msg + f'manger_id: {user.id} | '
                f'manager.cafe_id: {user.cafe_id}',
            )
            await raise_error((
                f"Менеджер '{user.username}' "
                f"привязан к кафе '{user_cafe.name}'! " + msg
            ))
        elif user.cafe_id is not None and db_cafe is None:
            """При создании кафе нельзя назначить занятого менджера."""
            user_cafe = await get_cafe_or_404(session, user.cafe_id)
            msg = 'Кафе нельзя создать с занятым менеджером!'
            logger.warning((
                msg + f'manаger_id: {user.id} | '
                f'manager.cafe_id: {user.cafe_id}'
            ))
            await raise_error((
                f"Менеджер '{user.username}' "
                f"привязан к кафе '{user_cafe.name}'! " + msg
            ))
    return db_users


async def is_manager_from_cafe(
    cafe_id: int,
    user: User,
    db_cafe: Optional[Cafe] = None,
) -> None:
    """Проверка, что менеджер может редактировать только свое кафе."""
    if db_cafe is not None and db_cafe.is_active is False:
        msg = 'Менеджер может редактировать только активное кафе!'
        logger.warning((
            msg + f'manager_id: {user.id} | '
            f'manager.cafe_id: {user.cafe_id} | '
            f'db_cafe.is_active: {db_cafe.is_active}'
        ))
        await raise_error(msg, HTTPStatus.FORBIDDEN)
    if user.cafe_id is None:
        msg = (
            'У вас нет привязанных кафе! Чтобы вас привязали '
            'к кафе - обратитесь к администратору!'
        )
        logger.warning((
            msg + f'manager_id: {user.id} | manager.cafe_id: {user.cafe_id}!'
        ))
        await raise_error(msg, HTTPStatus.FORBIDDEN)
    if user.cafe_id != cafe_id:
        msg = 'Менеджер может редактировать только свое привязанное кафе!'
        logger.warning(
            msg + f'user.id: {user.id} | user.cafe_id: {user.cafe_id}',
        )
        await raise_error(msg, HTTPStatus.FORBIDDEN)
