from http import HTTPStatus
from typing import List, Optional, Self, Union

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.cafe import cafe_crud
from app.models import Cafe, User
from app.schemas.cafe import CafeCreate, CafeUpdate

logger = get_logger


async def get_cafe_or_404(session: AsyncSession, obj_id: int) -> Self:
    """Возвращает объект по id и выдает 404, если он не найден."""
    db_cafe = await cafe_crud.get_obj_by_id(session, obj_id)
    # db_cafe = await cafe_crud.get(session, obj_id)  До фикса базового круда.
    if db_cafe is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='Объект не найден!')
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
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=(
                'Кафе с таким же названием и адресом уже существует! '
                'Введите другое название или адрес!'
            ),
        )


async def is_managers_id(
    session: AsyncSession,
    new_cafe: Union[CafeCreate, CafeUpdate],
) -> Optional[List[User]]:
    """Проверка, указаны ли реальные менеджеры и их передача для POST."""
    new_data = new_cafe.model_dump(exclude_unset=True)
    if 'managers_id' not in new_data:
        return None
    managers = []  # Cписок менеджеров, чтобы добавить в cafe_managers.
    for manager_id in new_data['managers_id']:
        db_user = await cafe_crud.get_obj_by_id(session, manager_id)
        if db_user is None:
            logger.warning(
                'Попытка назначить несуществующего пользователя менеджером!'
                + f' manager_id: {manager_id}',
            )
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Пользователь не найден.',
            )
        if not db_user.is_manager:
            logger.warning(
                'Попытка назначения роли, не являющейся ролью менеджера,'
                + ' для объекта "кафе"!'
                + f' manager_id: {manager_id} | role: {db_user.role}',
            )
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=(
                    f'Пользователь c id {manager_id} не является менеджером!'
                ),
            )
        managers.append(db_user)

    return managers
