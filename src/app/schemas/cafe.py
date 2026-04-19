from datetime import datetime
import re
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import CafeConstants


class ValidatePhoneMixin:
    @field_validator("phone")
    def is_correct_phone(cls, value: str) -> str:
        if not re.match(CafeConstants.PHONE_FORMAT, value):
            raise ValueError(CafeConstants.ERROR_PHONE)
        return value


class CafeBase(BaseModel):
    """Базовая схема."""

    name: str
    address: str
    phone: str = Field(examples=['+78005553535'])
    description: Optional[str] = None
    photo_id: Optional[UUID] = None

    model_config = ConfigDict(extra='forbid')


class CafeShortInfo(CafeBase):
    """Схема для короткой информации о кафе."""

    id: int


class CafeManagers(BaseModel):
    """Схема менеджеров для схемы CafeInfo."""

    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    tg_id: Optional[str]


class CafeInfo(CafeShortInfo):
    """Схема для метода GET (multi + id) и POST."""

    # managers: list[CafeManagers]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CafeUpdate(ValidatePhoneMixin, BaseModel):
    """Схема для метода PATCH."""

    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers_id: Optional[List[int]] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')


class CafeCreate(ValidatePhoneMixin, CafeBase):
    """Схема для метода POST."""

    managers_id: Optional[List[int]] = None
