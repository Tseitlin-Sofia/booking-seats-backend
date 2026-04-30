"""Схема для модели интервала времени бронирования столика."""

from datetime import time

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from typing_extensions import Self

from app.core.constants import SlotConstants


class SlotBase(BaseModel):
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

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def validate_time_interval(self) -> Self:
        """Проверяет, что end_time больше start_time."""
        if self.end_time <= self.start_time:
            raise ValueError(
                'Конечное время должно быть больше начального времени',
            )
        return self


class SlotCreate(SlotBase):
    """Схема для создания интервала времени бронирования слота в кафе."""


class SlotUpdate(SlotBase):
    """Схема для обновления интервала времени бронирования слота в кафе."""


class TimeSlotShortInfo(BaseModel):
    """Краткая информация о временном слоте."""

    id: int = Field(..., description='ID временного слота')
    start_time: time = Field(..., description='Время начала интервала')
    end_time: time = Field(..., description='Время окончания интервала')

    model_config = ConfigDict(from_attributes=True)
