from typing import Annotated

from fastapi import APIRouter, Depends, Path, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.crud.user import user_crud
from app.models import User
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserInfo, UserUpdate

router = APIRouter()

SessionDep = Annotated[
    AsyncSession,
    Depends(get_async_session),
]

@router.get(
    '/',
    response_model=list[UserInfo],
    description=(
        'Возвращает информацию о всех пользователях.'
        'Только для администраторов или менеджеров'
    )
)
async def get_users(
    session: SessionDep
    # TODO добавить пермишены
) -> list[UserInfo]:
    return await user_crud.get_multi(session=session,)
