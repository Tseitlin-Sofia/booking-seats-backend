import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import CafeConstants
from app.schemas.user import UserShortInfo


class CafeBase(BaseModel):
    """Базовая схема."""

    name: str = Field(min_length=CafeConstants.MIN_LENGTH_NAME,)
    address: str = Field(min_length=CafeConstants.MIN_LENGTH_NAME,)
    phone: str = Field(examples=['+78005553535'])
    description: Optional[str] = None
    photo_id: Optional[UUID] = None

    model_config = ConfigDict(extra='forbid')


class CafeShortInfo(CafeBase):
    """Схема для короткой информации о кафе."""

    id: int


class CafeInfo(CafeShortInfo):
    """Схема для метода GET (multi + id) и POST."""

    managers: list[UserShortInfo]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CafeUpdate(BaseModel):
    """Схема для метода PATCH."""

    name: Optional[str] = Field(
        default=None, min_length=CafeConstants.MIN_LENGTH_NAME,
    )
    address: Optional[str] = Field(
        default=None, min_length=CafeConstants.MIN_LENGTH_ADDRESS,
    )
    phone: Optional[str] = Field(default=None, examples=['+78005553535'])
    description: Optional[str] = Field(
        default=None, min_length=CafeConstants.MIN_LENGTH_DESCRIPTION,
    )
    photo_id: Optional[UUID] = None
    managers_id: Optional[List[int]] = Field(
        default=None, min_length=CafeConstants.MIN_LENGTH_MANAGERS_LIST,
    )
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')

    @field_validator("phone")
    def is_correct_phone(cls, value: str) -> str:  # noqa: N805
        """Проверка, указал ли правильный формат телефона."""
        if value is None:
            return value
        if isinstance(value, str) and value.strip() == "":
            raise ValueError("Вы ввели пустую строку!")
        if not re.match(CafeConstants.PHONE_FORMAT, value):
            raise ValueError(CafeConstants.ERROR_PHONE)
        return value


class CafeCreate(CafeBase):
    """Схема для метода POST."""

    managers_id: List[int] = Field(
        min_length=CafeConstants.MIN_LENGTH_MANAGERS_LIST,
    )

    @field_validator("phone")
    def is_correct_phone(cls, value: str) -> str:  # noqa: N805
        """Проверка, указал ли правильный формат телефона."""
        if not re.match(CafeConstants.PHONE_FORMAT, value):
            raise ValueError(CafeConstants.ERROR_PHONE)
        return value
