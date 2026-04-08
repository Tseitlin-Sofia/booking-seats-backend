"""Пример схемы."""

# from typing import Self
# from datetime import datetime, timedelta

# from pydantic import (
#     BaseModel, ConfigDict, Field, field_validator, model_validator
# )


# FROM_TIME = (
#     datetime.now() + timedelta(minutes=10)
# ).strftime('%Y-%m-%dT%H:%M')
# TO_TIME = (
#     datetime.now() + timedelta(hours=1)
# ).strftime('%Y-%m-%dT%H:%M')

# class ReservationBase(BaseModel):
#     from_reserve: datetime = Field(..., examples=[FROM_TIME])
#     to_reserve: datetime = Field(..., examples=[TO_TIME])

#     model_config = ConfigDict(extra='forbid')


# class ReservationDB(ReservationBase):
#     id: int
#     meetingroom_id: int
#     user_id: int | None = None

#     model_config = ConfigDict(from_attributes=True)

# class ReservationUpdate(ReservationBase):
#     @model_validator(mode='after')
#     def check_from_reserve_before_to_reserve(self) -> Self:
#         if self.from_reserve >= self.to_reserve:
#             raise ValueError('from_reserve должен быть раньше to_reserve.')
#         return self

#     @field_validator('from_reserve')
#     @classmethod
#     def check_from_reserve_later_than_now(cls, value):
#         if value <= datetime.now():
#             raise ValueError(
# 'from_reserve должен быть позже текущего времени.')
#         return value

# class ReservationCreate(ReservationUpdate):
#     meetingroom_id: int
