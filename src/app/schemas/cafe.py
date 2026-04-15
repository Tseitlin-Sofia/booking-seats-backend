from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CafeBase(BaseModel):
    """Базовая схема."""

    name: str
    address: str
    phone: str
    description: Optional[str]
    photo_id: Optional[UUID]

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
    """Схема для метода GET (multi + id)."""

    managers: list[CafeManagers]
    is_active: bool
    created_at: datetime
    updated_at: datetime


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


class CafeCreate(BaseModel):
    """Схема для метода POST."""

    name: str
    address: str
    phone: str
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers_id: List[int]


class CafeDB(CafeInfo):
    """Схема ответа на методы POST и PATCH."""

    model_config = ConfigDict(from_attributes=True)
