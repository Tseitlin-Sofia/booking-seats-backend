"""Схемы для работы с пользователями."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.models.user import UserRole
from app.schemas.validators import validate_phone_number


class UserCreate(BaseModel):
    """Схема для создания пользователя."""

    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None
    password: str
    role: Optional[UserRole] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        return validate_phone_number(v)

    @model_validator(mode="after")
    def check_one_credential(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided")
        return self


class UserInfo(BaseModel):
    """Схема для отображения информации о пользователе."""

    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Схема для обновления пользователя."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        return validate_phone_number(v)
