from http import HTTPStatus
from typing import List, Optional, Self, Union

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.cafe import cafe_crud
from app.crud.user import user_crud
from app.models import Cafe, User
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
        is_exist: Optional[bool] = False,
) -> Self:
    """Возвращает объект по id и выдает 404, если он не найден."""
    if is_exist:
        db_cafe = await cafe_crud.is_cafe_exist(session, cafe_id)
    else:
        db_cafe = await cafe_crud.get(cafe_id, session)
    if db_cafe is False or db_cafe is None:
        msg = f'Кафе не найдено! cafe_id: {cafe_id}'
        logger.debug(msg)
        await raise_error(msg, HTTPStatus.NOT_FOUND)
    return db_cafe


async def check_name_address(
    session: AsyncSession,
    new_cafe: Union[CafeCreate, CafeUpdate],
    db_cafe: Optional[Cafe] = None,
) -> None:
    """Проверка, существует ли кафе с одинаковой парой name-address."""
    new_data = new_cafe.model_dump(exclude_unset=True)
    name = new_data['name'] if 'name' in new_data else None
    address = new_data['address'] if 'address' in new_data else None
    is_exist = await cafe_crud.is_unique_name_address(
        session, db_cafe, name, address,
    )
    if is_exist:
        await raise_error((
            'Кафе с таким же названием и адресом уже существует! '
            'Введите другое название или адрес!'
        ))


async def is_managers_id(
    session: AsyncSession,
    new_cafe: Union[CafeCreate, CafeUpdate],
    cafe_id: Optional[int] = None,
) -> Optional[List[User]]:
    """Проверка, указаны ли реальные менеджеры."""
    new_data = new_cafe.model_dump(exclude_unset=True)
    if 'managers_id' not in new_data:
        return None
    managers = []
    for manager_id in new_data['managers_id']:
        db_user = await user_crud.get(manager_id, session, True)
        if db_user is None:
            msg = (
                'Попытка назначить несуществующего пользователя менеджером! '
                f'manager_id: {manager_id}'
            )
            logger.warning(msg)
            await raise_error(msg)
        if not db_user.is_manager:
            msg = (
                'Попытка назначить к кафе не менеджера! '
                f'manager_id: {manager_id} | role: {db_user.role}'
            )
            logger.warning(msg)
            await raise_error(msg)
        if db_user.cafe_id is not None and db_user.cafe_id != cafe_id:
            """Проверка, обеспечивающая любому кафе наличие менеджеров."""
            msg = (
                f'Вы пытаетесь назначить менеджера c id {manager_id}, '
                'привязанного к другому кафе! Сначала замените или исключите '
                f'его из кафе с id {db_user.cafe_id}!'
            )
            logger.warning(msg)
            await raise_error(msg)
        managers.append(db_user)

    return managers


async def is_manager_from_cafe(cafe_id: int, user: User) -> None:
    """Проверка, что менеджер может редактировать только свое кафе."""
    if user.is_manager and user.cafe_id != cafe_id:
        msg = 'Менеджер может редактировать только свое привязанное кафе!'
        await raise_error(msg, HTTPStatus.FORBIDDEN)
