"""Pydantic схемы для бронирований."""

from datetime import date, datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.booking import BookingStatus
from app.schemas.cafe import CafeShortInfo
from app.schemas.slot import TimeSlotShortInfo
from app.schemas.table import TableShortInfo
from app.schemas.user import UserShortInfo
from app.schemas.validators.booking import BookingValidatorMixin


class BookingTableSlot(BaseModel):
    """Пара ID стола и ID временного слота."""

    table_id: int = Field(..., title="Table Id")
    slot_id: int = Field(..., title="Slot Id")

    model_config = ConfigDict(extra='forbid')


class BookingTableSlotCreate(BookingTableSlot):
    """Пара ID стола и ID временного слота для создания бронирования."""

    booking_id: int = Field(..., title="Booking Id")


class BookingTableSlotShortInfo(BaseModel):
    """Информация о столе и слоте для бронирования."""

    table: TableShortInfo
    slot: TimeSlotShortInfo

    model_config = ConfigDict(from_attributes=True)


class BookingCommon(BookingValidatorMixin, BaseModel):
    """Общие поля для бронирований."""

    table_slots: list[BookingTableSlot] = Field(..., title="Table-Slot pairs")
    guest_number: int = Field(..., title="Guest Number")
    note: Optional[str] = Field(None, title="Note")
    booking_date: date = Field(..., title="Booking Date")


class BookingCreate(BookingCommon):
    """Схема для создания бронирования."""

    cafe_id: int = Field(..., title="Cafe Id")

    model_config = ConfigDict(extra='forbid')


class BookingInfo(BookingCommon):
    """Полная информация о бронировании."""

    id: int = Field(..., title="Id")
    user: UserShortInfo
    cafe: CafeShortInfo
    status: BookingStatus
    is_active: bool = Field(..., title="Is Active")
    created_at: datetime = Field(..., title="Created At")
    updated_at: datetime = Field(..., title="Updated At")

    model_config = ConfigDict(from_attributes=True)


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования."""

    table_slots: list[BookingTableSlot] = Field(..., title="Table-Slot pairs")
    guest_number: Optional[int] = Field(None, gt=0, title="Guest Number")
    note: Optional[str] = Field(None, title="Note")
    status: Optional[BookingStatus] = None
    booking_date: Optional[date] = Field(None, title="Booking Date")
    is_active: Optional[bool] = Field(None, title="Is Active")

    model_config = ConfigDict(extra='forbid')
