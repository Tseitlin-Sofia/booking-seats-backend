from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import (
    get_admin_user,
    get_current_user,
    get_current_user_optional,
    get_manager_user,
)
from app.models import User

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
UserDep = Annotated[User, Depends(get_current_user)]
OptionalUserDep = Annotated[Optional[User], Depends(get_current_user_optional)]
AdminDep = Annotated[User, Depends(get_admin_user)]
ManagerDep = Annotated[User, Depends(get_manager_user)]
