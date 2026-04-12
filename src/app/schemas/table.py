"""Pydantic-схемы для столов."""

import datetime
from typing import Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CafeShortInfo(BaseModel):
    """Краткая информация о кафе (для вложенных ответов)."""

    id: int
    name: str
    address: str
    phone: str
    description: Optional[str] = None
    photo_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TableCreate(BaseModel):
    """Схема создания стола."""

    seat_number: int = Field(..., gt=0)
    description: Optional[str] = Field(
        None,
        max_length=500,
    )

    model_config = ConfigDict(extra='forbid')


class TableUpdate(BaseModel):
    """Схема обновления стола (все поля опциональны)."""

    seat_number: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(
        None,
        max_length=500,
    )
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def prevent_null_required_fields(self) -> Self:
        """Запрещает явную передачу null для обязательных полей."""
        not_nullable = {'seat_number'}
        for field_name in not_nullable:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                msg = f'Поле {field_name} не может быть null'
                raise ValueError(msg)
        return self


class TableShortInfo(BaseModel):
    """Краткая информация о столе."""

    id: int
    description: Optional[str] = None
    seat_number: int

    model_config = ConfigDict(from_attributes=True)


class TableInfo(BaseModel):
    """Полная информация о столе."""

    id: int
    cafe: CafeShortInfo
    description: Optional[str] = None
    seat_number: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
