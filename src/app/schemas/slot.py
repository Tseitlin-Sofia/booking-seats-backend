"""Схема для модели интервала времени бронирования столика."""

from datetime import datetime, time
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from typing_extensions import Self

from app.core.constants import SlotConstants
from app.schemas.cafe import CafeShortInfo


class TimeSlotBase(BaseModel):
    """Базовая схема для модели интервала времени бронирования слота в кафе."""

    start_time: time = Field(
        ...,
        examples=[SlotConstants.FROM_TIME],
        description='Время начала интервала (HH:MM или HH:MM:SS)',
    )
    end_time: time = Field(
        ...,
        examples=[SlotConstants.TO_TIME],
        description='Время окончания интервала (HH:MM или HH:MM:SS)',
    )
    description: str | None = Field(
        None,
        description='Описание слота',
    )

    @model_validator(mode='after')
    def validate_time_interval(self) -> Self:
        """Проверяет, что end_time больше start_time."""
        if self.end_time <= self.start_time:
            raise ValueError(
                'Конечное время должно быть больше начального времени',
            )
        return self


class TimeSlotInfo(TimeSlotBase):
    """Схема для информации о слоте в кафе."""

    id: int = Field(..., description='ID слота')
    cafe: CafeShortInfo = Field(..., description='Информация о кафе')
    is_active: bool = Field(..., description='Активен ли слот')
    created_at: datetime = Field(..., title='Created At')
    updated_at: datetime = Field(..., title='Updated At')

    model_config = ConfigDict(from_attributes=True)


class TimeSlotCreate(TimeSlotBase):
    """Схема для создания интервала времени бронирования слота в кафе."""

    model_config = ConfigDict(extra='forbid')


class TimeSlotUpdate(BaseModel):
    """Схема для обновления интервала времени бронирования слота в кафе."""

    start_time: Optional[time] = Field(
        None, description='Время начала интервала',
    )
    end_time: Optional[time] = Field(
        None, description='Время окончания интервала')
    description: Optional[str] = Field(
        None, description='Описание временного слота',
    )
    is_active: Optional[bool] = Field(
        None, description='Активен ли временной слот',
    )

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def validate_time_interval(self) -> Self:
        """Проверяет, что end_time больше start_time."""
        if self.start_time is None or self.end_time is None:
            return self
        if self.end_time <= self.start_time:
            raise ValueError(
                'Конечное время должно быть больше начального времени',
            )
        return self


class TimeSlotShortInfo(BaseModel):
    """Краткая информация о временном слоте."""

    id: int = Field(..., description='ID временного слота')
    start_time: time = Field(..., description='Время начала интервала')
    end_time: time = Field(..., description='Время окончания интервала')

    model_config = ConfigDict(from_attributes=True)
