from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ActionConstants
from app.schemas.cafe import CafeShortInfo


class ActionBase(BaseModel):
    """Базовая схема."""

    photo_id: Optional[UUID] = None

    model_config = ConfigDict(extra='forbid')


class ActionUpdate(ActionBase):
    """Схема для метода PATCH."""

    cafes_id: Optional[List[int]] = Field(
        default=None, min_length=ActionConstants.MIN_LENGTH_CAFES_LIST,
    )
    description: Optional[str] = Field(
        default=None, min_length=ActionConstants.MIN_DESCRIPTION,
    )
    is_active: Optional[bool] = None


class ActionInfo(ActionBase):
    """Схема для метода GET (multi + id) и POST."""

    id: int
    cafes: list[CafeShortInfo]
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionCreate(ActionBase):
    """Схема для метода POST."""

    cafes_id: List[int] = Field(
        min_length=ActionConstants.MIN_LENGTH_CAFES_LIST,
    )
    description: str = Field(min_length=ActionConstants.MIN_DESCRIPTION)
