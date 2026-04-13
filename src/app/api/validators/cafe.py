from http import HTTPStatus
from typing import List, Union

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
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
