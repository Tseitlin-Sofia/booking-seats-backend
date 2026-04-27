"""Схемы для предзаказов."""

from pydantic import BaseModel, ConfigDict, Field


class PreOrderItemCreate(BaseModel):
    """Схема передачи данных о позиции предзаказа при создании бронирования."""

    dish_id: int
    quantity: int = Field(ge=1, description='Количество порций')


class PreOrderItemInfo(BaseModel):
    """Схема возврата информации о позиции предзаказа в ответе API."""

    dish_id: int
    dish_name: str
    quantity: int
    price_at_order: float
    model_config = ConfigDict(from_attributes=True)
