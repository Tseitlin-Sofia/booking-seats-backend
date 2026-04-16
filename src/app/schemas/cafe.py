from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.api.validators.cafe import is_correct_phone


class CafeBase(BaseModel):
    """Базовая схема."""

    name: str
    address: str
    phone: str
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

    managers: list[CafeManagers]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CafeUpdate(BaseModel):
    """Схема для метода PATCH."""

    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers_id: Optional[List[int]] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return is_correct_phone(value)


class CafeCreate(CafeBase):
    """Схема для метода POST."""

    managers_id: List[int]

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return is_correct_phone(value)
