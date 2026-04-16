from http import HTTPStatus
import re
from typing import List, Union

from fastapi import HTTPException
from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CafeConstants
from app.models import Cafe, User
from app.schemas.cafe import CafeCreate, CafeUpdate


async def is_managers_id(
        obj_in: Union[CafeCreate, CafeUpdate],
        session: AsyncSession,
) -> List[User]:
    """Проверка, указал ли пользователь реальных менеджеров."""
    obj_in_data = obj_in.model_dump()
    managers = []  # NOTE: список менеджеров, чтобы добавить в cafe_managers.
    for manager_id in obj_in_data['managers_id']:
        result = await session.execute(
            select(User)
            .where(User.id == manager_id),
        )
        db_user = result.scalars().first()
        if db_user.role != 'manager':
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Введенные пользователи не являются менеджерами!',
            )
        managers.append(db_user)

    return managers


def is_correct_phone(phone: str) -> str:
    """Проверка, указал ли правильный формат телефона."""
    if not re.match(phone, CafeConstants.PHONE_FORMAT):
        raise ValueError(CafeConstants.ERROR_PHONE)
    return phone


async def is_unique_name_address(
    new_cafe: CafeCreate,
    session: AsyncSession,
    db_cafe: Cafe
) -> None:
    """Проверка, существует ли кафе с одинаковой парой name-address."""
    if db_cafe:
        if new_cafe.name and not new_cafe.address:
            exists_criteria = select(
                exists()
                .where(and_(
                    Cafe.name == new_cafe.name,
                    Cafe.address == new_cafe.address
                ))
            )

    exists_criteria = select(
        exists()
        .where(and_(
            Cafe.name == new_cafe.name,
            Cafe.address == new_cafe.address
        ))
    )
    result = await session.execute(exists_criteria)
    if result.scalar():
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=(
                'Кафе с таким же названием и адресом уже существует! '
                'Введите другое название или адрес!'
            )
        )
